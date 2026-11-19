/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        darkBg: '#0B0D10',
        surface: 'rgba(255, 255, 255, 0.06)',
        surfaceBorder: 'rgba(255, 255, 255, 0.08)',
        surfaceHighlight: 'rgba(255, 255, 255, 0.12)',
        primaryText: '#FFFFFF',
        secondaryText: 'rgba(255, 255, 255, 0.60)',
        mutedText: 'rgba(255, 255, 255, 0.40)',
      },
      borderRadius: {
        '28': '28px',
        '32': '32px',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        'glow': '0 0 25px -5px rgba(255, 255, 255, 0.3)',
      },
    },
  },
  plugins: [],
}

