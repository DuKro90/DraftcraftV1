/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // DraftCraft Brand Colors (from existing demo)
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#b9dcfe',
          300: '#7cc0fd',
          400: '#36a2fa',
          500: '#0c85eb',
          600: '#0067c8',
          700: '#0152a2',
          800: '#064686',
          900: '#0b3a6f',
          950: '#08244a',
        },
        accent: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#F5C400', // Primary yellow
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
          950: '#451a03',
        },
        // Tier colors for German Handwerk
        tier1: {
          DEFAULT: '#3498DB',
          light: '#5DADE2',
          dark: '#2874A6',
        },
        tier2: {
          DEFAULT: '#F39C12',
          light: '#F8C471',
          dark: '#D68910',
        },
        tier3: {
          DEFAULT: '#9B59B6',
          light: '#BB8FCE',
          dark: '#7D3C98',
        },
        critical: {
          DEFAULT: '#E74C3C',
          light: '#EC7063',
          dark: '#C0392B',
        },
        dsgvo: {
          DEFAULT: '#27AE60',
          light: '#52BE80',
          dark: '#1E8449',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
