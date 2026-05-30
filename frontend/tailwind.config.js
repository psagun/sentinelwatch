/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#0B0F19',
          50: '#0D111E',
          100: '#131826',
          200: '#1A2035',
          300: '#232B44',
        },
        accent: {
          cyan: '#22D3EE',
          amber: '#F59E0B',
          red: '#EF4444',
          green: '#22C55E',
          purple: '#A78BFA',
        },
        text: {
          primary: '#E2E8F0',
          secondary: '#8892A6',
          muted: '#555E72',
        },
        border: {
          DEFAULT: '#1E2433',
          light: '#2A3348',
        },
      },
      fontFamily: {
        display: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'slide-up': 'slideUp 0.5s ease-out forwards',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(34, 211, 238, 0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(34, 211, 238, 0.4)' },
        },
      },
    },
  },
  plugins: [],
};
