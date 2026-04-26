import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#059669',
        secondary: '#f97316',
        success: '#22c55e',
        warning: '#eab308',
        danger: '#ef4444',
        'priority-red': '#dc2626',
        'priority-yellow': '#f59e0b',
        'priority-green': '#10b981',
      },
      fontFamily: {
        sans: ['system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
export default config
