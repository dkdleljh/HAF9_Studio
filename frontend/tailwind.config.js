/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'haf9': {
          'dark': '#0a0e17',
          'card': '#111827',
          'border': '#1f2937',
          'accent': '#06b6d4',
          'accent-hover': '#0891b2',
          'success': '#10b981',
          'warning': '#f59e0b',
          'danger': '#ef4444',
          'text': '#e5e7eb',
          'text-muted': '#9ca3af',
        }
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'Fira Code', 'monospace'],
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
