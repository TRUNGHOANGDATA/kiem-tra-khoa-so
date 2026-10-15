# Thuế GTGT từ Sổ chi tiết bán hàng — C3.2 viết lại, C3.4 mới, lưu kho 3 nguồn (1.3.0)

Ngày: 2026-10-15 · Plan: `docs/plan/2026-10-15-c32-vat-tu-so-chi-tiet-ban-hang-plan.md`

## Đã làm

| Phần | File |
|---|---|
| Parser sổ chi tiết bán hàng (tên file `So chi tiet ban hang A01 092026`, kiểm cột, kiểm kỳ ↔ DocDate) | `app/so_ban_hang.py` |
| Kho schema **v5**: bảng `nguon` (bảng kê + sổ bán hàng, BLOB gzip, vân tay sha256), `snapshot_so_ban_hang` | `app/kho/schema.py`, `luu_tru.py` |
| Chốt sổ đóng băng thêm sổ bán hàng; nhập-gộp mang theo `snapshot_cdps` + `snapshot_so_ban_hang`; `tom_tat_kho` đếm nguồn | `luu_tru.py`, `sao_luu.py` |
| **C3.2** đọc sổ bán hàng: Nợ 131/Có 511, `Amount3 = 0`, `Amount2 ≠ 0`, ngoài TransCode 2303/2110 | `app/checks/g3_thue_gtgt.py` |
| **C3.4 mới**: Nợ 521/Có 131, `Amount3 = 0` (cùng hàm lọc) — tổng **60 check** | như trên |
| Lá chắn độ tươi: 4 tổng sổ bán hàng ↔ bảng kê (chỉ so cùng loại CT HD/TL) → `ghi_chu` cảnh báo | như trên |
| Nạp bảng kê **tự ghi vào kho**; `nap_so_ban_hang_thu_muc`, `thieu_so_ban_hang` (chặn cứng), `khong_can_so_ban_hang`, `ky_trong_kho`, `nap_tu_kho` | `app/api.py` |
| Chọn nhầm sổ bán hàng làm bảng kê → báo rõ "là SỔ CHI TIẾT BÁN HÀNG" | `app/loader.py` |
| UI: Bước 2 Sổ bán hàng, Bảng kê thành Bước 3, chip ✓ ✕ – theo chi nhánh, nút "Kiểm tra lại từ kho…" | `ui/src/ChonFile.tsx`, `App.tsx`, `api.ts` |

## Kiểm trên file thật A01 (kho tạm, không chạm kho thật)

| | C3.2 | C3.4 | 4 tổng ↔ bảng kê |
|---|---|---|---|
| 09/2026 | **31 dòng · 20 CT · 121.957.260** | **6 dòng · 1 CT · −6.810.000** | khớp |
| 08/2026 | **131 dòng · 58 CT · 487.978.969** | **20 dòng · 10 CT · −32.676.776** | khớp (sau khi lọc cùng loại CT) |

Đúng từng con số dự kiến trong plan. Nạp 2 sổ bán hàng 2,9 s; nạp + lưu kho bảng kê A01
~9 s; **kiểm tra từ kho cho kết quả y hệt từ file** (60 check, 19 bước; chỉ khác độ phân
giải DocDate us/ns — vô hại). Kho sau 2 bảng kê + 2 sổ bán hàng: 9,2 MB.

## Phát hiện trong lúc làm

1. **Phiếu kế toán PK cũng ghi Nợ 131/Có 511 nhưng không lên sổ bán hàng** — A01 08/2026
   `PK2608-000026` (180.000) và `PK2608-000028` (360.000). Lần chạy đầu, phép so 4 tổng báo
   "không cùng thời điểm" OAN. Sửa: chỉ so trên loại CT mà sổ bán hàng chứa (HD/TL).
   Hệ quả nghiệp vụ: doanh thu ghi qua PK **không được C3.2 soát thuế** (sổ bán hàng không
   có chúng) — cần KTTH xác nhận PK 131/511 có phải xuất hóa đơn không.
2. **Cảnh báo "CĐPS cũ hơn bảng kê" gần như chưa bao giờ bật**: `_moc_lech_cdps` đọc mtime từ
   `tt.cac_file` — đó là TÊN file, không phải đường dẫn. Nay loader ghi sẵn `mtime_file`
   (ISO) vào `ThongTinFile`, nạp từ kho thì lấy mốc đã lưu.
3. Test cũ `JsApi()` không ép thư mục kho — từ v5 nạp bảng kê là GHI kho, nên
   `tests/conftest.py` nay ép `app.api.GOC` về `tmp_path` cho MỌI test.

## Lệch so với plan (cố ý)

- **Giữ cơ chế đọc lại file khi kỳ đã chốt** (plan §9 định bỏ). Lần đọc lại nay cũng ghi
  kho, nên kho vẫn là một nguồn sự thật — bỏ đi thì người dùng sửa file rồi bấm Kiểm tra
  sẽ thấy KHỚP giả (đúng lỗi đã sửa ngày 16/09).
- **Sổ bán hàng nạp lại không hỏi trước khi đè** (khác CĐPS): nó được đóng băng riêng lúc
  chốt nên mất bản sống không mất mốc nào; kết quả nạp vẫn nói rõ MỚI / ĐỔI / GIỐNG.
- **Không làm dải vàng "mtime sổ bán hàng vs bảng kê > 1 ngày"**: phép so 4 tổng trong C3.2
  là bằng chứng mạnh hơn (đo trực tiếp số liệu, không đoán theo giờ file).

## Chưa kiểm

- **Giao diện chưa chạy bằng mắt** (không dựng được cửa sổ pywebview ở đây) — cần mở app:
  Bước 2 nạp thư mục `1. Source/SO CHI TIET BAN HANG`, chip ✓ ✕ –, nút "Kiểm tra lại từ kho…".
- Các chi nhánh khác: chờ file — chạy bảng kiểm ở plan §11.
