# C2.5 — Bán TSCĐ chuyển giao: thu 711 ≠ giá trị còn lại

Ngày: 2026-11-17 · Plan: `docs/plan/2026-11-17-c25-ban-tscd-noi-bo-plan.md`

## Đã làm

| Phần | File |
|---|---|
| C2.5 (nhóm G2, ✕ ĐỎ): thu Nợ 131 / Có 711 từ pháp nhân nhận so với GTCL Nợ 811 / Có 21x, tính ròng, bỏ đối ứng 911, ngưỡng 1.000đ × số TS | `app/checks/g2_dinh_khoan.py` |
| Nhãn cột "Loại bút toán" | `app/checks/base.py` |
| 12 test mới; đổi số check 60 → 61 ở 3 test cũ | `tests/test_c25_ban_tscd.py`, `test_g2_dinh_khoan.py`, `test_du_lieu_bien.py`, `test_chay_tat_ca.py` |

Plan được red-team trước khi code, ra 8 điểm. Đã sửa:
- **Thu chỉ lấy dòng Nợ 131.** Không lọc thì ĐỎ giả ở 6/14 khay.
- **Tính ròng.** Bút toán đảo được trừ đi, nên kế toán sửa xong thì cảnh báo tắt.
- **Bảng chi tiết rỗng khi khớp.** Không thì khay khớp cũng bị tính thành lỗi.
- **Tiêu chí để trong code, không đưa vào cấu hình.** Khóa cấu hình mới sẽ bị xóa khi lưu Cài đặt.
- **Thêm test** tìm từ khóa nguyên văn (không regex) và cho frame rỗng.

Tiêu chí trong code chỉ là tên thành phố và từ khóa diễn giải, không có tên công ty.

## Test

**549 xanh** dưới `pytest -W error`.

## Kiểm thật (chỉ đọc file, không chạm kho)

| Dữ liệu | Kết quả |
|---|---|
| File 15/11 mà Power BI đã dùng (khay A cũ A04–A08) | A04–A07 ✕ ĐỎ, chênh **trùng đúng** số Power BI. A08 ✓ (lệch 48đ trên 53 TS, trong ngưỡng) |
| T00 17/11, 14 khay | A04–A08 ✕ ĐỎ. A01–A03 và C01–C06 đứng ngoài (–), không ĐỎ giả |
| Bảng kê 07–09/2026 (red-team đo) | Không kỳ nào kích hoạt C2.5 |

Số tiền chi tiết từng khay để ở memory (repo public).

- **A05 và A06:** chênh trên T00 nhỏ hơn hẳn bản 15/11, vì kế toán đang điều chỉnh.
- **A08:** 15/11 khớp, nay lệch. Sau 15/11 có thêm phiếu PK ghi Có 711, ứng với phần tất toán chi
  phí chờ phân bổ. Trong đó có 5 dòng Nợ 133 / Có 711, đã được đánh dấu ⚠.

## Phát hiện

- Nếu cộng cả phần tất toán bán kèm (Nợ 811 / Có 24x, 6xx, 15x) vào GTCL, chênh ở cả 5 khay co
  xuống vài chục tới ~100 triệu, nhưng vẫn khác 0. Luật hiện theo Power BI: không cộng. Ghi chú
  của check nêu sẵn con số này để KTTH quyết.
