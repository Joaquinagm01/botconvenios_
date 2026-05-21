import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#0f172a',
        paper: '#f8fafc',
        sand: '#f5efe6',
        accent: '#1f6feb',
        accentSoft: '#dbeafe',
        success: '#0f9d58',
      },
      boxShadow: {
        soft: '0 20px 60px rgba(15, 23, 42, 0.12)',
      },
      fontFamily: {
        display: ['"Avenir Next"', '"SF Pro Display"', '"Trebuchet MS"', 'sans-serif'],
        body: ['"Avenir Next"', '"Segoe UI"', 'sans-serif'],
      },
      backgroundImage: {
        hero: 'radial-gradient(circle at top left, rgba(31,111,235,.18), transparent 35%), radial-gradient(circle at right top, rgba(15,157,88,.16), transparent 28%), linear-gradient(180deg, #f8fafc 0%, #f3f7ff 100%)',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        fadeUp: 'fadeUp 0.5s ease-out both',
      },
    },
  },
  plugins: [],
} satisfies Config
