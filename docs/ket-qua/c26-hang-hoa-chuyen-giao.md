# C2.6 — Hàng hóa chuyển giao: doanh thu ≠ giá vốn

Ngày: 2026-11-17 · Plan: `docs/plan/2026-11-17-c26-hang-hoa-chuyen-giao-plan.md`

## Đã làm

| Phần | File |
|---|---|
| C2.6 (nhóm G2, ▲ VÀNG, ngưỡng 0đ): doanh thu 5111/5112 (trừ 521, ròng) so với giá vốn 632 (ròng) trên chứng từ có khách pháp nhân nhận; chỉ xét khay × kỳ có chuyển giao TSCĐ | `app/checks/g2_dinh_khoan.py` |
| Tiêu chí chung với C2.5 (`_chuyen_giao`); nhãn cột Doanh thu / Giá vốn / Chênh | `app/checks/g2_dinh_khoan.py`, `app/checks/base.py` |
| 12 test mới; đổi số check 61 → 62 | `tests/test_c26_hang_hoa_chuyen_giao.py` và 3 test đếm |

Red-team tìm 6 điểm. Đã sửa:
- **Doanh thu dịch vụ 5113:** bị tính nhầm là hàng, làm chênh sai dấu ở A04 và A07. Giờ chỉ lấy 5111/5112.
- **Tính ròng:** điều chỉnh ghi số âm theo cả hai chiều nên phải tính ròng; bỏ dòng kết chuyển 511 ↔ 521.
- **Lý do nhóm theo Id** ghi trong code và test đã được sửa cho đúng hình dạng dữ liệu thật.
- **Đánh dấu ⚠** dòng Nợ 133 / Có 511.

## Test

**561 xanh** dưới `pytest -W error`.

## Kiểm thật (chỉ đọc file)

| Dữ liệu | Kết quả |
|---|---|
| File 15/11 Power BI, công thức gốc (trước sửa) | Trùng đúng số Power BI ở cả 5 khay. A05 lệch âm rất lớn: xuất kho chưa ghi doanh thu |
| T00 17/11, công thức sau sửa | A04–A08 ▲ VÀNG, lệch từ −0,2% tới +2,4% doanh thu hàng. A01–A03 và C01–C06 đứng ngoài |
| Tháng 07–09 (red-team đo) | Không khay nào vào diện |

Số tiền chi tiết từng khay để ở memory (repo public). A05 có 6 dòng Nợ 133 / Có 511, đã đánh dấu ⚠.
