# Task 15 — Báo cáo kiểm thử end-to-end trên file thật & tinh chỉnh

Ngày chạy: 2026-09-15
Máy: Windows 11, Python 3.14.4, pandas 3.0.2
File thật: `1. Source/Bang ke chung tu 082027.xlsx` — 79.450 dòng dữ liệu × 79 cột,
kỳ 08/2026, tổng phát sinh Nợ ≈ 836.867.804.478 VNĐ (khớp mô tả trong đề bài).

---

## 1. Việc đã làm

1. Viết `tests/test_e2e_file_that.py` đúng theo brief (skip tự động nếu không có
   file thật — `pytestmark = pytest.mark.skipif(not os.path.exists(FILE), ...)`).
   Test dùng `tmp_path` cho `thu_muc_report` nên không sinh file trong `2. Report/`.
2. Chạy pipeline thật qua `JsApi` (không mở GUI — theo đúng chỉ đạo của controller),
   ghi lại toàn bộ số liệu bên dưới.
3. Sửa hồi quy ở `app/web/app.js` (mục 2 trong "Controller rulings"): `tieuDe`
   trong `moChiTiet` chỉ được gán vào `textContent`, không phải `innerHTML`, nên
   không cần (và không nên) đi qua `esc()` — `esc()` mã hoá entity HTML
   (`&`→`&amp;`...) nhưng `textContent` không giải mã lại, nên tiêu đề chứa
   `&`, `<`, `>`, `"`, `'` sẽ hiển thị sai (vd. `&gt;` thay vì `>`).
4. Rà 29 check trên dữ liệu thật, đối chiếu 3 mục nghi vấn được giao (C5.1,
   C4.1/Amount âm, danh sách cột số trong `app.js`) — xem mục 4.
