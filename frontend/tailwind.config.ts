import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        paper: '#0B3A8C',
        panel: '#082F73',
        deepest: '#061F52',
        ink: '#FFFFFF',
        accent: '#FFD400',
      },
      fontFamily: {
        technical: ['Barlow Condensed', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
} satisfies Config;
