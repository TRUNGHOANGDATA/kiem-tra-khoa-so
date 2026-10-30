---
name: soat-du-lieu-that
description: Đo một check (hoặc một thay đổi logic) của tool kiểm tra khóa sổ trên file Bravo THẬT trước khi sửa/kết luận — kho tạm, so trước/sau theo chi nhánh × kỳ. Dùng khi người dùng báo "check này sai", "báo giả", "kiểm lại trên dữ liệu thật", gửi file Excel mới, hoặc trước khi đổi tiêu chí một check.
---

# Soát check trên dữ liệu thật

Mục tiêu: mọi thay đổi check đều có **số đo thật** (số dòng · số chứng từ · số tiền, theo
chi nhánh × kỳ) trước và sau, ghi vào `docs/ket-qua/`.

## 1. An toàn trước tiên
- **KHÔNG mở kho thật** (`3. Chot so/`, `%LOCALAPPDATA%\KiemTraKhoaSo\`) bằng `KhoChotSo` hay
  `JsApi()` mặc định — mở là có thể tự nâng schema/ghi dữ liệu. Muốn xem kho thật: `sqlite3`
  với URI `?mode=ro`.
- Script soát: `api = JsApi(); api._thu_muc_kho = api.thu_muc_report = tempfile.mkdtemp()`.
- Script/tệp tạm để ở scratchpad, không để trong repo. File `.xlsx` không bao giờ commit.
- Console Windows: `export PYTHONIOENCODING=utf-8` trước khi in tiếng Việt.

## 2. Nạp dữ liệu (đúng đường app dùng)
- Bảng kê: `app.loader.doc_bang_ke` / `doc_nhieu_bang_ke` (tách theo `BranchCode`).
- Sổ chi tiết bán hàng: `app.so_ban_hang.doc_so_ban_hang` (mã CN + kỳ từ tên file).
- CĐPS: `app.cdps.doc_cdps`.
- Hoặc đi trọn luồng: `api.nap_so_ban_hang_thu_muc(...)`, `api.nap_nhieu_file([...])`,
  `api.chay_kiem_tra(paths)` rồi đọc `api._dv[i].kq["C3.2"].chi_tiet`.
- File 100+ MB đọc mất 25–35 s; chỉ cần vài cột thì `pd.read_excel(..., engine="calamine",
  usecols=[...])`.

## 3. Đo
- Kiểm độ tươi trước: các nguồn có kết xuất cùng lúc không (mtime file, tổng PS 511 khớp
  giữa nguồn). Lệch → kết luận chéo nguồn chưa đáng tin.
- Đếm theo chi nhánh × kỳ: số dòng, số chứng từ (`DocCode`+`DocNo`), tổng tiền.
- Soi tay vài chứng từ lớn nhất mỗi nhóm; tách "lỗi thật" vs "báo giả" và **nguyên nhân gốc**.
- So với ground truth của kế toán tổng hợp trong memory (chi nhánh nào đã xác nhận sạch/lỗi).
- Mâu thuẫn với luật nghiệp vụ đã chốt → hỏi người dùng, không tự đổi luật.

## 4. Ghi lại
- `docs/ket-qua/<chủ-đề>.md`: bảng trước/sau, nguyên nhân gốc, quyết định. Commit được
  (repo public) thì **bỏ tên khách hàng, tên chi nhánh thật**; số liệu chi tiết để ở memory.
- Thêm test tái hiện (DataFrame tự dựng qua `tests/conftest.py::tao_df` / `tao_sbh`).
