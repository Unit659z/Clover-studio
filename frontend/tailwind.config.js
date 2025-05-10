/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      // --- ИЗМЕНЕНИЕ ЗДЕСЬ: Оборачиваем sans в fontFamily ---
      fontFamily: {
        sans: ['Ubuntu', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', '"Noto Sans"', 'sans-serif', '"Apple Color Emoji"', '"Segoe UI Emoji"', '"Segoe UI Symbol"', '"Noto Color Emoji"'],
        // ubuntu: ['Ubuntu', 'sans-serif'], // Оставляем закомментированным, если не нужно
      }
      // ----------------------------------------------------
    },
  },
  plugins: [
    require('@tailwindcss/typography'), // Плагин для стилизации Markdown (уже должен быть)
    require('@tailwindcss/line-clamp'), // !!! Добавляем этот плагин !!!
  ],
}