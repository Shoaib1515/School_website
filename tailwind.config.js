/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./dist/**/*.html", "./src/**/*.js"],
  theme: {
    extend: {
      colors: {
        ink: "#0b1f33",
        navy: "#082a46",
        lake: "#006b78",
        sky: "#b9e6ee",
        cream: "#f4f0e7",
        coral: "#ef6a52",
        paper: "#fffdf8"
      },
      fontFamily: {
        display: ["Georgia", "Cambria", "Times New Roman", "serif"],
        sans: ["Arial", "Helvetica", "sans-serif"]
      }
    }
  },
  plugins: []
};

