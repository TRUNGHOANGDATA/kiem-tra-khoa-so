# Tool kiểm tra khóa sổ cuối kỳ — hướng dẫn cho Claude

File này đi theo repo nên **không phụ thuộc tài khoản Claude**: đổi tài khoản/tổ chức, mất
memory, máy mới… Claude vẫn nắm được dự án từ đây. Trả lời người dùng bằng **tiếng Việt**.

> **Repo này PUBLIC** (`github.com/TRUNGHOANGDATA/kiem-tra-khoa-so`, kênh cập nhật của app).
> KHÔNG đưa vào file commit: tên khách hàng, số tiền/số chứng từ thật, tên chi nhánh thật
> (nằm ở `chi_nhanh.json`, gitignore). Số liệu thật chỉ ghi vào memory hoặc `_backup_claude/`.

## Bắt đầu phiên

1. Đọc memory dự án (index `MEMORY.md`). **Memory trống** (tài khoản mới, tổ chức tắt
   auto-memory…) → đọc bản sao `_backup_claude/<ngày mới nhất>/memory/` (local, gitignore).
   File đọc trước: `tool-kiem-tra-khoa-so-trang-thai.md`, rồi file mới nhất theo ngày.
2. `git log --oneline -10` + `git status` — plan nào đang dở thì nằm ở `docs/plan/` mà
   chưa có file tương ứng trong `docs/ket-qua/`.
3. Phiên bản hiện hành: file `VERSION`.

## Dự án là gì

App desktop (pywebview + React) soát **bảng kê chứng từ Bravo** trước khi khóa sổ tháng
(Thông tư 200, nhiều chi nhánh — đơn vị kiểm là `BranchCode`, không phải file). Ba nguồn:
**CĐPS** (cân đối phát sinh), **Sổ chi tiết bán hàng** (thuế GTGT từng dòng hàng), **Bảng kê
chứng từ** — cả ba lưu trong kho SQLite `3. Chot so/kho_chot_so.sqlite` (schema ở
`app/kho/schema.py`). 11 nhóm check `app/checks/g1..g11`, mỗi module `kiem_tra(df, ctx)`.

| Việc | Lệnh |
|---|---|
| Chạy app (dev) | `python -m app.main` hoặc `Kiem_tra_khoa_so.bat` |
| Test | `python -m pytest -W error -q tests` (phải xanh hết) |
| Build giao diện | `cd ui && npm run build` → `app/webapp/index.html` (commit file này) |
| Đóng gói + phát hành | skill `phat-hanh` · chi tiết `tools/DONG_GOI.md` |

Tài liệu: `docs/spec/` (thiết kế) → `docs/plan/` (kế hoạch) → `docs/ket-qua/` (nhật ký,
số đo thật, quyết định). Mỗi đợt việc lớn đi đủ ba bước này.

## Luật cứng (đã trả giá mới có)

- **Test KHÔNG được chạm kho thật.** `tests/conftest.py` ép `app.api.GOC` và thư mục xuất về
  `tmp_path` cho mọi test — đừng gỡ. Script soát dữ liệu thật: luôn dùng kho tạm
  (`api._thu_muc_kho = tempfile.mkdtemp()`). Đã từng ghi 12 bản chốt rác vào kho người dùng.
- **Người dùng mù màu.** Mọi mức độ phải có ký hiệu + chữ: `✕` lỗi · `▲` cảnh báo · `✓` đạt
  · `–` không áp dụng. Màu chỉ là phụ.
- **Không cảnh báo từ "không thấy bằng chứng".** Thiếu dữ liệu để kết luận → `la_thong_ke=True`
  (đứng ngoài kết luận), không phải VÀNG/ĐỎ. Chỉ cảnh báo khi trong file có bằng chứng thật.
- **Phiên bản chỉ sửa ở file `VERSION`**, rồi build lại `ui` (số phiên bản nhồi lúc build).
- **Màn Kết quả:** khối phụ không xếp chồng dọc cùng cột với khu làm việc.
- **Độ tươi dữ liệu:** các nguồn phải kết xuất CÙNG thời điểm; lệch là đối chiếu chéo nói
  sai. Trước khi kết luận "sổ sai", kiểm hai nguồn có cùng lát cắt không.
- **Giao dịch nội bộ nhận theo `TransCode`, không theo số hiệu TK** (`g3.TRANSCODE_NOI_BO`).
  "Chi nhánh" (2303/2110) = cùng pháp nhân, không VAT; "Công ty nội bộ" (2304/2112) = pháp
  nhân khác, PHẢI có VAT. Danh mục gốc: `1. Source/Danh mục loại giao dịch.xlsx`.
- **Sổ chi tiết bán hàng:** `Amount2` = doanh thu, `Amount3` = thuế, `Amount` = **giá vốn**.
  Không có cột chi nhánh — gán chi nhánh qua `Id` (= Id chứng từ trong bảng kê); `DocNo`
  trùng giữa chi nhánh nên KHÔNG dùng làm khóa.
- Dữ liệu `.xlsx` không bao giờ vào git (`.gitignore` đã chặn `*.xlsx`, `1. Source/`…).

## Cách làm việc người dùng muốn

- Đổi một check: **đo trên dữ liệu thật trước** (skill `soat-du-lieu-that`), nói rõ số dòng
  / số chứng từ / số tiền trước–sau, rồi mới sửa. Người dùng là kế toán tổng hợp — luật
  nghiệp vụ do họ chốt; số đo mâu thuẫn với luật thì hỏi, không tự đổi.
- Làm trọn một đợt ("làm 1 lần, không chia phase"), test xanh, rồi mới hỏi commit/phát hành.
- Commit thẳng `main` khi người dùng bảo; thông điệp không dấu, kiểu `feat(g3): …`,
  `release: X.Y.Z (…)`.
- Nhiều quyết định nghiệp vụ chi tiết (vì sao hẹp/bỏ từng check, ground truth từng chi
  nhánh) nằm trong memory — đọc trước khi "sửa cho đúng" một check có vẻ lạ.

## Môi trường máy này (không gắn với tài khoản Claude)

Python 3.14 · Node · PyInstaller · Inno Setup 6 ở `%LOCALAPPDATA%\Programs\Inno Setup 6\` ·
`gh` CLI đã đăng nhập GitHub (keyring, độc lập với Claude). App đã cài lưu dữ liệu ở
`%LOCALAPPDATA%\KiemTraKhoaSo\`; bản dev lưu ở thư mục repo.
