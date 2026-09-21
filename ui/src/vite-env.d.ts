/// <reference types="vite/client" />

/** Phiên bản app, do vite.config.ts bơm vào từ file VERSION ở gốc repo — MỘT nguồn
 *  duy nhất dùng chung với bộ cài (tools/installer.iss cũng đọc file đó). Trước đây
 *  số này hard-code riêng ở App.tsx nên trôi: UI ghi 1.0.1 khi bộ cài đã 1.1.1. */
declare const __PHIEN_BAN__: string;
