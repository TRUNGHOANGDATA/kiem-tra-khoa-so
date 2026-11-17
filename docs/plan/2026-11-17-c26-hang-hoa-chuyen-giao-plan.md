# C2.6 — Hàng hóa chuyển giao sang khay C: doanh thu 511 phải bằng giá vốn 632

Ngày: 2026-11-17 · Trạng thái: **ĐÃ CODE** (kết quả: `docs/ket-qua/c26-hang-hoa-chuyen-giao.md`) · Đích: 1.5.0
Cách tính: lấy từ dự án Power BI nội bộ (`giai_trinh_chuyen_giao_tscd.py`, sheet "Hàng hoá -
theo khay"). Repo public: không ghi tên công ty hay số tiền thật; số đo chi tiết ở memory.

## 1. Luật (người dùng chốt 17/11)

Hàng hóa chuyển giao từ khay A sang khay C bán **đúng giá vốn**: doanh thu (Có 511/521) = giá vốn
(Nợ 632). Lệch thì báo **▲ VÀNG**, ngưỡng **0 đồng** (|chênh| < 1đ mới ✓).

## 2. Cách tính (Power BI, sửa theo số đo)

1. **Phạm vi khay × kỳ:** chỉ khay × kỳ có **chuyển giao TSCĐ** theo C2.5, tức có dòng GTCL Nợ
   811 / Có 21x không thuộc nội bộ.
   - Power BI chỉ chạy trên khay A cũ (A04–A08 kỳ 10).
   - Chạy theo "mọi chứng từ có khách pháp nhân nhận" thì đo kỳ 10 bắt cả **A01** (bán hàng
     thường cho chi nhánh khay C, có lãi là đúng) và **C02–C06** (khách là chính khay đó). Như vậy
     là VÀNG giả ở 6 khay.
2. **Chứng từ chuyển giao:** chứng từ có ít nhất một dòng khách là pháp nhân nhận (cùng tiêu chí
   tên khách của C2.5). Nhóm theo **`Id` chứng từ**, không theo `DocNo`.
   - Power BI phải gom các dòng "(không số)" thành một nhóm.
   - Đo A07: 208 dòng Nợ 632 **không có số chứng từ**, nhưng đều cùng `Id` với chứng từ có khách
     pháp nhân nhận. Nhóm theo `Id` thì bắt đúng.
   - Bảng kê thiếu cột `Id` thì lùi về (DocCode, DocNo).
3. Bỏ dòng đối ứng 911.
4. **Chênh** = Σ Có 511/521 − Σ Nợ 632 trên các chứng từ đó (gộp cả khay, y Power BI).
   - Giảm doanh thu (Nợ 511/521) và giảm giá vốn (Có 632) **nêu trong ghi chú**, không vào chênh,
     y Power BI.
5. **Bảng chứng minh:** mỗi chứng từ một dòng (Loại CT, Số CT, Diễn giải đầu, Doanh thu, Giá vốn,
   Chênh), chỉ những chứng từ có DT ≠ GV.
   - Một khay có thể ghi doanh thu và giá vốn ở **hai chứng từ khác nhau** (A07). Từng dòng có
     thể lệch lớn nhưng bù trừ nhau; kết luận dựa trên **tổng khay**.

## 2b. Sửa sau red-team (17/11) — khác Power BI có chủ đích

- **Doanh thu chỉ lấy 5111/5112 (+ trừ 521).**
  - Chứng từ của khách pháp nhân nhận còn có doanh thu 5113 (cho thuê xe, phần mềm), không có giá
    vốn đi kèm. Tính gộp vào thì chênh sai dấu ở A04 và A07.
  - Cho thuê xe xuất hóa đơn hằng tháng, nên nếu để vậy sẽ sinh ▲ giả.
  - 5113/5118 chỉ đưa vào ghi chú.
- **Tính ròng** (Có − Nợ cho doanh thu, Nợ − Có cho 632), thống nhất với C2.5.
  - Điều chỉnh ghi số âm theo cả hai chiều. Tính gộp thì kế toán sửa xong ▲ vẫn không tắt.
  - Bỏ dòng kết chuyển nội tại 511 ↔ 521.
- **Nhóm theo `Id`, thiếu `Id` thì lùi về (DocCode, DocNo).** Lý do đúng: dòng giá vốn không số
  chứng từ (A07) **tự mang tên khách** pháp nhân nhận, nên vào diện theo chính nó.
- Dòng **Nợ 133 / Có 511** (thuế đầu vào ghi doanh thu) được đánh dấu ⚠ ở ghi chú.
- **Giới hạn đã biết:** tháng chỉ chuyển hàng mà không chuyển TSCĐ thì không xét. Ghi chú nêu rõ
  điều này.

## 3. Số đo kỳ 10 (T00 17/11, sổ chưa chốt)

- Cả 5 khay A04–A08 đều lệch (sau sửa: từ −0,2% tới +2,4% doanh thu hàng). Ngưỡng 0đ → cả 5 khay ▲ VÀNG.
- Theo từng chứng từ: phần lớn chứng từ có cả DT và GV đều lệch (A04 9/12). Giá xuất hóa đơn
  khác giá vốn bình quân tính cuối tháng.
- Bản 15/11 (Power BI): A05 lệch âm rất lớn (xuất kho chưa ghi doanh thu). Bản 17/11 đã sửa.

## 4. Các bước

1. `app/checks/g2_dinh_khoan.py`: `_c26(df)` dùng chung tiêu chí của C2.5 (`KHACH_NHAN`, nhận
   GTCL chuyển giao).
2. Test (`tao_df`):
   - khớp → ✓;
   - lệch → ▲;
   - không có chuyển giao TSCĐ → đứng ngoài;
   - khay chỉ bán hàng thường cho khách pháp nhân nhận (không có TSCĐ chuyển giao) → đứng ngoài;
   - doanh thu và giá vốn ở hai chứng từ khác `Id` vẫn cộng đúng;
   - dòng giá vốn không số chứng từ cùng `Id` được tính;
   - 911 bỏ;
   - giảm DT/GV ở ghi chú.
3. Kiểm thật: file 15/11 Power BI → đúng số Power BI. T00 17/11 → chỉ A04–A08 ▲, khay khác đứng
   ngoài.
4. `pytest -W error`, `docs/ket-qua/`, hỏi commit/phát hành.
