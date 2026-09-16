import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";

// base: './' -> đường dẫn tương đối để pywebview nạp bản build qua file://.
// build ra app/webapp/ (được commit) nên máy người dùng chỉ cần Python, không cần Node.
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: {
    outDir: fileURLToPath(new URL("../app/webapp", import.meta.url)),
    emptyOutDir: true,
  },
});
