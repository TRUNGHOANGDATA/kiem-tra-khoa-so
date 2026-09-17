import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";
import { fileURLToPath } from "node:url";

// Gộp toàn bộ JS/CSS vào MỘT index.html (viteSingleFile) — pywebview nạp qua file://
// không còn asset rời hay thuộc tính crossorigin (hay bị WebView2 chặn). base './'.
// Build ra app/webapp/ (commit sẵn) nên máy người dùng chỉ cần Python, không cần Node.
export default defineConfig({
  plugins: [react(), viteSingleFile()],
  base: "./",
  build: {
    outDir: fileURLToPath(new URL("../app/webapp", import.meta.url)),
    emptyOutDir: true,
    assetsInlineLimit: 100000000,
    cssCodeSplit: false,
  },
});
