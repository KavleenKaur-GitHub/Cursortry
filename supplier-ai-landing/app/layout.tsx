import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SupplierAI - Transform Supplier Onboarding with Intelligent AI",
  description: "Automate document verification, compliance checks, and risk assessment. Reduce onboarding time from weeks to hours with our AI-driven workflow platform.",
  keywords: ["supplier onboarding", "AI automation", "document processing", "compliance", "risk assessment"],
  authors: [{ name: "SupplierAI" }],
  openGraph: {
    title: "SupplierAI - Transform Supplier Onboarding with Intelligent AI",
    description: "Automate document verification, compliance checks, and risk assessment. Reduce onboarding time from weeks to hours with our AI-driven workflow platform.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
