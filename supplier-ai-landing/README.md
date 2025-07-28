# SupplierAI Landing Page

A modern, responsive landing page for an AI-powered supplier onboarding workflow platform built with Next.js, TypeScript, Tailwind CSS, and shadcn/ui components.

## 🚀 Features

- **Modern Design**: Clean, professional design with gradient effects and smooth animations
- **Fully Responsive**: Mobile-first approach that works on all screen sizes
- **AI-Focused Content**: Compelling copy highlighting AI automation benefits
- **Interactive Components**: Hover effects, smooth scrolling navigation, and engaging CTAs
- **Performance Optimized**: Built with Next.js for optimal loading speeds
- **Type Safety**: Full TypeScript implementation
- **Accessible**: Proper semantic HTML and ARIA labels

## 🛠 Tech Stack

- **Framework**: Next.js 15.4.4 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **Icons**: Lucide React
- **Build Tools**: Turborepack, ESLint

## 📦 Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd supplier-ai-landing
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## 🏗 Project Structure

```
supplier-ai-landing/
├── app/
│   ├── globals.css         # Global styles with CSS variables
│   ├── layout.tsx          # Root layout with metadata
│   └── page.tsx           # Main landing page component
├── components/
│   └── ui/                # shadcn/ui components
│       ├── button.tsx     # Button component with variants
│       ├── card.tsx       # Card components
│       └── badge.tsx      # Badge component
├── lib/
│   └── utils.ts           # Utility functions (cn helper)
└── tailwind.config.ts     # Tailwind configuration
```

## 🎨 Design System

### Color Palette
- **Primary**: Blue (`blue-600`) - Trust and reliability
- **Secondary**: Purple (`purple-600`) - Innovation and AI
- **Accent Colors**: Green, Orange, Red for different features
- **Background**: White and light gray gradients

### Typography
- **Headlines**: Large, bold fonts (text-4xl to text-6xl)
- **Body Text**: Clean, readable text with proper hierarchy
- **Gradient Text**: Blue to purple gradient for key headlines

### Components
- **Buttons**: Primary, outline, and ghost variants
- **Cards**: Hover effects with shadow transitions
- **Badges**: Colored badges for features and steps
- **Icons**: Lucide React icons with consistent sizing

## 📱 Sections

1. **Header**: Sticky navigation with logo, menu, and CTA buttons
2. **Hero**: Main value proposition with gradient text and trust indicators
3. **Stats**: Key metrics in a 4-column grid
4. **Workflow**: 3-step AI workflow explanation
5. **Features**: 6 key features in a responsive grid
6. **Benefits**: Business impact with ROI calculator
7. **CTA**: Final conversion section with gradient background
8. **Footer**: Company information and links

## 🚀 Build & Deploy

### Development
```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run start    # Start production server
npm run lint     # Run ESLint
```

### Production
The application is optimized for deployment on platforms like:
- Vercel (recommended for Next.js)
- Netlify
- AWS Amplify
- Docker containers

## 📊 Performance

- **First Load JS**: ~99.7 kB
- **Static Generation**: All pages pre-rendered at build time
- **Image Optimization**: Next.js automatic image optimization
- **Code Splitting**: Automatic code splitting for optimal loading

## 🔧 Customization

### Colors
Update the CSS variables in `app/globals.css`:
```css
:root {
  --primary: 221.2 83.2% 53.3%;
  --secondary: 210 40% 96%;
  /* ... other variables */
}
```

### Content
All content is in the main `page.tsx` file and can be easily modified:
- Headlines and copy
- Statistics and metrics
- Feature descriptions
- CTA messages

### Styling
Tailwind classes can be modified throughout the components:
- Spacing and layout
- Colors and gradients
- Typography and sizing
- Responsive breakpoints

## 📋 Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 📞 Support

For questions or support, please contact:
- Email: support@supplierai.com
- Documentation: [docs.supplierai.com](https://docs.supplierai.com)
- GitHub Issues: Create an issue for bug reports or feature requests

---

Built with ❤️ by the SupplierAI team
