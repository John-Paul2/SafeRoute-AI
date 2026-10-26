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
          DEFAULT: '#30a83c',
          strong: '#197e25',
          surface: '#defde4',
        },
        brand: {
          DEFAULT: '#30a83c',
          strong: '#197e25',
          surface: '#defde4',
        },
        hot: '#ce1736',
        cold: '#034eb1',
        warm: '#fb6001',
        premium: '#7457dd',
        canvas: '#f3f5f7',
        surface: '#ffffff',
        ink: '#000000',
        body: '#6b6d70',
        muted: '#a7a9ac',
        hairline: '#dfe1e4',
        warning: {
          surface: '#faf9ca',
          text: '#9f5c0c',
        },
        discount: {
          surface: '#defde4',
          text: '#197e25',
        },
      },
      borderRadius: {
        'xs': '2px',
        'sm': '4px',
        'md': '8px',
        'full': '540px',
      },
      fontFamily: {
        sans: ['Mulish', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
