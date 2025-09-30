import os
import sys
import traceback

from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio


# ------------------------------
# Config
# ------------------------------
DATA_FILE = "Negotiation Dummy Data.xlsx"
DEFAULT_ITEM = "MacBook Pro 16 Inch"

app = Flask(__name__)


# ------------------------------
# Dummy data creation (if missing)
# ------------------------------
def create_dummy_data(save_to_file: bool = True) -> pd.DataFrame:
    rng = np.random.default_rng(42)

    suppliers = [
        "TechSource",
        "Global IT",
        "ValueHub",
        "Prime Devices",
        "BlueWave",
        "NovaSupply",
    ]
    locations = [
        "New York",
        "Austin",
        "San Jose",
        "Chicago",
        "Atlanta",
        "Seattle",
    ]

    # Price baselines per supplier for the target item
    supplier_price_adjust = {
        "TechSource": 1.00,   # baseline
        "Global IT": 1.05,
        "ValueHub": 0.97,
        "Prime Devices": 1.08,
        "BlueWave": 1.03,
        "NovaSupply": 0.99,
    }

    records = []
    num_rows = 200

    for i in range(num_rows):
        supplier = suppliers[i % len(suppliers)]
        location = locations[i % len(locations)]

        # Mix of items but ensure plenty of our target item
        if i % 3 == 0:
            title = "MacBook Pro 16 Inch"
            base_price = 2700.0
            # Add some random price noise and supplier adjustment
            unit_price = (
                base_price
                * supplier_price_adjust[supplier]
                * float(1 + rng.normal(0.0, 0.03))
            )
        else:
            # Other items to make the dataset more realistic
            other_items = [
                "Dell XPS 13",
                "ThinkPad X1 Carbon",
                "HP EliteBook 840",
                "Monitor 27 Inch",
                "USB-C Docking Station",
            ]
            title = other_items[i % len(other_items)]
            unit_price = float(abs(800 + rng.normal(0, 150)))

        quantity = int(max(1, rng.integers(1, 25)))
        spend = float(unit_price * quantity)

        records.append(
            {
                "title": title,
                "quantity": quantity,
                "spend": round(spend, 2),
                "supplier": supplier,
                "location": location,
            }
        )

    df = pd.DataFrame.from_records(records)
    if save_to_file:
        try:
            # Ensure Excel writer engine is available
            df.to_excel(DATA_FILE, index=False)
        except Exception:
            # Fallback: also save a CSV alongside for transparency
            df.to_csv(DATA_FILE.replace(".xlsx", ".csv"), index=False)
    return df


