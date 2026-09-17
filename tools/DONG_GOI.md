# Đóng gói bộ cài trọn gói

Bộ cài `KiemTraKhoaSo-Setup-1.0.0.exe` mở lên là chạy được ngay: đã kèm sẵn **kho
CĐPS** (tên 8 chi nhánh + Cân đối phát sinh các kỳ). Người dùng chỉ thả **Bảng kê
chứng từ** hằng tháng vào rồi bấm Kiểm tra. Không cần cài Python.

## Máy build cần
- Python 3.14 + `pip install -r requirements.txt` + `pip install pyinstaller`
- Inno Setup 6 (`winget install JRSoftware.InnoSetup`)
- Đã có sẵn CĐPS thật trong `1. Source/BANG CAN DOI PHAT SINH/` để dựng seed

## Ba bước (chạy từ thư mục gốc repo)

```bash
# 1. Build lại giao diện React (nếu vừa sửa UI)
cd ui && npm run build && cd ..

# 2. Dựng seed (kho CĐPS + tên chi nhánh) -> build/_seed
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

## Vì sao KHÔNG kèm Bảng kê chứng từ
File bảng kê thật 121–132 MB, là dữ liệu hằng tháng của người dùng — không thuộc bộ
cài. Chỉ kèm CĐPS (nhẹ) vì đó là "database" cần có sẵn để đối chiếu.
