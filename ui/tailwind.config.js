/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      // Bản sắc "Thép & Sổ cái": mực xanh-đen, navy thép trầm, nền xám thép nguội,
      // điểm nhấn đồng thau (tiết chế), trạng thái trầm không chói.
      colors: {
        ink: "#0C1B2A",
        steel: {
          50: "#F4F6F9", 100: "#EDF0F4", 200: "#E2E7EE",
          300: "#C7D1DE", 400: "#93A1B2", 500: "#51617A", 700: "#2A3B4E", 900: "#0C1B2A",
        },
        navy: { DEFAULT: "#1B4B7A", dark: "#10395F", 600: "#16416B", 400: "#2F6CA6" },
        brass: { DEFAULT: "#B0812E", 50: "#FBF4E6" },
        do:   { DEFAULT: "#CB4242", nen: "#FCF2F2", vien: "#F0C9C9", dam: "#8E2C2C" },
        vang: { DEFAULT: "#C07D14", nen: "#FBF5E9", vien: "#EAD6AA", dam: "#7A5210" },
        xanh: { DEFAULT: "#1C8A5F", nen: "#ECF6F1", vien: "#B4DEC8", dam: "#0E5B3E" },
      },
      fontFamily: {
        sans: ['Inter', '"Segoe UI"', "system-ui", "sans-serif"],
      },
      boxShadow: {
        soft: "0 1px 1px rgba(12,27,42,.05)",
        card: "0 1px 2px rgba(12,27,42,.05), 0 8px 20px -12px rgba(12,27,42,.18)",
        header: "0 10px 26px -16px rgba(16,57,95,.55)",
        pop: "0 20px 48px -14px rgba(12,27,42,.32)",
      },
    },
  },
  plugins: [],
};
