import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

// Phiên bản lấy từ file VERSION ở gốc repo — MỘT nguồn duy nhất, dùng chung với
// tools/installer.iss. Trước đây số này hard-code riêng ở App.tsx nên trôi khỏi bộ cài:
// giao diện ghi 1.0.1 trong khi bộ cài đã 1.1.1.
const PHIEN_BAN = readFileSync(
  fileURLToPath(new URL("../VERSION", import.meta.url)), "utf-8").trim();

// Gộp toàn bộ JS/CSS vào MỘT index.html (viteSingleFile) — pywebview nạp qua file://
// không còn asset rời hay thuộc tính crossorigin (hay bị WebView2 chặn). base './'.
// Build ra app/webapp/ (commit sẵn) nên máy người dùng chỉ cần Python, không cần Node.
export default defineConfig({
  define: { __PHIEN_BAN__: JSON.stringify(PHIEN_BAN) },
  plugins: [react(), viteSingleFile()],
  base: "./",
  build: {
    outDir: fileURLToPath(new URL("../app/webapp", import.meta.url)),
    emptyOutDir: true,
    assetsInlineLimit: 100000000,
    cssCodeSplit: false,
  },
});
