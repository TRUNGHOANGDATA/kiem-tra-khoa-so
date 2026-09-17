/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      // Bản sắc "Thép & Sổ cái": mực xanh-đen, navy thép trầm, nền xám thép nguội,
      // điểm nhấn đồng thau (tiết chế), trạng thái trầm không chói.
      colors: {
        ink: "#0C1B2A",
        // Nền ứng dụng: giấy sổ cái ấm (ngả vàng nhẹ) — dùng qua class .nen-so-cai (kẻ đồng thau mờ).
        nen: "#F1EFE9",
        // Đầu trang thép: khối mực xanh-đen như thép nguội tôi đậm.
        muc: { DEFAULT: "#122636", cao: "#1B3A54", tram: "#0A1521" },
        steel: {
          50: "#F5F6F8", 100: "#EDEEF1", 200: "#E1E4EA",
          300: "#C6CDD8", 400: "#8E9AAB", 500: "#4F5E73", 700: "#2A3B4E", 900: "#0C1B2A",
        },
        // Tone chính: Emerald (thay cho navy cũ — giữ tên khoá "navy" để không phải sửa hàng loạt class).
        navy: { DEFAULT: "#059669", dark: "#047857", 600: "#059669", 400: "#10B981" },
        // Đồng thau — điểm nhấn thật của bản sắc (huy hiệu, đường kẻ sổ).
        brass: { DEFAULT: "#B4842B", 50: "#FAF3E2", 300: "#D6AF57", 600: "#8A6320" },
        do:   { DEFAULT: "#CB4242", nen: "#FCF2F2", vien: "#F0C9C9", dam: "#8E2C2C" },
        vang: { DEFAULT: "#C07D14", nen: "#FBF5E9", vien: "#EAD6AA", dam: "#7A5210" },
        xanh: { DEFAULT: "#1C8A5F", nen: "#ECF6F1", vien: "#B4DEC8", dam: "#0E5B3E" },
      },
      fontFamily: {
        sans: ['"Segoe UI"', "system-ui", "Tahoma", "sans-serif"],
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
