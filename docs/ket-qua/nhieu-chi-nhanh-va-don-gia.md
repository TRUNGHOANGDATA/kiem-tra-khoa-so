# Nhiều chi nhánh, nhiều file bảng kê — và C4.6 đơn giá xuất kho

Ngày 15/09/2026. Ba việc trong một lượt: hỗ trợ nhiều chi nhánh, sửa câu chữ của
bước tính giá xuất kho, và thêm một bộ kiểm tra đơn giá bất thường.

## 1. Đơn vị kiểm tra là CHI NHÁNH, không phải file

Bảng kê Bravo có sẵn cột `BranchCode` (file 08/2026: `A01` cho cả 79.450 dòng).
Đó là mốc duy nhất đúng trong cả hai chiều:

- **một file, nhiều chi nhánh** — xuất gộp rồi mới tách;
- **một chi nhánh, nhiều file** — xuất làm nhiều lần rồi gộp lại.

Lấy tên file làm đơn vị sẽ sai ở cả hai. Vì vậy `doc_nhieu_bang_ke` đọc từng file,
gộp lại, rồi `tach_theo_chi_nhanh` cắt theo `BranchCode`. Mỗi chi nhánh nhận một
`DonVi` riêng: frame riêng, 30 kết quả kiểm tra riêng, 11 bước riêng.

**Vì sao không chạy trên frame gộp:** mỗi chi nhánh khóa sổ trên sổ của chính
mình. TK 911 phải cân trong phạm vi một chi nhánh; kết chuyển 642 dư của chi
nhánh này không bù được phần thiếu của chi nhánh kia. Chạy 30 check trên frame
gộp sẽ cho một kết luận không thuộc về ai.

Các quyết định đi kèm:

- **Đường dẫn trùng bị bỏ qua** (có ghi vào nhật ký). Chọn nhầm cùng một file hai
  lần mà nhân đôi phát sinh của cả chi nhánh thì sai số đó không lộ ra ở đâu cho
  tới lúc đối chiếu sổ cái.
- **Dòng không có mã chi nhánh** vẫn thuộc một đơn vị tên `(không có mã chi
  nhánh)`. Bỏ rơi chúng là để phát sinh biến mất khỏi mọi kiểm tra trong im lặng.
- `ma_chi_nhanh` **tự cắt khoảng trắng** thay vì tin rằng `chuan_hoa` đã chạy: một
  mã toàn dấu cách lọt qua sẽ thành một nút không có chữ trên thanh chọn chi nhánh.
- **Kỳ suy riêng cho từng chi nhánh** — hai chi nhánh nộp hai kỳ khác nhau vẫn đọc
  được, không bị một `mode()` chung nuốt mất.

