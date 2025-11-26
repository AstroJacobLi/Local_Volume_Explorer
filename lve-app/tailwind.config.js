/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'space-black': '#050505',
        'neon-blue': '#00f3ff',
        'neon-red': '#ff0055',
      }
    },
  },
  plugins: [],
}
