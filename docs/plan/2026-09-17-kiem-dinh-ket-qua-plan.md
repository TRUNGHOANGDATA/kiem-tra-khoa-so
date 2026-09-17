# Plan — Kiểm định độ đúng của kết quả kiểm tra (verdict từng chi nhánh)

_2026-09-17. Trạng thái: chờ ground-truth từ người dùng + duyệt hướng sửa._

## Vấn đề người dùng nêu
"Xem cái gì cũng đã làm hết" nhưng thực tế **chỉ A07/A08 mới chốt sổ được**. Nghi kết
quả sai.

## Điều tra trên dữ liệu thật (file `082026 A00`, 8 chi nhánh) — verdict hiện tại
| CN | ĐỎ | VÀNG | Kết luận | Check ĐỎ |
|----|----|----|----------|----------|
| A01 | 4 | 10 | chưa sẵn sàng | **C1.5**, C5.2, C5.3, C5.4 |
| A02 | 5 | 9 | chưa sẵn sàng | **C1.5**, C4.4, C5.2, C5.3, C5.4 |
| A03 | 1 | 5 | chưa sẵn sàng | **C1.5** |
| A04 | 1 | 3 | chưa sẵn sàng | **C1.5** |
| A05 | 1 | 4 | chưa sẵn sàng | **C1.5** |
| A06 | 1 | 5 | chưa sẵn sàng | **C1.5** |
| A07 | 1 | 3 | chưa sẵn sàng | **C1.5** |
| A08 | 1 | 4 | chưa sẵn sàng | **C1.5** |

**Phát hiện chính:** **C1.5 "Số tiền ≤ 0" (ĐỎ) bắn trên MỌI chi nhánh** → tất cả đều
"chưa sẵn sàng". Mẫu A08: 72 dòng Amount<0 đều là bút toán **"Kiểm kê T08.2026"**
(Nợ 3381/Có 1521/1526/1561, số âm) — **âm là hợp lệ** (điều chỉnh/kiểm kê trong Bravo),
không phải lỗi nghiêm trọng. ⇒ **C1.5 là dương tính giả**, che mất khác biệt thật giữa
các chi nhánh.

**Vì sao "16 bước Đã làm hết" mà vẫn "chưa sẵn sàng":** 16 bước (trang_thai) KHÔNG chứa
C1.5; kết luận lại lấy từ check. Nên bước xanh hết nhưng C1.5 đỏ kéo về "chưa sẵn sàng"
→ gây rối mắt.

## Việc kiểm định (theo thứ tự)
1. **C1.5 (Amount ≤ 0):** phân biệt `= 0` (đáng ngờ) vs `< 0` (thường là điều chỉnh/kiểm
   kê hợp lệ). Đề xuất: hạ `< 0` xuống **thống kê/cảnh báo** (không chặn), chỉ giữ ĐỎ cho
   `= 0` hoặc theo quy tắc hẹp. **Cần người dùng xác nhận** bản chất Amount<0.
2. **Đối chiếu ground truth:** người dùng nói chỉ A07/A08 chốt được. Sau khi hạ C1.5,
   A03–A08 đều 0 đỏ → sẽ "sẵn sàng"; nhưng thực tế A03–A06 KHÔNG nên sẵn sàng. ⇒ **cần
   biết A01–A06 thực tế vướng gì** để xem tool có bắt được không (A01/A02 đã bắt qua
   C5.x; A03–A06 hiện chỉ C1.5 → có thể tool đang THIẾU check cho các lỗi thật của họ).
3. **Kiểm từng check ĐỎ đang kéo kết luận** trên dữ liệu thật: C1.5, C5.2/C5.3/C5.4
   (kết chuyển doanh thu/chi phí → 911), C4.4 — mỗi cái xác minh là lỗi THẬT hay giả.
4. **Rà các check "luôn xanh"** (có thể quá dễ dãi, bỏ sót) — nhất là nhóm quyết định
   "sẵn sàng".
5. **Đồng bộ màn hình:** đưa lỗi chặn (như C1.5) vào tầm nhìn ở "Trạng thái khóa sổ"
   hoặc nhấn mạnh kết luận, để không hiểu nhầm "đã làm hết".
6. **Thêm test hồi quy** từ các ca đã xác nhận (C1.5 kiểm kê không chặn; A01/A02 thiếu
   kết chuyển vẫn đỏ…).

## Cần người dùng trả lời (ground truth)
- **(a)** Dòng Amount < 0 (vd "Kiểm kê", điều chỉnh) có phải bút toán **hợp lệ** không?
  (nếu đúng → hạ C1.5 khỏi mức chặn).
- **(b)** Vì sao **chỉ A07/A08** chốt được — A01–A06 thực tế còn vướng gì? (để hiệu chỉnh
  check phân biệt đúng). A01/A02 tool đang báo thiếu **kết chuyển 911 (C5.x)** — có khớp
  thực tế không?
