# Đóng gói bộ cài trọn gói

Bộ cài `KiemTraKhoaSo-Setup-<VERSION>.exe` mở lên là chạy được ngay: đã kèm sẵn
**bảng quy đổi tên chi nhánh**. Người dùng tự nạp **CĐPS** của mình rồi thả **Bảng kê
chứng từ** hằng tháng vào để bấm Kiểm tra. Không cần cài Python.

`<VERSION>` luôn lấy từ **một** file `VERSION` ở gốc repo (giao diện và Inno dùng
chung) — đừng gõ số phiên bản vào đâu khác.

## Máy build cần
- Python 3.14 + `pip install -r requirements.txt` + `pip install pyinstaller`
- Node (để `npm run build` giao diện React)
- Inno Setup 6 (`winget install JRSoftware.InnoSetup`). Cài scope user →
  `%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe`.
- `gh` CLI đã `gh auth login` (để phát hành release)
- File `chi_nhanh.json` ở gốc repo (local, gitignore — xem mục dưới)

## Trước khi build: `chi_nhanh.json`
`tools/tao_seed.py` đọc bảng quy đổi mã chi nhánh -> tên hiển thị từ `chi_nhanh.json`
ở gốc repo. File này **không** commit (đã gitignore) vì chứa tên chi nhánh thật của
khách hàng. Tạo file (định dạng `{"A01": "Hà Nội", ...}`) trước khi chạy
`tools.tao_seed`, nếu không seed sẽ không có bảng quy đổi.

## Các bước build (chạy từ thư mục gốc repo)

```bash
# 1. Build lại giao diện React (BẮT BUỘC nếu đã sửa VERSION hoặc UI — __PHIEN_BAN__
#    được nhồi vào bundle lúc build, không build lại thì app báo sai phiên bản)
cd ui && npm run build && cd ..

# 2. Dựng seed (tên chi nhánh, KHÔNG kèm CĐPS) -> build/_seed
python -m tools.tao_seed

# 3. Đóng gói app + seed -> build/dist/KiemTraKhoaSo/
pyinstaller tools/app.spec --noconfirm --clean --distpath build/dist --workpath build/work

# 4. Gói thành 1 file cài -> build/Output/KiemTraKhoaSo-Setup-<VERSION>.exe
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" tools/installer.iss
```

Hoặc chạy một phát: `tools/dong_goi.bat`

## Dữ liệu nằm ở đâu sau khi cài
Cài **per-user, không cần admin** (`PrivilegesRequired=lowest`) nên:
- **Ứng dụng**: `%LOCALAPPDATA%\Programs\KiemTraKhoaSo\` — ghi được.
- **Báo cáo xuất**: mặc định `…\Programs\KiemTraKhoaSo\2. Report` — **cạnh app cho
  dễ tìm** (bộ cài tạo sẵn; gỡ cài không xoá). Đổi được trong Cài đặt → Thư mục,
  hoặc bấm nút **"Mở thư mục báo cáo"**. Nếu thư mục cài chỉ-đọc (hiếm, cài admin
  vào Program Files thật) app tự lui về `%LOCALAPPDATA%\KiemTraKhoaSo\2. Report`.
- **Cấu hình + kho chốt sổ**: `%LOCALAPPDATA%\KiemTraKhoaSo\`. Lần đầu mở, app tự
  chép `_seed` sang đây (không đè nếu đã có).

## Vì sao KHÔNG kèm Bảng kê chứng từ và KHÔNG kèm CĐPS
File bảng kê thật 121–132 MB là dữ liệu hằng tháng của người dùng — không thuộc bộ
cài. CĐPS là số liệu tài chính thật của khách hàng — không nhúng vào bộ cài public;
người dùng tự nạp lần đầu dùng.

## Phát hành bản mới (auto-update)
Kênh cập nhật: repo public `TRUNGHOANGDATA/kiem-tra-khoa-so` (đã đặt trong
`app/cap_nhat.py` → `KHO_PHAT_HANH`). App hỏi `releases/latest`, thấy tag cao hơn
thì mời cài.

1. Sửa số trong `VERSION` (vd `1.2.2`).
2. Đảm bảo `chi_nhanh.json` có ở gốc (local, không commit).
3. Chạy **4 bước build** ở trên (nhớ `npm run build` để bundle mang đúng phiên bản).
4. Commit + push (gồm `VERSION` và `app/webapp/` vừa build lại):
   `git add VERSION app/webapp && git commit -m "release: X.Y.Z …" && git push`
5. Phát hành kèm file cài:
   `gh release create vX.Y.Z "build/Output/KiemTraKhoaSo-Setup-X.Y.Z.exe" --title X.Y.Z --notes "…"`
6. Kiểm nhanh kênh (tuỳ chọn): máy bản cũ mở lên sẽ thấy báo có bản mới.

Lưu ý: tag `vX.Y.Z` nhưng tên file cài là `…-X.Y.Z.exe` (asset khớp tiền tố
`KiemTraKhoaSo-Setup` + đuôi `.exe` để app nhận đúng).