5. Không sửa bất kỳ ngưỡng/điều kiện nào trong `app/checks/*` — xem lý do ở
   mục 4 và 5 (mọi phát hiện đều là "judgement call" cần controller quyết định,
   không có trường hợp nào đủ rõ ràng để tự sửa theo tiêu chí "false positive
   trên sổ sách đúng, sửa an toàn tuyệt đối" mà brief yêu cầu).

---

## 2. Thời gian chạy `chay_kiem_tra`

Đo bằng script độc lập (không qua pytest, tránh nhiễu do capture I/O) và bằng
chính test e2e (`python -m pytest tests/test_e2e_file_that.py -q -s`, cần
`PYTHONUTF8=1` trên máy này vì console mặc định là cp1252 và không decode được
tiếng Việt khi in trực tiếp — không phải lỗi của code, chỉ là code page của
console Windows; test dùng `print()` thường vẫn chạy tốt trong pytest bình
thường vì pytest capture output bằng encoding riêng).

| Lần đo | Thời gian `chay_kiem_tra` (đọc file + 29 check) |
|---|---|
| Script trực tiếp | 9,64 s |
| pytest -s (đo trong test) | 9,1 – 9,6 s |
| `doc_bang_ke` một mình (đọc Excel, chuẩn hoá) | 8,3 – 8,5 s |

**Kết luận:** ~86-90% thời gian là đọc + chuẩn hoá Excel bằng engine `calamine`
(79.450 dòng × 79 cột, file 30MB); phần chạy 29 check trên DataFrame đã nạp chỉ
mất dưới 1,5 giây. Đạt mục tiêu "dưới 10 giây" của kế hoạch (biên độ mỏng,
9,1-9,7s tuỳ lần chạy) và dư giả so với ngưỡng 60s của assertion trong test.
Không cần tối ưu thêm ở bước này; nếu muốn margin an toàn hơn, hướng tối ưu duy
nhất đáng làm là đọc Excel (cache, đọc cột cần thiết thay vì cả 79 cột, hoặc
convert sang parquet một lần) — không phải tối ưu logic check.

`xuat_bao_cao()` (ghi workbook Excel đầy đủ Tổng quan/Trạng thái/29 sheet chi
tiết/Nhật ký) mất thêm 4,3s, file kết quả 2.157.553 bytes, mở đọc được bình
thường bằng `openpyxl`/Excel.

---

## 3. Bảng đầy đủ 29 check (mã, tên, mức độ, số lỗi)

| Mã | Tên | Mức độ | Số lỗi | Ghi chú |
|---|---|---|---:|---|
| C1.1 | Thiếu diễn giải | vàng | 26.958 | xem mục 5.1 |
| C1.2 | Ngày chứng từ ngoài kỳ | xanh | 0 | |
| C1.3 | Nghi trùng bút toán | vàng | 2.335 | |
| C1.4 | TK Nợ = TK Có | **đỏ** | 2.488 | xem mục 5.2 |
| C1.5 | Số tiền ≤ 0 | **đỏ** | 243 | xem mục 4.2 |
| C1.6 | Thiếu số chứng từ / ngày | xanh | 0 | |
| C2.1 | Thiếu mã đối tượng ở TK công nợ | xanh | 0 | |
| C2.2 | Tài khoản sai định dạng | xanh | 0 | |
| C2.3 | Chuyển tiền nội bộ cùng nhóm TK | vàng | 27 | |
| C2.4 | Lệch quy đổi ngoại tệ | vàng | 7 | không ồn (brief nêu ví dụ giả định, thực tế không xảy ra) |
| C3.1 | Có mã thuế nhưng chứng từ thiếu TK thuế | vàng | 157 | |
| C3.2 | Doanh thu thiếu thuế đầu ra | vàng | 68 | |
| C3.3 | Tổng hợp thuế GTGT theo mã thuế | xanh | 0 (thống kê) | la_thong_ke |
| C4.1 | Xuất/nhập kho giá = 0 | **đỏ** | 30.502 | xem mục 4.3 — ồn nhất trong 29 check |
| C4.2 | Tiền ≠ Số lượng × Đơn giá | vàng | 397 | |
| C4.3 | Giá vốn không đối ứng TK kho | xanh | 0 | |
| C4.4 | Chưa tập hợp chi phí SX về 154 | xanh | 0 | |
| C4.5 | Chưa nhập kho thành phẩm 154 → 155 | xanh | 0 | |
| C5.1 | TK đầu 5/6/7/8 chưa kết chuyển hết | vàng | 3 | xem mục 4.1 |
| C5.2 | Thiếu kết chuyển giá vốn 632 → 911 | xanh | 0 | |
| C5.3 | Thiếu kết chuyển doanh thu → 911 | xanh | 0 | |
| C5.4 | Thiếu kết chuyển chi phí → 911 | **đỏ** | 1 | TK 642 còn dư ~19,7 triệu — phát hiện thật, không ồn |
| C5.5 | Thiếu kết chuyển lãi/lỗ 911 ↔ 421 | xanh | 0 | |
| C5.6 | Thiếu khấu trừ thuế GTGT | xanh | 0 | |
| C6.1 | Top 50 giao dịch giá trị lớn | xanh (thống kê) | 0 | la_thong_ke |
| C6.2 | Phát sinh theo tài khoản | xanh (thống kê) | 0 | la_thong_ke |
| C6.3 | Phát sinh theo loại chứng từ | xanh (thống kê) | 0 | la_thong_ke |
| C6.4 | Phát sinh theo người lập | xanh (thống kê) | 0 | la_thong_ke |
| C6.5 | Phân bố bút toán theo ngày | xanh (thống kê) | 0 | la_thong_ke |

**Tổng số check "đỏ" có lỗi: 4** (C1.4, C1.5, C4.1, C5.4) — khớp `so_do: 4`.
**Tổng số check "vàng" có lỗi: 8** (C1.1, C1.3, C2.3, C2.4, C3.1, C3.2, C4.2,
C5.1) — khớp `so_vang: 8`.

---

## 4. Bảng đầy đủ 11 bước khóa sổ (Tab A)

| # | Bước | Trạng thái | Tóm tắt |
|---|---|---|---|
| 1 | Tập hợp CP NVL trực tiếp 621 → 154 | ✅ đã làm | Nợ 10.330.447.075 / Có 10.330.447.075 — đã về 0 |
| 2 | Tập hợp CP nhân công trực tiếp 622 → 154 | ✅ đã làm | Nợ 22.957.338 / Có 22.957.338 — đã về 0 |
| 3 | Tập hợp & phân bổ CP SXC 627 → 154 | ✅ đã làm | Nợ 957.918.289 / Có 957.918.289 — đã về 0 |
| 4 | Nhập kho thành phẩm 154 → 155 (tính giá thành) | ✅ đã làm | Nợ 155/157/632 / Có 154: 9.039.759.064 |
| 5 | Xuất kho có đầy đủ giá | ⚠️ cần rà | Còn 30.502 dòng kho có số lượng nhưng giá = 0 |
| 6 | Kết chuyển giá vốn 632 → 911 | ✅ đã làm | Nợ 18.464.470.188 / Có 18.464.470.188 — đã về 0 |
| 7 | Kết chuyển doanh thu 511/515/711 → 911 | ✅ đã làm | Đã kết chuyển: 511, 515, 711 |
| 8 | Kết chuyển chi phí 635/641/642/811 → 911 | ⚠️ cần rà | Kết chuyển chưa hết — 642 còn 19.727.324 |
| 9 | Khấu trừ thuế GTGT 3331 ↔ 1331 | ✅ đã làm | Thuế vào 8.459.970.698 / thuế ra 2.676.056.026 — đã khấu trừ |
| 10 | Kết chuyển lãi/lỗ 911 ↔ 421 | ✅ đã làm | Đã có bút toán 911 ↔ 421 |
| 11 | TK đầu 5/6/7/8 đã về 0 (kết chuyển hết) | ⚠️ cần rà | Còn 3 tài khoản có net ≠ 0 |

Không bước nào rơi vào `khong_ap_dung` hay `chua_lam` — thoả yêu cầu của test
e2e (G4/G5 phải phản ánh dữ liệu thật, có phát sinh 621/632 thật).

---

## 5. Kết luận đầu (headline)

```
so_dong: 79.450   tong_ps: 836.867.804.477,78
so_do: 4   so_vang: 8   so_chua_lam: 0   con_viec: 4
san_sang: FALSE  →  "CHƯA SẴN SÀNG — còn 4 việc"
```

`lay_chi_tiet` xác nhận phân trang đúng: C1.1 có 26.958 dòng vi phạm nhưng
`lay_chi_tiet("C1.1", 1, 100)` chỉ trả 100 dòng/trang (≤500 theo giới hạn cứng
trong `api.py`); tương tự C4.1 (30.502 dòng) trả đúng số dòng theo `kich_thuoc`
yêu cầu. `xuat_bao_cao()` sinh file Excel đọc được, có đủ sheet Tổng quan/Trạng
thái/29 sheet chi tiết/Nhật ký (2.157.553 bytes).

---

## 6. Ba mục nghi vấn được giao — phát hiện trên dữ liệu thật

### 6.1. C5.1 — gộp theo tài khoản cấp con có gây "chưa kết chuyển hết" giả không?

**Không xảy ra trên file này.** Kiểm tra trực tiếp: doanh thu được ghi Có vào
các TK con `51111/51112/51113/51121/51122/51123` (7.703 – 8.344 dòng mỗi TK);
bút toán kết chuyển cuối kỳ (`CreditAccount == "911"`) cũng ghi Nợ đúng **cùng
mã TK con** (`51111, 51112, 51113, 51121, 51122, 51123` — mỗi mã đúng 1 dòng
kết chuyển). Tương tự phía giá vốn: Nợ 911 đối ứng Có đúng các mã con
`632111/632121/632131/632211/632221/632231`. Doanh nghiệp này **không** dùng
kiểu "ghi doanh thu vào 5111 nhưng kết chuyển bằng Nợ 511/Có 911" — họ kết
chuyển đúng ở cấp con đã ghi, nên việc `so_phat_sinh_tai_khoan` gộp theo chuỗi
TK chính xác (không gộp theo prefix cha) **không** tạo ra hai dòng lệch nhau
kiểu "ảo" như lo ngại ban đầu.

`C5.1` trên dữ liệu thật chỉ còn đúng 3 dòng, đều là phát hiện thật:
- `5215`: Nợ 37.736.893 / Có 0 → net dương 37,7 triệu, chưa hề có bút toán
  kết chuyển nào cho TK này (khoản giảm trừ doanh thu, rất có thể bị bỏ sót).
- `6427`, `6428` (chi phí QLDN dịch vụ mua ngoài / chi phí khác bằng tiền):
  còn dư lần lượt 111.478 và 19.615.846 — khớp với residual mà C5.4 báo ở
  bước 8 (TK 642 còn 19.727.324 ≈ 111.478 + 19.615.846), tức là cùng một vấn
  đề thật (kết chuyển 642→911 chưa hết) được hai check độc lập xác nhận chéo.

**Khuyến nghị:** không cần sửa `so_phat_sinh_tai_khoan`/C5.1. Rủi ro lý
thuyết về gộp sai cấp vẫn còn với công ty khác dùng kiểu ghi sổ khác, nhưng
không có bằng chứng ở đây để retune — giữ nguyên.

### 6.2. Amount âm (bút toán đỏ) — có bị C4.1 tính nhầm thành "chưa định giá" không?

**Bravo có phát sinh Amount âm**: 242 dòng Amount<0 + 1 dòng Amount=0 (khớp
`C1.5 = 243`). Phân theo cặp TK:
- `3381/1561` (134), `3381/1521` (89), `3381/1551` (2), `3381/1526` (1),
  `632111/1551` (1) = 227 dòng — tất cả là bút toán "Chênh lệch kiểm kê kho"
  (`KKT08.26.*`), Quantity9 **âm** (vd -1, -2, -80, -100...). Vì `C4.1` yêu
  cầu `Quantity9 > 0`, nhóm này **đã bị loại đúng** khỏi C4.1 — thiết kế hiện
  tại xử lý đúng trường hợp phổ biến nhất của bút toán đỏ.
- `6214/1521` (10) và `81188/1521` (5) = 15 dòng — bút toán "TĐ từ phiếu TP"
  (điều chỉnh chuyển từ phiếu thành phẩm), Quantity9 **dương** nhỏ (0,16–2,4)
  nhưng Amount âm. 15/15 dòng này đã có UnitCost=0 sẵn (nằm trong nhóm noise
  ở mục 6.3 dưới), nên dù có bỏ điều kiện `Amount<=0` khỏi C4.1, các dòng này
  vẫn bị flag vì `UnitCost<=0` — **loại bỏ điều kiện Amount<=0 không thay đổi
  số đếm** (30.502 → ~30.498, không đáng kể).

**Kết luận:** bút toán đỏ không phải nguyên nhân gây ồn cho C4.1 — nguyên
nhân thật là mục 6.3 dưới đây. Nhóm Quantity9 âm ("chênh lệch kiểm kê") đã
được gate `Quantity9 > 0` loại đúng từ trước; không cần sửa.

### 6.3. Danh sách cột số trong `app.js` — có thiếu cột nào không?

Đã lấy `cot` thật từ `lay_chi_tiet` cho toàn bộ 29 check trên file thật.
Toàn bộ cột số (numeric) từng xuất hiện: `Amount, net, ps_co, ps_no, so_dong,
thue_ra_33311, thue_vao_1331, tong`. **Tất cả đều đã có sẵn** trong tập hiện
tại `{Amount, ps_no, ps_co, net, tong, so_dong, thue_vao_1331, thue_ra_33311,
UnitCost, Quantity9}` — **không thiếu cột nào**.

Ngược lại: `UnitCost` và `Quantity9` trong danh sách **không bao giờ xuất
hiện thực tế** trong `cot` của bất kỳ check nào — `tao_ket_qua()` (base.py)
luôn cắt cột về `COT_CHUAN = [DocNo, DocDate, DebitAccount, CreditAccount,
Amount, Description, ly_do]`, nên giá trị số lượng/đơn giá của C4.1/C4.2 chỉ
được nhúng dạng text vào `ly_do`, không bao giờ là cột riêng. Hai mục này là
tử code vô hại (không gây lỗi hiển thị, chỉ là điều kiện `soCot.has(c)` không
bao giờ đúng với hai tên đó).

**Khuyến nghị (không sửa):** có thể dọn `UnitCost`, `Quantity9` khỏi tập
`soCot` trong `app.js` (dòng 135) vì chết code, nhưng đây không phải yêu cầu
bắt buộc và không ảnh hưởng số liệu — để controller quyết định.

---

## 7. Phát hiện thêm ngoài 3 mục được giao (2 check đỏ khả nghi cao)

Task cho phép/khuyến khích rà thêm bất kỳ check nào "flag quá nhiều". Ngoài
C4.1 (30.502, đã phân tích ở 7.2), hai check sau cũng có số đếm rất lớn và có
bằng chứng mạnh cho thấy phần lớn là false positive — nhưng tôi **không sửa**
vì việc sửa đòi hỏi thay đổi định nghĩa ngữ nghĩa của check (thêm điều kiện
loại trừ theo cột/khía cạnh khác), tức là một quyết định thiết kế, không phải
một điều chỉnh ngưỡng an toàn hiển nhiên.

### 7.1. C1.1 "Thiếu diễn giải" — vàng, 26.958/79.450 dòng (33,9%)

100% các dòng bị flag đều là chứng từ `DocCode = "HD"` (hoá đơn bán hàng):
- `131/511` (11.400 dòng): dòng công nợ/doanh thu của hoá đơn bán.
- `632/155` + `632/156` (11.388 dòng): dòng giá vốn tương ứng.
- `131/333` (4.157 dòng): dòng thuế GTGT đầu ra của hoá đơn.

Trong số 26.958 dòng "thiếu diễn giải", **22.801 dòng (84,6%) có cột
`ItemName` (tên mặt hàng) khác rỗng** — ví dụ "Trần nhựa nano P06 - 5.0kg",
"Keo dán đa năng V-500". Đây là mẫu hình rất phổ biến của ERP: dòng chi tiết
hoá đơn không lặp lại diễn giải tự do vì đã có tên mặt hàng riêng cột, "diễn
giải" theo nghĩa kế toán thực chất tồn tại — chỉ nằm ở cột khác. Chỉ có 4.157
dòng (toàn bộ là dòng thuế `131/333`, không có `ItemName`/`CustomerName` liên
quan) thực sự không có bất kỳ ngữ cảnh mô tả nào.

**Khuyến nghị (không sửa, để controller quyết):** nếu coi `ItemName` là một
dạng diễn giải hợp lệ, C1.1 nên đổi vế "trống" thành `Description trống AND
ItemName trống`, giảm số đếm từ 26.958 → ~4.157 (chỉ còn dòng thuế thật sự
không có mô tả gì). Đây là quyết định về "cái gì được coi là diễn giải hợp
lệ" — mang tính nghiệp vụ/kiểm toán, không phải bug thuần kỹ thuật, nên tôi
để nguyên và báo cáo.

### 7.2. C1.4 "TK Nợ = TK Có" — đỏ, 2.488/79.450 dòng (3,1%)

Phân theo `DocCode`: `DC` (điều chuyển kho, 2.298), `LR` (xử lý/điều chỉnh,
152), `BN` (chuyển tiền ngân hàng, 25), `BT` (13). **100% mẫu
kiểm tra là giao dịch nội bộ hợp lệ**, không phải lỗi:
- `DC` (điều chuyển kho): TK Nợ=Có=1521 hoặc 1561 (cùng TK kế toán vật tư)
  nhưng `WarehouseName` khác nhau rõ ràng giữa hai vế (vd "Kho HO - kho trung
  gian" → "Kho đi đường" → "Kho Hà Nội - Kho nguyên vật liệu") — điều chuyển
  vật tư/hàng hoá giữa các kho vật lý, TK GL giữ nguyên, phân biệt bằng
  `WarehouseCode`, không phải lỗi định khoản.
- `LR` (xử lý chênh lệch): diễn giải kiểu "XLR tôn lấy thêm tỉ trọng", "Đơn
  cxl trần nhựa..." — bút toán điều chỉnh nội bộ hợp lệ.
- `BN`/`BT` (chuyển tiền ngân hàng): diễn giải "Chuyển sang BIDV", "Chuyển
  sang ACB cty" — chuyển tiền giữa các tài khoản ngân hàng cùng dùng TK GL
  1121, phân biệt bằng `BankAccId`, không phải lỗi.

Không có dòng nào trong mẫu thuộc loại chứng từ "chung chung"/không rõ mục
đích mà lẽ ra phải là copy-paste nhầm TK.

**Khuyến nghị (không sửa, để controller quyết):** có 2 hướng khả dĩ —
(a) loại trừ `DocCode ∈ {DC, LR, BN, BT}` khỏi C1.4, hoặc (b) chỉ flag khi TK
Nợ=Có **và** cột phân biệt tương ứng (`WarehouseCode` cho TK kho,
`BankAccId`/`CashFlowId` cho TK tiền) cũng trùng nhau (tức thực sự không có
gì phân biệt hai vế). Hướng (b) chặt chẽ hơn nhưng phức tạp hơn về code. Vì
đây thay đổi định nghĩa "lỗi" thay vì chỉnh một ngưỡng số, tôi để nguyên và
báo cáo — đây gần như chắc chắn là false positive nhưng cách sửa cụ thể là
quyết định thiết kế nên xin controller chọn hướng.

**Lưu ý quan trọng cho headline:** vì C1.4 và (rất có thể) phần lớn C4.1 là
false-positive-nặng, verdict "san_sang: false, còn 4 việc" hiện tại có thể
đang phóng đại số việc thật cần làm — trên thực tế chỉ có C1.5 (243 dòng,
đáng xem lại) và C5.4 (1 dòng, 642 chưa kết chuyển hết ~19,7 triệu) là những
phát hiện "đỏ" chắc chắn cần accountant xử lý trước khi khóa sổ.

### 7.3. C4.1 "Xuất/nhập kho giá = 0" — đỏ, 30.502/79.450 dòng (38,4%) — chi tiết

Đây là check ồn nhất. Phân tích: các dòng flag tập trung gần như tuyệt đối ở
`621→152` (9.951/9.951 = 100%), `632→155` (9.038/9.053 = 99,8%), `632→156`
(8.166/8.182 = 99,8%), và các dòng chuyển kho nội bộ `152→152`/`156→156`
(1.679/1.836 và 650/665). Ở TẤT CẢ các dòng này, `UnitCost = 0` — trong khi
các dòng **nhập kho** (`Nợ 1521/Có 3311` — mua hàng) có `UnitCost` thực tế
hợp lý (17.350 – 95.061 đ/kg…).

Điều này cho thấy: trong file "Bảng kê chứng từ" này, Bravo **không** ghi đơn
giá trên từng dòng xuất kho — giá xuất kho (bình quân gia quyền cuối kỳ) là
một bước tính riêng, có thể (a) công ty *chưa chạy* bước "tính giá xuất kho
bình quân cuối kỳ 08/2026" tại thời điểm xuất file này, hoặc (b) báo cáo
"bảng kê chứng từ" theo thiết kế của Bravo **không bao giờ** xuất `UnitCost`
cho dòng xuất kho (giá được tính và lưu ở một bảng/báo cáo khác, không phản
ánh vào cột này của export này). Tôi không có cách nào phân biệt (a) và (b)
chỉ từ dữ liệu — đây chính là lý do brief liệt mục này là "judgement call".

**Khuyến nghị (không sửa, để controller quyết):** xác nhận với kế toán/IT
Bravo xem giá xuất kho bình quân của kỳ 08/2026 đã chạy chưa. Nếu (a) đúng —
đây là phát hiện thật, chính xác chức năng của C4.1 (nhắc kế toán chạy giá
thành trước khi khóa sổ) — giữ nguyên logic, có thể cân nhắc đổi mức độ hoặc
thông điệp để phản ánh "chưa chạy giá bình quân cuối kỳ" (một hành động, một
lần) thay vì liệt kê 30.502 dòng riêng lẻ như 30.502 lỗi độc lập. Nếu (b)
đúng — cột `UnitCost` không có ý nghĩa cho dòng xuất kho trong định dạng
export này, nên hạ mức độ (đỏ → vàng, hoặc bỏ điều kiện `UnitCost<=0` khỏi
C4.1 và chỉ giữ `Amount<=0`) vì check hiện tại không đo được điều nó tuyên bố
đo. Cả hai đều là quyết định cần thông tin nghiệp vụ tôi không có — để
nguyên.

---

## 8. Thay đổi mã nguồn thực tế trong task này

### 8.1. `app/web/app.js` — sửa hồi quy (bắt buộc, theo ruling 2)

Ba điểm gọi `moChiTiet(...)` xây `tieuDe` bằng `esc()` nhưng `tieuDe` chỉ
được dùng qua `$("chi-tiet-tieu-de").textContent` (không phải `innerHTML`).
Đã đổi sang nối chuỗi thô (không dùng `${...}` với các biến bị cấm theo test
`test_du_lieu_duoc_escape_truoc_khi_vao_innerhtml`, để tránh xuất hiện lại
các pattern `${b.buoc}`/`${c.ma}`/`${c.ten}` mà test cấm — dùng phép nối `+`
thay cho template literal cho các phần không escape):

```js
// truoc
li.onclick = () => moChiTiet(b.ma_check, `${esc(b.buoc)} — chứng minh (${b.ma_check})`);
...
chonThe(d); moChiTiet(c.ma, `${esc(c.ma)} · ${esc(c.ten)}${c.ghi_chu ? " — " + esc(c.ghi_chu) : ""}`);
...
d.onclick = () => { ... moChiTiet(c.ma, `${esc(c.ma)} · ${esc(c.ten)}`); };

// sau
li.onclick = () => moChiTiet(b.ma_check, b.buoc + ` — chứng minh (${b.ma_check})`);
...
chonThe(d); moChiTiet(c.ma, c.ma + " · " + c.ten + (c.ghi_chu ? " — " + c.ghi_chu : ""));
...
d.onclick = () => { ... moChiTiet(c.ma, c.ma + " · " + c.ten); };
```

`esc()` vẫn được giữ nguyên ở mọi điểm ghi vào `innerHTML` thật (Tab A, Tab B,
bảng chi tiết) — không đổi gì ở các chỗ đó.

### 8.2. `tests/test_e2e_file_that.py` — file mới, đúng theo brief.

### 8.3. Không có thay đổi nào khác trong `app/`.
Mọi phát hiện tinh chỉnh ở mục 6-7 đều được **báo cáo, không áp dụng**, vì
không có mục nào đạt tiêu chí "rõ ràng là false positive, sửa an toàn tuyệt
đối" mà không đụng đến định nghĩa nghiệp vụ của check (xem lý do chi tiết ở
từng mục).

---

## 9. TDD evidence

- `tests/test_e2e_file_that.py` được chạy thực tế trên file thật (không phải
  giả lập): `python -m pytest tests/test_e2e_file_that.py -q -s` → skip khi
  không có file thật (đã xác nhận logic skip đúng bằng cách đọc code, không
  cần xoá file để test vì file quá lớn/không nên đụng vào), pass khi có file
  (`PYTHONUTF8=1` cần thiết trên máy này do console cp1252 — không phải lỗi
  logic).
- Sửa `app.js` được xác minh bằng test hiện có
  `test_du_lieu_duoc_escape_truoc_khi_vao_innerhtml` (không cần viết test mới
  vì đây là bug hiển thị JS thuần, không có test harness JS trong repo — xác
  minh bằng cách đọc lại `app.js` sau sửa để bảo đảm không còn `esc(b.buoc)`,
  `esc(c.ma)`, `esc(c.ten)`, `esc(c.ghi_chu)` trong các lệnh gọi `moChiTiet`,
  và bảo đảm không xuất hiện lại các pattern `${b.buoc}`/`${c.ma}`/`${c.ten}`
  mà test tĩnh cấm — đã `grep` xác nhận không còn).
- Vì không sửa logic bất kỳ check nào, không cần thêm/sửa test đơn vị cho
  `app/checks/*`.

---

## 10. Kết quả full suite

```
PYTHONUTF8=1 python -m pytest -q -W error
........................................................................ [ 79%]
...................                                                      [100%]
91 passed in 26.02s
```

(90 test cũ + 1 test e2e mới = 91, tất cả pass, sạch dưới `-W error`.)

---

## 11. File đã thay đổi

- `app/web/app.js` — sửa (bỏ `esc()` sai chỗ khi build `tieuDe`, giữ nguyên
  mọi `esc()` ở sink `innerHTML` thật).
- `tests/test_e2e_file_that.py` — mới.
- Không đụng tới `1. Source/` hay `2. Report/` (đã kiểm tra `.gitignore` loại
  trừ sẵn hai thư mục này; test dùng `tmp_path`, không ghi vào `2. Report/`).

---

## 12. Quan ngại (concerns) cần controller quyết định

1. **C4.1 (30.502/79.450, đỏ)** — cực kỳ ồn, nguyên nhân gần chắc chắn là
   `UnitCost` không được Bravo ghi trên dòng xuất kho trong export này (khác
   với dòng nhập kho, luôn có giá). Cần xác nhận nghiệp vụ: đã chạy tính giá
   xuất kho bình quân cho kỳ 08/2026 chưa? Kết quả xác nhận sẽ quyết định có
   nên đổi mức độ/logic của C4.1 hay không.
2. **C1.4 (2.488/79.450, đỏ)** — bằng chứng rất mạnh (100% mẫu kiểm tra) cho
   thấy đây là điều chuyển kho/chuyển tiền ngân hàng hợp lệ, không phải lỗi
   định khoản. Đề xuất 2 hướng sửa cụ thể ở mục 7.2, chờ controller chọn.
3. **C1.1 (26.958/79.450, vàng)** — 84,6% có `ItemName` thay thế vai trò diễn
   giải; đề xuất đổi điều kiện thành `Description trống AND ItemName trống`
   (giảm còn ~4.157), chờ controller quyết định.
4. Do 1–3, **verdict "san_sang: false, còn 4 việc" trên dữ liệu thật có thể
   đang phóng đại số việc cần làm thật sự** — về bản chất chỉ có C1.5 (243
   dòng bút toán đỏ/0đ, đáng rà) và C5.4 (1 dòng, TK 642 còn dư ~19,7 triệu)
   là phát hiện "đỏ" chắc chắn không tranh cãi.
5. Thời gian `chay_kiem_tra` (9,1–9,7s) sát ngưỡng mục tiêu 10s của kế hoạch,
   gần như toàn bộ là thời gian đọc Excel bằng `calamine` — không phải logic
   check. Nếu cần margin an toàn hơn cho các file lớn hơn trong tương lai,
   hướng tối ưu là ở bước đọc file, không phải ở 29 check.
6. `UnitCost`, `Quantity9` trong tập cột số ở `app.js` (dòng 135) là tử code
   (không bao giờ khớp cột thật) — vô hại, có thể dọn nếu muốn, không bắt
   buộc.

Không có mục nào ở trên đủ nghiêm trọng để escalate BLOCKED — tool vẫn chạy
đúng, đủ, nhanh trên dữ liệu thật; các mục 1–3 là tinh chỉnh chất lượng có
thể làm ở một task/PR riêng sau khi controller quyết định hướng.