### Giao diện
Màn hình 1 nhận nhiều file (kéo-thả nhiều, hộp thoại nhiều file, hoặc "Nạp cả thư
mục") và liệt kê các chi nhánh sẽ được kiểm tra. Màn hình 2 thêm một thanh chip
chọn chi nhánh — chỉ hiện khi có từ 2 chi nhánh trở lên. Chip mang màu theo kết
luận **kèm biểu tượng và số việc phải xử lý**, không bao giờ chỉ dùng màu.

Nút "Kiểm tra" gửi lại **cả danh sách** đường dẫn. Gửi mỗi file đầu sẽ khiến
backend coi là đã đổi lựa chọn rồi nạp lại một mình nó, vứt mất các chi nhánh còn
lại — đây là cái bẫy rõ ràng nhất của bước đổi từ một file sang nhiều file.

### Báo cáo
- `xuat_bao_cao` — như cũ, cho **chi nhánh đang xem**, tên file kèm mã chi nhánh.
- `xuat_tong_hop` — một workbook: sheet so sánh mọi chi nhánh, rồi tổng quan và 11
  bước của từng chi nhánh. **Không** kèm chi tiết từng dòng vi phạm: 30 check × N
  chi nhánh vượt giới hạn sheet của Excel từ chi nhánh thứ chín, và mỗi chi nhánh
  đã có báo cáo riêng đầy đủ.

### `_kq`/`_df`… thành chỉ đọc
`JsApi` giữ `_dv: list[DonVi]` và `_i`. Các thuộc tính cũ trở thành **khung nhìn
chỉ đọc** vào chi nhánh đang xem. Không có setter: gán vào khung nhìn khi chưa nạp
đơn vị nào sẽ rơi vào hư không — đúng loại lỗi im lặng mà nhánh này đã trả giá
nhiều lần.

## 2. Bước "Tính giá xuất kho" đếm nhầm mẫu số

Câu cũ: *"46522 dòng kho, không dòng nào chưa có giá trị"*. Bước này nói về giá
**xuất** kho, nhưng con số lại là tổng mọi dòng kho — cả nhập lẫn xuất. Trên sổ
08/2026: 46.522 dòng kho nhưng chỉ **32.519 dòng xuất**.

Câu mới: *"32.519 dòng xuất kho, mọi dòng đều đã có giá trị"* — cùng dùng
`thong_ke_xuat_kho`, tức cùng một vị từ với C4.1, nên hai chỗ không thể nói lệch
nhau. Các con số cũng được ngăn cách hàng nghìn.

## 3. C4.6 — đơn giá xuất kho lệch mặt bằng mã hàng

Bravo không ghi đơn giá trên dòng xuất (xem `sua-c41-gia-xuat-kho.md`), nên đơn
giá phải suy ra bằng `Amount / Quantity9`.

**Không có ngưỡng tuyệt đối nào dùng được.** Dòng đắt nhất trên sổ 08/2026 là
**2.347.789.345đ/đơn vị** (mã `TSCCDC129`, xuất 1 đơn vị) và nó hoàn toàn hợp lệ —
một TSCĐ. Một ngưỡng tuyệt đối sẽ bắt nó và bỏ sót mọi thứ khác.

Mốc so sánh duy nhất có nghĩa là **trung vị của chính mã hàng đó trong kỳ**. Sai
đơn vị tính hay gõ nhầm số lượng lộ ra ở đó, không lộ ra ở con số tuyệt đối.

- **Trung vị, không phải trung bình** — một dòng lệch 251 lần kéo trung bình lên
  theo mình rồi tự che mất.
- **Mã hàng xuất dưới 3 lần thì bỏ qua** và nói rõ trong ghi chú (sổ 08/2026: 491
  dòng). Im lặng ở đây sẽ bị đọc thành "đã soi và không thấy gì".
- Mức 🟡, không phải 🔴: đây là việc cần rà, không phải bút toán sai chắc chắn.

Đo trên file thật: **48 dòng / 9 mã hàng**, tốn 0,05 s. Dòng nặng nhất là
`PX2608-002385`, mã `S103VT0600049`: SL 0,059 · tiền 450.878 → đơn giá 7.707.316,
gấp **251 lần** mặt bằng 30.755 của chính mã đó.

### Một lỗi phát sinh ngay trong bảng C4.6
Bảng chi tiết của C4.6 có cột `Quantity9` **thật** (không phải chuỗi nhúng trong
`ly_do` như C4.1). `COT_SO_HIEN_THI` làm tròn 0 chữ số, nên số lượng **0,059 sẽ in
ra "0"** — đọc đúng thành "không có số lượng", ngược hẳn với dòng đang được nêu.
Thêm `COT_SO_LE` để giao diện (`maximumFractionDigits: 9`) và Excel
(`#,##0.#########`) biết cột nào có phần thập phân.

## Kết quả trên file thật (A01, kỳ 08/2026)

Kết luận đầu trang **không đổi**: "CHƯA SẴN SÀNG KHÓA SỔ — còn 2 việc phải xử lý".
C4.6 là một mục 🟡 mới cần rà, không phải một việc chặn khóa sổ.

231 test xanh dưới `-W error`.
