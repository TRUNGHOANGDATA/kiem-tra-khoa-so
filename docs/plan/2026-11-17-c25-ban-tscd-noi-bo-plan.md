# C2.5 — Bán TSCĐ chuyển giao sang khay C: thu 711 phải bằng giá trị còn lại

Ngày: 2026-11-17 · Trạng thái: **ĐÃ CODE** (kết quả: `docs/ket-qua/c25-ban-tscd-chuyen-giao.md`) ·
Đích: 1.4.0 · Cách tính: lấy nguyên từ dự án Power BI nội bộ (`giai_trinh_chuyen_giao_tscd.py`,
sheet "TSCĐ - theo khay"), đã sửa theo red-team.

Repo public: plan này không ghi tên công ty và số tiền thật. Số đo chi tiết nằm ở memory.

## 1. Luật nghiệp vụ (người dùng chốt 16–17/11)

Khi chuyển TSCĐ từ khay A (pháp nhân cũ) sang khay C (pháp nhân nhận), **không được ghi chênh
lệch**. Hóa đơn bán xuất đúng giá trị còn lại (GTCL):
- Nợ 214 / Có 21x và **Nợ 811 / Có 21x = GTCL**;
- Nợ 131 / **Có 711 = GTCL** (+ Có 33311).

Lệch thì báo **✕ ĐỎ** (người dùng chốt).

## 2. Cách tính

Mỗi khay × kỳ, bỏ mọi dòng đối ứng 911:

| Chỉ tiêu | Công thức | Vào chênh? |
|---|---|---|
| Thu | Σ **Nợ 131 / Có 711**, khách là pháp nhân nhận − Σ bút toán đảo Nợ 711 / Có 131 | có |
| GTCL | Σ Nợ 811 / Có 21x − Σ Nợ 21x / Có 811, **trừ** dòng nội bộ | có |
| **Chênh** | Thu − GTCL; ngưỡng **1.000đ × số tài sản** | — |
| GTCL chuyển nội bộ | diễn giải chứa "Bán Hà Nội" / "An Giang", hoặc **không** chứa "HCM" | ghi chú |
| Tất toán CCDC / chi phí chờ phân bổ | Nợ 811 / Có 24x, 6xx, 15x | ghi chú |
| Nợ 133 / Có 711, khách pháp nhân nhận | thuế đầu vào ghi vào thu nhập khác | ⚠ đánh dấu |

**Khác bản Power BI (theo red-team 17/11):**

1. **Thu chỉ lấy dòng Nợ 131.**
   - Tên khách khớp cả các chi nhánh của pháp nhân nhận, ví dụ dòng phạt trừ lương Nợ 334 / Có 711.
   - Không lọc thì ĐỎ giả ở 6/14 khay kỳ 10.
   - Lọc như vậy vẫn giữ nguyên các số Power BI đã báo ngày 15/11.
2. **Tính ròng (trừ bút toán đảo).** Kế toán sửa bằng bút toán đảo thì cảnh báo tắt được.
3. **Ngưỡng 1.000đ × số tài sản** chứ không phải 0.
   - Hóa đơn làm tròn nghìn đồng cho từng tài sản.
   - A08 file 15/11 lệch tổng 48đ trên 53 tài sản. Power BI coi là khớp; ngưỡng 1đ sẽ báo ĐỎ giả.
4. **Tiêu chí để thẳng trong code, không đưa vào `cau-hinh.json`.**
   - Tiêu chí chỉ gồm tên thành phố trong tên khách và từ khóa diễn giải.
   - Khóa cấu hình mới sẽ bị `_ghi_tho` xóa mỗi lần lưu Cài đặt, và máy đang dùng không bao giờ
     nhận được giá trị mặc định.

## 3. Thiết kế check

**C2.5 "Bán TSCĐ chuyển giao: thu 711 ≠ giá trị còn lại"**, nhóm G2, chạy trên bảng kê từng khay.

- Không có dòng thu / GTCL nào thuộc diện → đứng ngoài (`la_thong_ke`), không báo đạt.
- Khớp trong ngưỡng → ✓, bảng chi tiết rỗng. Ghi chú vẫn nêu số Thu / GTCL / chênh.
- Lệch → ✕ ĐỎ. Bảng chứng minh gồm các dòng vào chênh và dòng Nợ 133 / Có 711, có cột "Loại
  bút toán". Ghi chú nêu Thu, GTCL, chênh, GTCL nội bộ, tất toán, và "Thu − GTCL − tất toán".
- Bán TSCĐ cho khách ngoài không xét.

## 4. Còn mở

- **Nợ 133 / Có 711 ở A08:** hỏi kế toán. Hiện chỉ đánh dấu.
- **Phần tất toán bán kèm.** Theo luật Power BI, phần này không vào GTCL. Số "Thu − GTCL − tất
  toán" trong ghi chú cho thấy nếu tính cả phần này thì chênh co lại nhiều, nhưng vẫn khác 0. Nếu
  KTTH đổi luật thì sửa đúng một dòng.
- **C2.6 hàng hóa chuyển giao** (doanh thu 511 = giá vốn 632): chưa làm, chờ người dùng.
