/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#fef6f0',
          100: '#fdeadb',
          200: '#fbd2b5',
          300: '#f6b182',
          400: '#f09050',
          500: '#ea7025',
          600: '#d45a18',
          700: '#b04515',
          800: '#8c3814',
          900: '#6e2e12',
        },
        tangerine: {
          DEFAULT: '#ea7025',
          light: '#f09050',
          dark: '#d45a18',
          50: '#fef6f0',
          100: '#fdeadb',
          200: '#fbd2b5',
          300: '#f6b182',
          400: '#f09050',
          500: '#ea7025',
          600: '#d45a18',
          700: '#b04515',
          800: '#8c3814',
          900: '#6e2e12',
        },
      },
      fontFamily: {
        sans: ['"Open Sans"', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
