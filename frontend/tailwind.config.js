/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#141517",
        surface: "#1E1F25",
        surface2: "#2A2B33",
        ink: "#E7E8EC",
        comment: "#8B8D98",
        accent: "#FFA116",
        success: "#2ECC71",
        danger: "#FF5C5C",
      },
      fontFamily: {
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
        sans: ['"Inter"', "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
}