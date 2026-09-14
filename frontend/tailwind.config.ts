import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        // Primary brand — deep indigo
        nova: {
          50:  '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
          950: '#1e1b4b',
        },
        // Accent — warm amber
        amber: {
          50:  '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
        // Neutral surfaces — deep charcoal
        ink: {
          950: '#08090e',
          900: '#0d0e18',
          800: '#12141f',
          750: '#161824',
          700: '#1c1e2c',
          600: '#242638',
          500: '#2e3048',
          400: '#3d4060',
          300: '#5a5f82',
        },
        // Text
        mist: {
          100: '#f0f1f8',
          200: '#d8daea',
          300: '#b0b4cc',
          400: '#8589a8',
          500: '#5e6280',
        },
      },
      animation: {
        'slide-up':     'slideUp 0.35s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-in':     'slideIn 0.35s cubic-bezier(0.16, 1, 0.3, 1)',
        'fade-in':      'fadeIn 0.4s ease-out',
        'fade-in-up':   'fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
        'pulse-dot':    'pulseDot 2s ease-in-out infinite',
        'bounce-dot':   'bounceDot 1.4s ease-in-out infinite',
        'shimmer':      'shimmer 2s linear infinite',
        'spin-slow':    'spin 3s linear infinite',
        'glow':         'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        slideUp: {
          '0%':   { transform: 'translateY(16px)', opacity: '0' },
          '100%': { transform: 'translateY(0)',    opacity: '1' },
        },
        slideIn: {
          '0%':   { transform: 'translateX(-12px)', opacity: '0' },
          '100%': { transform: 'translateX(0)',     opacity: '1' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%':   { transform: 'translateY(8px)', opacity: '0' },
          '100%': { transform: 'translateY(0)',   opacity: '1' },
        },
        pulseDot: {
          '0%, 100%': { opacity: '1',   transform: 'scale(1)' },
          '50%':      { opacity: '0.5', transform: 'scale(0.8)' },
        },
        bounceDot: {
          '0%, 60%, 100%': { transform: 'translateY(0)',    opacity: '0.4' },
          '30%':           { transform: 'translateY(-8px)', opacity: '1' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        glow: {
          '0%':   { boxShadow: '0 0 8px rgba(99, 102, 241, 0.3)' },
          '100%': { boxShadow: '0 0 24px rgba(99, 102, 241, 0.6)' },
        },
      },
      backgroundImage: {
        'grid-pattern': "url(\"data:image/svg+xml,%3Csvg width='32' height='32' viewBox='0 0 32 32' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 0h32v1H0zM0 0v32h1V0z' fill='rgba(255,255,255,0.02)' fill-rule='nonzero'/%3E%3C/svg%3E\")",
      },
      boxShadow: {
        'nova-sm':  '0 0 0 1px rgba(99, 102, 241, 0.3), 0 2px 8px rgba(99, 102, 241, 0.15)',
        'nova-md':  '0 0 0 1px rgba(99, 102, 241, 0.4), 0 4px 20px rgba(99, 102, 241, 0.2)',
        'nova-lg':  '0 0 0 1px rgba(99, 102, 241, 0.5), 0 8px 32px rgba(99, 102, 241, 0.3)',
        'card':     '0 1px 3px rgba(0,0,0,0.4), 0 4px 12px rgba(0,0,0,0.3)',
        'card-hover': '0 2px 8px rgba(0,0,0,0.5), 0 8px 24px rgba(0,0,0,0.4)',
        'message':  '0 2px 12px rgba(0,0,0,0.3)',
      },
    },
  },
  plugins: [],
} satisfies Config
