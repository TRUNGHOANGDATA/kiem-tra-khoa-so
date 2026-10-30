---
name: phat-hanh
description: Build bộ cài và phát hành phiên bản mới của tool kiểm tra khóa sổ lên GitHub Releases (kênh tự cập nhật trong app). Dùng khi người dùng nói "build bộ cài", "phát hành", "release", "ra bản mới", "đẩy bản cập nhật".
---

# Phát hành bản mới

Kênh cập nhật: repo public `TRUNGHOANGDATA/kiem-tra-khoa-so`. App hỏi `releases/latest`,
thấy tag cao hơn thì mời cài. Chi tiết đầy đủ: `tools/DONG_GOI.md`.

## Trước khi bắt đầu
- Người dùng đã đồng ý phát hành (đẩy lên GitHub là công khai — hỏi nếu chưa rõ).
- `python -m pytest -W error -q tests` xanh; `git status` sạch (hoặc chỉ còn phần sắp commit).
- `chi_nhanh.json` có ở gốc repo (local, gitignore) — thiếu thì seed không có tên chi nhánh.

## Các bước (gốc repo)
1. Sửa số trong `VERSION` (chỉ ở đây). Semver: sửa lỗi → patch, thêm tính năng → minor.
2. `cd ui && npm run build` — BẮT BUỘC sau khi đổi VERSION (số phiên bản nhồi lúc build).
   Kiểm: `grep -o '"X.Y.Z"' app/webapp/index.html`.
3. `python -m tools.tao_seed` → `build/_seed`. Kiểm seed **không có dữ liệu tài chính**: kho
   seed chỉ có bảng `quy_doi_chi_nhanh` có dòng; `cdps`, `snapshot*`, `nguon` phải = 0 dòng.
4. `pyinstaller tools/app.spec --noconfirm --clean --distpath build/dist --workpath build/work`
   — module mới phải thấy trong `build/work/app/xref-app.html`.
5. `"$LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe" tools/installer.iss`
   → `build/Output/KiemTraKhoaSo-Setup-X.Y.Z.exe`.
6. Commit (`release: X.Y.Z (…)`, gồm `VERSION` + `app/webapp/`) rồi `git push origin main`.
7. `gh release create vX.Y.Z "build/Output/KiemTraKhoaSo-Setup-X.Y.Z.exe" --title X.Y.Z --notes-file <file>`
   — tag có `v`, tên file cài không có. Ghi chú phát hành **không** chứa tên khách, số tiền,
   số chứng từ thật (repo public).
8. Kiểm kênh:
   `python -c "from app import cap_nhat; print(cap_nhat.lay_ban_moi_nhat())"` → phải trả
   đúng X.Y.Z và link tải.

## Lưu ý
- Đổi schema kho (`app/kho/schema.py`) → ghi rõ trong release notes rằng bản cũ không mở được
  kho sau khi nâng.
- Cập nhật memory/`docs/ket-qua/` với commit + tag vừa phát hành.
