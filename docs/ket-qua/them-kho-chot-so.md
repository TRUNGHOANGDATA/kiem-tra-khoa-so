# Thêm Kho chốt sổ + đối chiếu theo kỳ

Ngày 16/09/2026. Nhánh `feat/kho-chot-so`. 287 test xanh dưới `-W error`.

## Mục tiêu

Chốt sổ từng cặp (chi nhánh × kỳ) vào một **kho SQLite nhúng**
(`3. Chot so/kho_chot_so.sqlite`, git-ignored, một file = toàn bộ dữ liệu, sao
lưu = copy 1 file). Từ lần đọc file sau, đối chiếu dữ liệu nguồn với bản đã
chốt để phát hiện **thay đổi (drift)** — ai đó sửa lại chứng từ trong file
Bravo sau khi kỳ đã khóa. Kèm UI chốt/mở lại/xem thay đổi/lịch sử, và bộ công
cụ sao lưu/phục hồi/nhập-gộp kho.

## Kiến trúc

- **`app/chot_so.py`** — vân tay canonical: `van_tay(df)` → `(so_dong, tong_ps,
  ma_bam)`; `chuoi_dong(row)` chuẩn hoá một dòng thành chuỗi ổn định để băm;
  `doi_chieu(...)` trả một trong ba trạng thái **KHỚP / LỆCH / CHƯA_CHỐT**;
  `dien_diff(...)` tính danh sách dòng **thêm / bớt**, gom hiển thị theo
  `DocCode + DocNo` thay vì so từng dòng thô.
- **`app/kho/`** — package kho SQLite:
  - `schema.py` — định nghĩa bảng `snapshot` / `snapshot_check` /
    `snapshot_du_lieu` / `schema_version`.
  - `ket_noi.py` — `mo_kho()` mở kết nối + tự chạy migration; raise
    `PhienBanMoiHon` nếu file kho được tạo bởi bản tool mới hơn (chặn tool cũ
    ghi đè kho mới).
  - `luu_tru.py` — `KhoChotSo`: lớp lưu trữ **append-only** (chốt lại / mở lại
    không xoá bản ghi cũ, giữ nguyên dấu vết audit).
  - `sao_luu.py` — sao lưu (copy file kho), phục hồi (ghi đè từ file sao lưu),
    nhập-gộp (merge hai kho, ưu tiên theo thời điểm chốt mới nhất).
- **`app/api.py`** — nối UI: `chot_so`, `mo_lai_ky`, `lich_su_chot`,
  `lay_diff_chot`, `sao_luu_kho`, `phuc_hoi_kho`, `nhap_gop_kho`,
  `chon_file_sqlite`; đồng thời bơm khoá `chot` vào kết quả có sẵn của
  `_tom_tat` và `_danh_sach_don_vi` để UI hiển thị badge trạng thái chốt ngay
  trên màn hình tổng quan.
- **UI** — badge trạng thái chốt trên danh sách đơn vị, khối "chốt sổ" +
  modal xác nhận, banner cảnh báo khi phát hiện drift kèm nút xem thay đổi,
  tab lịch sử chốt, và thanh công cụ sao lưu/phục hồi/nhập kho (phong cách
  Premium Light, khớp giao diện hiện có).

## Quyết định quan trọng

1. **Lưu dòng nguồn đóng băng bằng BLOB gzip JSON `orient="table"`**, không
   dùng bảng cột hay parquet. `orient="table"` giữ schema (dtype từng cột) nên
   round-trip đọc lại không bị trôi kiểu dữ liệu — quan trọng nhất là giữ số 0
   đầu của `DocNo` (ví dụ "0087") vốn sẽ mất nếu đi qua một cột SQL kiểu số
   hay qua CSV/parquet không khai schema tường minh.
2. **Diff băm cả dòng**, không phụ thuộc vào một khoá chứng từ cố định (file
   Bravo không đảm bảo khoá duy nhất ổn định qua các lần export). Kết quả diff
   sau đó được **gom hiển thị theo `DocCode + DocNo`** để người dùng đọc theo
   đơn vị chứng từ quen thuộc, không phải theo từng dòng rời rạc.
3. **Append-only + cờ `con_hieu_luc`**: chốt lại hay mở lại một kỳ không xoá
   bản ghi cũ mà chỉ tắt cờ hiệu lực và thêm bản ghi mới — giữ nguyên toàn bộ
   lịch sử cho mục đích audit trail.
4. **C7.5 (413 – chênh lệch tỷ giá cuối kỳ) hạ từ CẦN_RA xuống nhắc nhẹ
   `la_thong_ke`** — không kéo kết luận sẵn sàng/chưa sẵn sàng của kỳ nữa, chỉ
   còn là gợi ý tham khảo. Kèm theo, `app/trang_thai.py` bước liên quan đến
   413 chuyển từ `CAN_RA` sang `TU_XAC_NHAN`. Lý do: đánh giá tỷ giá phụ thuộc
   dữ liệu ngoại tệ nhiều biến thể mà tool không đủ bằng chứng để tự kết luận
   — đúng nguyên tắc "không cảnh báo từ sự vắng mặt bằng chứng" đã áp dụng cho
   các check khác trong dự án.

## Còn để lại (stretch sau)

- Diff mức từng ô theo kiểu ba chiều (hiện tại `dien_diff` chỉ báo thêm/bớt cả
  dòng, chưa chỉ ra chính xác ô nào trong dòng đã đổi).
- Xuất lịch sử chốt ra Excel.
- Nối kho chốt với DWH SQL Server trung tâm (hiện chỉ là kho SQLite cục bộ,
  từng máy).

## Kiểm thử

`pytest -W error` — **287 passed**.

Phần UI (badge, khối chốt, modal xác nhận, banner drift, tab lịch sử, thanh
sao lưu/phục hồi/nhập kho) **không chạy được bằng test tự động** vì môi trường
này không dựng được cửa sổ GUI `pywebview`. Đã xác minh bằng `node --check`
trên các file JS liên quan và cross-trace tay giữa DOM id / hàm gọi API ở
front-end với chữ ký hàm thật trong `app/api.py` — chưa có ảnh chụp màn hình
chạy thật. **Người dùng nên tự mở app một lượt để kiểm tra bằng mắt thường**
trước khi coi tính năng là hoàn tất.
