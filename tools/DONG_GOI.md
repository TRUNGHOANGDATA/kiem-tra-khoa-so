# Đóng gói bộ cài trọn gói

Bộ cài `KiemTraKhoaSo-Setup-1.0.0.exe` mở lên là chạy được ngay: đã kèm sẵn **bảng
quy đổi tên chi nhánh**. Người dùng tự nạp **CĐPS** của mình rồi thả **Bảng kê
chứng từ** hằng tháng vào để bấm Kiểm tra. Không cần cài Python.

## Máy build cần
- Python 3.14 + `pip install -r requirements.txt` + `pip install pyinstaller`
- Inno Setup 6 (`winget install JRSoftware.InnoSetup`)
- File `chi_nhanh.json` ở gốc repo (local, gitignore — xem mục "Trước khi build" bên dưới)

## Trước khi build: `chi_nhanh.json`
`tools/tao_seed.py` đọc bảng quy đổi mã chi nhánh -> tên hiển thị từ `chi_nhanh.json`
ở gốc repo. File này **không** commit (đã gitignore) vì chứa tên chi nhánh thật của
khách hàng. Tạo file này (định dạng `{"A01": "Hà Nội", ...}`) trước khi chạy
`tools.tao_seed`, nếu không seed sẽ không có bảng quy đổi.

## Ba bước (chạy từ thư mục gốc repo)

```bash
# 1. Build lại giao diện React (nếu vừa sửa UI)
cd ui && npm run build && cd ..

# 2. Dựng seed (tên chi nhánh, KHÔNG kèm CĐPS) -> build/_seed
python -m tools.tao_seed

# 3. Đóng gói app + seed -> build/dist/KiemTraKhoaSo/
pyinstaller tools/app.spec --noconfirm --clean --distpath build/dist --workpath build/work

# 4. Gói thành 1 file cài -> build/Output/KiemTraKhoaSo-Setup-1.0.0.exe
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" tools/installer.iss
```

Hoặc chạy một phát: `tools/dong_goi.bat`

## Dữ liệu nằm ở đâu sau khi cài
- **Ứng dụng**: `%ProgramFiles%\KiemTraKhoaSo\` (chỉ đọc)
- **Dữ liệu người dùng**: `%LOCALAPPDATA%\KiemTraKhoaSo\` — cấu hình, kho chốt sổ,
  báo cáo. Lần đầu mở, app tự chép `_seed` sang đây (không đè nếu đã có).

## Vì sao KHÔNG kèm Bảng kê chứng từ và KHÔNG kèm CĐPS
File bảng kê thật 121–132 MB là dữ liệu hằng tháng của người dùng — không thuộc bộ
cài. CĐPS là số liệu tài chính thật của khách hàng — không nhúng vào bộ cài public;
người dùng tự nạp lần đầu dùng.

## Phát hành bản mới (auto-update)
1. Sửa số trong file `VERSION` (vd 1.2.0).
2. Đảm bảo `chi_nhanh.json` có ở gốc (local, không commit).
3. Build: `python -m tools.tao_seed && pyinstaller tools/app.spec --noconfirm --clean` rồi chạy ISCC (như trên).
4. Phát hành: `gh release create v1.2.0 build/Output/KiemTraKhoaSo-Setup-1.2.0.exe --title 1.2.0 --notes "..."`.
   (Lần đầu: đặt `KHO_PHAT_HANH` trong `app/cap_nhat.py` = slug repo public.)