# ------------------------------
# Data loading & processing
# ------------------------------
def load_and_prepare() -> pd.DataFrame:
    if not os.path.exists(DATA_FILE):
        # Auto-generate a dummy dataset so the app runs out-of-the-box
        create_dummy_data(save_to_file=True)

    # Prefer Excel; if missing (e.g., engine not available), fall back to CSV
    df = None
    try:
        if os.path.exists(DATA_FILE):
            df = pd.read_excel(DATA_FILE)
    except Exception:
        df = None

    if df is None:
        csv_alt = DATA_FILE.replace(".xlsx", ".csv")
        if os.path.exists(csv_alt):
            df = pd.read_csv(csv_alt)
        else:
            raise FileNotFoundError(
                f"Data file not found or unreadable: {DATA_FILE} (and no CSV fallback at {csv_alt})."
            )
    df.columns = df.columns.str.strip().str.lower()

    # ensure required columns exist
    required = {"title", "quantity", "spend", "supplier", "location"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(
            f"Missing required columns in {DATA_FILE}: {sorted(list(missing))}"
        )

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["spend"] = pd.to_numeric(df["spend"], errors="coerce")
    df["unit_price"] = np.where(
        df["quantity"] > 0, df["spend"] / df["quantity"], np.nan
    )
    return df


def compute_supplier_summary(df: pd.DataFrame, selected_item: str = DEFAULT_ITEM):
    df_item = df[df["title"].str.contains(selected_item, case=False, na=False)]
    if df_item.empty:
        return None, None, df_item

    supplier_summary = (
        df_item.groupby("supplier", as_index=False)
        .agg(
            orders=("title", "count"),
            total_qty=("quantity", "sum"),
            avg_unit_price=("unit_price", "mean"),
            min_unit_price=("unit_price", "min"),
            max_unit_price=("unit_price", "max"),
            locations=("location", "nunique"),
        )
    )

    overall_avg = supplier_summary["avg_unit_price"].mean()
    supplier_summary["price_var_vs_avg"] = (
        (supplier_summary["avg_unit_price"] - overall_avg) / overall_avg * 100
    ).round(1)

    insights = []
    for _, row in supplier_summary.iterrows():
        notes = []
        if row["price_var_vs_avg"] < 0:
            notes.append("✅ Consistently below avg pricing")
        else:
            notes.append("❌ Above avg pricing")

        if row["orders"] >= supplier_summary["orders"].median():
            notes.append("✅ Higher order volume → reliable partner")
        else:
            notes.append("❌ Fewer historical transactions")

        if row["locations"] > 1:
            notes.append("✅ Broad geographic presence")
        else:
            notes.append("❌ Limited geographic presence")

        insights.append("\n".join(notes))

    supplier_summary["ai_insights"] = insights

    best_supplier = supplier_summary.loc[
        supplier_summary["avg_unit_price"].idxmin()
    ]
    worst_supplier = supplier_summary.loc[
        supplier_summary["avg_unit_price"].idxmax()
    ]

    benchmark_price = round(overall_avg, 2)
    best_price = round(best_supplier["avg_unit_price"], 2)
    shift_qty = worst_supplier["total_qty"] * 0.5
    saving_potential = (worst_supplier["avg_unit_price"] - best_price) * shift_qty

    negotiation = {
        "benchmark_price": benchmark_price,
        "best_supplier": best_supplier.to_dict(),
        "worst_supplier": worst_supplier.to_dict(),
        "best_price": best_price,
        "saving_potential": round(saving_potential, 2),
    }
    return supplier_summary, negotiation, df_item


# ------------------------------
# Plot builder (blue shades)
# ------------------------------
def build_price_bar(supplier_summary: pd.DataFrame) -> str:
    blue_shades = [
        "#003f6b",
        "#005ea6",
        "#007ab3",
        "#0096bf",
        "#00b2cb",
        "#00ced7",
    ]
    repeat_colors = (
        blue_shades * ((len(supplier_summary) // len(blue_shades)) + 1)
    )[: len(supplier_summary)]

    fig = px.bar(
        supplier_summary.sort_values("avg_unit_price"),
        x="supplier",
        y="avg_unit_price",
        text="avg_unit_price",
        color="supplier",
        color_discrete_sequence=repeat_colors,
        labels={"avg_unit_price": "Avg Unit Price", "supplier": "Supplier"},
        title="Average Unit Price by Supplier",
    )
    fig.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
    fig.update_layout(
        margin=dict(t=70, b=40, l=40, r=40),
        height=420,
        showlegend=False,
        font=dict(family="Inter, Arial"),
    )
    return pio.to_html(fig, full_html=False)


# ------------------------------
# HTML Templates (Landing + Dashboard)
# ------------------------------
LANDING_TEMPLATE = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>Data-Driven Negotiation</title>
  <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
  <style>
    :root { --cog-blue:#005ea6; --cog-dark:#0f2340; --cog-cyan:#00b2cb; }
    html, body { height:100%; }
    body{
      background: radial-gradient(1200px 600px at 10% 10%, rgba(0,178,203,0.22), transparent 60%),
                  radial-gradient(1000px 600px at 90% 20%, rgba(0,94,166,0.18), transparent 55%),
                  linear-gradient(180deg, #f7fbff 0%, #f2fbff 100%);
      color: var(--cog-dark);
      font-family: Inter, system-ui, -apple-system, \"Segoe UI\", Roboto, Arial;
      overflow-x:hidden;
    }
    .nav-brand { font-weight: 800; letter-spacing: .2px; color: var(--cog-blue); }
    .hero { padding: 80px 0 30px; position:relative; }
    .hero h1 { font-weight: 900; line-height:1.1; letter-spacing: -.5px; }
    .hero p { color:#4e6b86; font-size:1.1rem; }
    .cta-btn{ background:var(--cog-blue); border-color:var(--cog-blue); padding:12px 18px; border-radius:12px; }
    .floating { position:absolute; border-radius:16px; backdrop-filter: blur(6px); animation: float 10s ease-in-out infinite; }
    .f1{ top: -20px; right: -20px; width: 180px; height: 180px; background: linear-gradient(135deg, rgba(0,94,166,.18), rgba(0,178,203,.12)); }
    .f2{ bottom: -30px; left: -30px; width: 220px; height: 220px; background: linear-gradient(135deg, rgba(0,178,203,.18), rgba(0,94,166,.12)); animation-delay: -3s; }
    @keyframes float { 0%{ transform: translateY(0px) } 50%{ transform: translateY(-14px) } 100%{ transform: translateY(0px) } }
    .feature { border-radius:16px; background:white; box-shadow:0 12px 40px rgba(9,30,66,.06); padding:18px; height:100%; opacity:0; transform: translateY(16px); transition:.6s ease; }
    .feature.visible{ opacity:1; transform: translateY(0); }
    .badge-soft { background: rgba(0,94,166,.08); color: var(--cog-blue); border:1px solid rgba(0,94,166,.12); border-radius:10px; padding:6px 10px; }
    footer { color:#6f869a; padding: 28px 0 18px; }
  </style>
</head>
<body>
  <nav class=\"navbar navbar-expand-lg bg-transparent\">
    <div class=\"container\">
      <span class=\"nav-brand\">Data-Driven Negotiation</span>
      <div class=\"ms-auto\">
        <a class=\"btn btn-outline-primary\" href=\"{{ url_for('dashboard') }}\">Open Dashboard</a>
      </div>
    </div>
  </nav>

  <section class=\"hero\">
    <div class=\"container position-relative\">
      <div class=\"row align-items-center\">
        <div class=\"col-lg-6\">
          <span class=\"badge-soft\">Procurement Intelligence</span>
          <h1 class=\"display-5 mt-3\">Negotiate smarter with live supplier analytics</h1>
          <p class=\"mt-3\">A modern, data-driven dashboard that benchmarks historical prices, highlights savings opportunities, and guides conversations with an AI playbook.</p>
          <div class=\"d-flex gap-3 mt-4\">
            <a class=\"btn btn-primary cta-btn\" href=\"{{ url_for('dashboard') }}?item={{ default_item|urlencode }}\">Launch Dashboard</a>
            <a class=\"btn btn-outline-secondary\" href=\"#features\">Learn more</a>
          </div>
        </div>
        <div class=\"col-lg-6 position-relative\">
          <div class=\"floating f1\"></div>
          <div class=\"floating f2\"></div>
          <img class=\"img-fluid rounded-4 shadow\" src=\"https://images.unsplash.com/photo-1517336714731-489689fd1ca8?q=80&w=1200&auto=format&fit=crop\" alt=\"Laptop workspace\" />
        </div>
      </div>
    </div>
  </section>

  <section id=\"features\" class=\"py-4 py-lg-5\">
    <div class=\"container\">
      <div class=\"row g-4\">
        <div class=\"col-md-4\">
          <div class=\"feature\"><h6>Supplier Benchmarking</h6><p class=\"mb-0\">Compare avg unit prices, volumes, and coverage across suppliers instantly.</p></div>
        </div>
        <div class=\"col-md-4\">
          <div class=\"feature\"><h6>Negotiation Playbook</h6><p class=\"mb-0\">AI-generated talking points tailored to each supplier's strengths and gaps.</p></div>
        </div>
        <div class=\"col-md-4\">
          <div class=\"feature\"><h6>Actionable Savings</h6><p class=\"mb-0\">Quantify potential savings by shifting volume based on best-in-class pricing.</p></div>
        </div>
      </div>
    </div>
  </section>

  <footer class=\"text-center\">
    Reads <code>{{ data_file }}</code> • Local demo
  </footer>

  <script>
    // Minimal reveal on scroll
    const io = new IntersectionObserver((entries)=>{
      entries.forEach(e=>{ if(e.isIntersecting){ e.target.classList.add('visible'); } });
    }, { threshold: .2 });
    document.querySelectorAll('.feature').forEach(el=> io.observe(el));
  </script>
</body>
</html>
"""


DASHBOARD_TEMPLATE = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>Negotiation Dashboard</title>
  <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
  <link rel=\"stylesheet\" href=\"https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css\">
  <style>
    :root { --cog-blue: #005ea6; --cog-dark: #003f6b; --card-bg:#ffffff; }
    body{ background: #f6fbfc; color: #0f2340; font-family: Inter, system-ui, -apple-system, \"Segoe UI\", Roboto, Arial; padding:20px; }
    .navbar { background: linear-gradient(180deg, rgba(0,94,166,.06), rgba(0,178,203,.02)); border:1px solid rgba(0,94,166,0.06); border-radius:14px; padding:10px 16px; }
    .brand { color: var(--cog-blue); font-weight:800; letter-spacing:.2px; }
    .card { border-radius:14px; box-shadow:0 10px 30px rgba(9,30,66,0.06); border:none; margin-bottom:22px; background:var(--card-bg); padding:18px; opacity:0; transform: translateY(18px); transition: .5s ease; }
    .card.visible{ opacity:1; transform: translateY(0); }
    .section-title { color: var(--cog-blue); font-weight:800; font-size:1.05rem; margin-bottom:12px; display:flex; align-items:center; gap:10px; }
    .section-title .dot { width:10px; height:10px; background:var(--cog-blue); border-radius:3px; display:inline-block; }
    table.dataTable thead th { background: transparent; color:var(--cog-dark); font-weight:700; }
    .chat-box { min-height:180px; border-radius:10px; border:1px solid #e6f0f4; padding:14px; background:#fff; }
    .chat-block { margin-bottom:14px; white-space:pre-line; }
    .chat-user { color:var(--cog-dark); font-weight:700; }
    .chat-bot { color:var(--cog-blue); font-weight:700; }
    .small-muted { color:#607b92; }
    .btn-primary { background: var(--cog-blue); border-color: var(--cog-blue); }
    footer { color:#6f869a; margin-top:10px; }
    .toolbar { display:flex; gap:10px; align-items:center; }
    .toolbar .select { min-width: 260px; }
    @media (max-width: 767px) { .chat-box{ min-height: 220px; } }
  </style>
</head>
<body>
  <div class=\"container-fluid\">
    <div class=\"navbar mb-3\">
      <div class=\"brand\">Negotiation Dashboard</div>
      <div class=\"ms-auto\"><a class=\"btn btn-sm btn-outline-primary\" href=\"{{ url_for('landing') }}\">Home</a></div>
    </div>

    <div class=\"card\">
      <div class=\"d-flex justify-content-between align-items-center\">
        <div class=\"section-title mb-0\"><span class=\"dot\"></span> Controls</div>
        <div class=\"toolbar\">
          <select id=\"item-select\" class=\"form-select select\">
            {% for opt in item_options %}
            <option value=\"{{ opt }}\" {% if opt==item %}selected{% endif %}>{{ opt }}</option>
            {% endfor %}
          </select>
          <button id=\"go-btn\" class=\"btn btn-primary\">Apply</button>
        </div>
      </div>
    </div>

    <!-- Supplier Table (full width) -->
    <div class=\"card\">
      <div class=\"section-title\"><span class=\"dot\"></span> Supplier Comparison</div>
      <div class=\"table-responsive\">
        <table id=\"supplier-table\" class=\"display\" style=\"width:100%\">
          <thead>
            <tr>
              <th>Supplier Insights</th>
              <th>Supplier</th>
              <th>Avg Unit Price</th>
              <th>Orders</th>
              <th>Total Qty</th>
              <th>Variance %</th>
              <th>Locations</th>
            </tr>
          </thead>
          <tbody>
            {% for r in supplier_rows %}
            <tr>
              <td style=\"white-space:pre-line;\">{{ r.ai_insights }}</td>
              <td>{{ r.supplier }}</td>
              <td>${{ "{:,.2f}".format(r.avg_unit_price) }}</td>
              <td>{{ r.orders }}</td>
              <td>{{ r.total_qty }}</td>
              <td>{{ r.price_var_vs_avg }}</td>
              <td>{{ r.locations }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Negotiation AI Summary (full width) -->
    <div class=\"card\">
      <div class=\"section-title\"><span class=\"dot\"></span> Negotiation AI Summary</div>
      <div style=\"padding:12px; border-radius:10px; background:linear-gradient(180deg, rgba(0,94,166,0.06), rgba(0,178,203,0.02)); border:1px solid rgba(0,94,166,0.06)\">
        <p style=\"margin:0\"><strong>Benchmark Price (Internal Avg):</strong> ${{ negotiation.benchmark_price }}</p>
        <p style=\"margin:0\"><strong>Best Historical Price:</strong> ${{ negotiation.best_price }} ({{ negotiation.best_supplier.supplier }})</p>
        <p style=\"margin:0\"><strong>Savings Potential:</strong> If shifted 50% of <strong>{{ negotiation.worst_supplier.supplier }}</strong>'s volume to <strong>{{ negotiation.best_supplier.supplier }}</strong> → ~${{ negotiation.saving_potential }}</p>
      </div>
    </div>

    <!-- Chatbot (full width) -->
    <div class=\"card\">
      <div class=\"section-title\"><span class=\"dot\"></span> Chatbot</div>
      <div class=\"row g-2 mb-3\">
        <div class=\"col-md-5\">
          <select id=\"chat-question\" class=\"form-select\">
            <option value=\"\">Select a question...</option>
            <option value=\"who_best\">Who is the best supplier?</option>
            <option value=\"why_supplier\">Why this supplier?</option>
            <option value=\"playbook\">Show negotiation playbook</option>
          </select>
        </div>
        <div class=\"col-md-5\">
          <select id=\"supplier-select\" class=\"form-select\">
            <option value=\"\">-- Choose supplier (for Why) --</option>
            {% for s in supplier_names %}
            <option value=\"{{ s }}\">{{ s }}</option>
            {% endfor %}
          </select>
        </div>
        <div class=\"col-md-2 d-grid\">
          <button id=\"ask-btn\" class=\"btn btn-primary\">Ask</button>
        </div>
      </div>
      <div class=\"chat-box\" id=\"chat-answer\">
        <div class=\"chat-block\"><span class=\"small-muted\">Select a question and press <strong>Ask</strong>.</span></div>
      </div>
    </div>

    <!-- Plot (full width) -->
    <div class=\"card\">
      <div class=\"section-title\"><span class=\"dot\"></span> Average Unit Price by Supplier</div>
      <div id=\"bar-plot\">{{ bar_plot|safe }}</div>
    </div>

    <footer>Reads <code>{{ data_file }}</code> • Local demo</footer>
  </div>

  <!-- JS libs -->
  <script src=\"https://code.jquery.com/jquery-3.7.1.min.js\"></script>
  <script src=\"https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js\"></script>
  <script>
    // Reveal cards on load
    const io = new IntersectionObserver((entries)=>{
      entries.forEach(e=>{ if(e.isIntersecting){ e.target.classList.add('visible'); } });
    }, { threshold: .2 });
    document.querySelectorAll('.card').forEach(el=> io.observe(el));

    $(document).ready(function(){
      $('#supplier-table').DataTable({ pageLength: 10 });

      $('#go-btn').on('click', function(){
        const item = encodeURIComponent($('#item-select').val());
        const url = new URL(window.location.href);
        url.searchParams.set('item', item);
        window.location.href = url.toString();
      });

      $('#ask-btn').on('click', function(){
        const q = $('#chat-question').val();
        const supplier = $('#supplier-select').val();
        $('#chat-answer').html('<div class="chat-block small-muted">Thinking...</div>');
        $.post('/chat', { question: q, supplier: supplier, item: '{{ item }}' }, function(resp){
          $('#chat-answer').html(resp.answer_html);
        }, 'json').fail(function(xhr){
          $('#chat-answer').html('<div class="chat-block text-danger">Error: ' + xhr.responseText + '</div>');
        });
      });
    });
  </script>
</body>
</html>
"""


# ------------------------------
# Routes
# ------------------------------
@app.route("/")
def landing():
    return render_template_string(
        LANDING_TEMPLATE,
        data_file=DATA_FILE,
        default_item=DEFAULT_ITEM,
    )


@app.route("/dashboard")
def dashboard():
    item = request.args.get("item", DEFAULT_ITEM)
    try:
        df = load_and_prepare()
    except Exception as e:
        tb = traceback.format_exc()
        return (
            f"<h3>Error loading data:</h3><pre>{str(e)}</pre><h5>Traceback:</h5><pre>{tb}</pre>",
            500,
        )

    supplier_summary, negotiation, df_item = compute_supplier_summary(
        df, selected_item=item
    )
    if supplier_summary is None:
        sample_titles = df["title"].dropna().unique()[:12].tolist()
        return (
            f"<h3>No rows matching item: <code>{item}</code></h3>"
            f"<p>Make sure the 'title' column contains that string (case-insensitive).</p>"
            f"<p>Example titles from your file (first 12): {sample_titles}</p>",
            200,
        )

    bar_plot = build_price_bar(supplier_summary)
    supplier_rows = supplier_summary.to_dict(orient="records")
    supplier_names = supplier_summary["supplier"].tolist()

    # Item dropdown: include requested default item; allow duplicates for now as requested
    item_options = [
        DEFAULT_ITEM,
        DEFAULT_ITEM,  # repeated intentionally per request
    ]

    return render_template_string(
        DASHBOARD_TEMPLATE,
        bar_plot=bar_plot,
        supplier_rows=supplier_rows,
        supplier_names=supplier_names,
        negotiation=negotiation,
        item=item,
        data_file=DATA_FILE,
        item_options=item_options,
    )


@app.route("/chat", methods=["POST"])
def chat():
    question = request.form.get("question")
    supplier = request.form.get("supplier")
    item = request.form.get("item", DEFAULT_ITEM)

    try:
        df = load_and_prepare()
        supplier_summary, negotiation, _ = compute_supplier_summary(
            df, selected_item=item
        )
        if supplier_summary is None:
            return (
                jsonify({"answer_html": f"<div class='chat-block'>No data for item: {item}</div>"}),
                400,
            )

        best = negotiation["best_supplier"]
        best_price = negotiation["best_price"]
        rows = supplier_summary.set_index("supplier").to_dict(orient="index")

        def format_strengths(ai_text: str) -> str:
            parts = ai_text.splitlines()
            lines = []
            for p in parts:
                p = p.strip()
                if p:
                    lines.append(p)
            return "<br>".join(lines)

        if question == "who_best":
            user_block = (
                "<div class='chat-block'><span class='chat-user'>User: Who is the best supplier?</span></div>"
            )
            bot_text = (
                f"<div class='chat-block'><span class='chat-bot'>Chatbot: </span>"
                f"<span>Based on historical data, <strong>{best['supplier']}</strong> offers the lowest average unit price "
                f"(<strong>${best_price:,.2f}</strong>) with {int(best['orders'])} orders and consistent performance.</span></div>"
            )
            answer_html = user_block + bot_text
        elif question == "why_supplier":
            if not supplier:
                answer_html = (
                    "<div class='chat-block'>Please select a supplier from the dropdown to ask 'Why'.</div>"
                )
            elif supplier not in rows:
                answer_html = f"<div class='chat-block'>Supplier '{supplier}' not found.</div>"
            else:
                r = rows[supplier]
                gap = ((r["avg_unit_price"] - best_price) / best_price * 100) if best_price else 0
                gap = round(gap, 1)
                user_block = f"<div class='chat-block'><span class='chat-user'>User: Why {supplier}?</span></div>"
                bot_header = (
                    f"<div class='chat-block'><span class='chat-bot'>Chatbot: {supplier}’s avg price is "
                    f"${r['avg_unit_price']:,.0f}, {gap}% vs best supplier ({best['supplier']}).</span></div>"
                )
                strengths = format_strengths(r["ai_insights"]) if r.get("ai_insights") else ""
                strengths_block = f"<div class='chat-block'><strong>Strengths:</strong><br>{strengths}</div>"
                answer_html = user_block + bot_header + strengths_block
        elif question == "playbook":
            user_block = "<div class='chat-block'><span class='chat-user'>User: Show negotiation playbook</span></div>"
            lines = []
            for s, r in rows.items():
                gap = ((r["avg_unit_price"] - best_price) / best_price * 100) if best_price else 0
                gap = round(gap, 1)
                if s == best["supplier"]:
                    lines.append(f"- {s}: Strongest price position → use as benchmark.")
                else:
                    last_note = r.get("ai_insights", "").splitlines()[-1] if r.get("ai_insights") else ""
                    lines.append(
                        f"- {s}: {gap}% higher than {best['supplier']}. Highlight: {last_note}"
                    )
            playbook_html = "<br>".join(lines)
            bot_block = (
                f"<div class='chat-block'><span class='chat-bot'>Chatbot:</span><div style='margin-top:8px'>{playbook_html}</div></div>"
            )
            answer_html = user_block + bot_block
        else:
            answer_html = "<div class='chat-block'>Unknown question. Choose one of the options.</div>"

        return jsonify({"answer_html": answer_html})
    except Exception as e:
        tb = traceback.format_exc()
        return (
            jsonify(
                {
                    "answer_html": f"<div class='chat-block text-danger'>Error: {str(e)}<pre>{tb}</pre></div>",
                }
            ),
            500,
        )


# ------------------------------
# Run server (fail fast)
# ------------------------------
def main():
    try:
        _ = load_and_prepare()
    except Exception as e:
        print("ERROR: cannot start app — problem loading data file:", file=sys.stderr)
        traceback.print_exc()
        print("\nFix the error and re-run.", file=sys.stderr)
        sys.exit(1)

    host = "127.0.0.1"
    port = 5000
    print(f"Starting Flask app at http://{host}:{port} (pid={os.getpid()})")
    app.run(host=host, port=port, debug=True, use_reloader=False)


if __name__ == "__main__":
    main()

