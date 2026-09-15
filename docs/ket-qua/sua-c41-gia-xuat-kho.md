# Sửa C4.1 — "Xuất/nhập kho giá = 0" khóa nhầm cột

Ngày: 2026-09-15. File thật dùng để kiểm chứng: `1. Source/Bang ke chung tu 082027.xlsx`
(79.450 dòng, kỳ 08/2026).

---

## 1. Chẩn đoán

C4.1 khóa vào **cột sai**. Điều kiện cũ:

```python
gia_0 = co_sl & ((df["UnitCost"] <= 0) | (df["Amount"] <= 0))
```

flag một dòng kho có `Quantity9 > 0` khi `UnitCost <= 0` **HOẶC** `Amount <= 0`. Trên file
thật điều đó bắt 30.502 dòng. Đo trực tiếp 30.502 dòng đó:

- **30.492 dòng (100,0%) có `Amount > 0`** — giá vốn xuất kho ĐÃ được xác định. Đơn giá suy
  ra (`Amount / Quantity9`) nằm trong khoảng 30 – 15.647.500, trung vị 26.400 — hoàn toàn hợp
  lý về mặt giá trị.
- Chỉ **10 dòng** thật sự không có giá trị gì (`Amount <= 0`), toàn bộ là `DocCode = "PX"`,
  Nợ 6214 / Có 1521 (xuất NVL cho sản xuất).

**Nguyên nhân gốc:** Bravo không ghi đơn giá (`UnitCost`) trên dòng xuất kho — giá vốn bình
quân gia quyền cuối kỳ được tính và ghi thẳng vào `Amount`, không "trả ngược" thành đơn
giá/dòng. `UnitCost = 0` trên một dòng xuất là bình thường, không có ý nghĩa gì; `Amount` mới
là cột trả lời câu hỏi "giá xuất kho đã được xác định hay chưa". C4.1 (và phần dùng chung của
nó trong `trang_thai.py`) đo nhầm cột nên tạo ra 30.492 false positive.

Văn bản hiển thị cho người dùng còn tự mâu thuẫn: một dòng bị gắn cờ hiển thị
*"Số tiền 1.466.848 · Lý do: có SL 60, đơn giá 0, tiền 1.466.848 — có số lượng nhưng đơn giá
hoặc tiền = 0"* — khẳng định "tiền = 0" ngay cạnh một số tiền khác 0.

---

## 2. Thay đổi mã nguồn

### 2.1. `app/checks/g4_kho_gia_von.py`

- **C4.1** đổi tên thành **"Xuất/nhập kho chưa có giá trị"**, điều kiện còn lại chỉ
  `Amount <= 0` (bỏ hẳn `UnitCost <= 0`):
  ```python
  gia_0 = co_sl & (df["Amount"] <= 0)
  ```
  `ly_do` viết lại để không còn nhắc "đơn giá" và không còn khẳng định sai:
  ```
  Có SL {sl} nhưng tiền = {amount} — có số lượng nhưng chưa xác định giá trị
  (chưa tính giá xuất kho)
  ```
  Cả hai số trong câu (SL, tiền) đều đúng với cột bên cạnh — không còn khẳng định "tiền = 0"
  khi tiền thực chất khác 0.

- **`thong_ke_xuat_kho()`** (nền tảng cho tỷ lệ nghi ngờ "chưa chạy tính giá bình quân") đổi
  từ đếm `UnitCost <= 0` sang đếm `Amount <= 0`, cùng logic với C4.1. `GHI_CHU_CHUA_TINH_GIA`
  đổi chữ "chưa có đơn giá" → "chưa có giá trị" cho khớp predicate mới.
  `TY_LE_NGHI_CHUA_TINH_GIA` (0,8) và `SO_DONG_XUAT_TOI_THIEU` (100) giữ nguyên như yêu cầu.

- **C4.2** ("Tiền ≠ Số lượng × Đơn giá") — **không đổi logic** (vẫn gate trên
  `UnitCost > 0`, đúng như tên: đối chiếu công thức trên các dòng có đơn giá). Vì cột này giờ
  đã biết là chỉ tồn tại trên thiểu số dòng kho, đổi tên thành
  **"Tiền ≠ Số lượng × Đơn giá (chỉ dòng có đơn giá > 0)"** để không bị hiểu nhầm là đã đối
  chiếu toàn bộ dòng kho.

### 2.2. `app/trang_thai.py` (bước 5 trong Tab A)

- `BUOC_TINH_GIA_XUAT_KHO`: `"Tính giá xuất kho (mọi dòng xuất có đơn giá)"` →
  `"Tính giá xuất kho (mọi dòng xuất có giá trị)"`.
- Nhánh `CHUA_LAM` (nghi cả kỳ chưa chạy tính giá): "chưa có đơn giá" → "chưa có giá trị".
- Nhánh `DA_LAM`: "không dòng giá = 0" → "không dòng nào chưa có giá trị".
- Nhánh `CAN_RA`: "có số lượng nhưng giá = 0" → "chưa có giá trị (Amount = 0)" — nói rõ cột
  nào bằng 0, tránh mơ hồ giữa "giá" (đơn giá) và "giá trị" (thành tiền).

### 2.3. Không đổi

`GHI_CHU_THIEU_SL` (chỉ dựa trên `Quantity9`, không dựa `UnitCost`) — vẫn hoạt động đúng, không
đụng tới theo yêu cầu.

---

## 3. Trước / sau trên file thật

| | Trước | Sau |
|---|---:|---:|
| C4.1 số dòng lỗi | 30.502 | **10** |
| C4.1 ghi chú hệ thống ("nghi chưa chạy tính giá") | không kích hoạt | không kích hoạt |
| Bước 5 (Tab A) | `can_ra` — "Còn 30.502 dòng kho có số lượng nhưng giá = 0" | `can_ra` — "Còn 10 dòng kho có số lượng nhưng chưa có giá trị (Amount = 0)" |
| C4.2 (không đổi logic) | 397 dòng, tên cũ | 397 dòng, tên mới "...(chỉ dòng có đơn giá > 0)" |

Ratio nền cho ghi chú hệ thống (`thong_ke_xuat_kho`, rebase trên `Amount`): trên file thật chỉ
còn 10 / khoảng 32.500 dòng xuất kho có SL chưa có giá trị ⇒ tỷ lệ ≈ 0,0003, xa dưới ngưỡng
0,8 ⇒ đúng như dự đoán, không kích hoạt `GHI_CHU_CHUA_TINH_GIA`.

### Headline mới (chạy qua `JsApi.chay_kiem_tra()`, không mở GUI)

```
so_do = 3
so_vang = 8
so_chua_lam = 0
so_can_ra = 3
con_viec = 3
muc_do_ket_luan = "chua_san_sang"
cau_ket_luan = "CHƯA SẴN SÀNG KHÓA SỔ — còn 3 việc phải xử lý"
```

Ba check đỏ còn lại: C1.5 (Số tiền ≤ 0, 243 dòng), C4.1 (10 dòng), C5.4 (Thiếu kết chuyển chi
phí → 911, 1 dòng) — không đổi so với trước khi sửa, vì C1.1/C1.4 đã được xử lý ở một đợt sửa
trước đó (`docs/ket-qua/nhat-ky-sua-cuoi.md`) và C4.1 vẫn còn 10 dòng lỗi thật (vẫn đỏ, chỉ
giảm số lượng). Điểm khác biệt duy nhất so với trước task này: C4.1 từ 30.502 dòng noise xuống
còn đúng 10 dòng thật, và văn bản/tên bước 5 không còn tự mâu thuẫn.

---

## 4. Rà các chỗ khác còn khóa vào `UnitCost`

Tìm toàn bộ `UnitCost` trong repo (`app/`, `tests/`, `docs/`):

- `app/checks/g4_kho_gia_von.py` — C4.2 (giữ nguyên logic, chỉ đổi tên, xem mục 2.1).
- `app/trang_thai.py` — chỉ import hằng số/hàm từ `g4_kho_gia_von`, không tự đọc `UnitCost`.
- `app/loader.py` — `COT_SO = [..., "UnitCost"]`: chỉ là danh sách cột được ép kiểu số khi đọc
  Excel (`pd.to_numeric`), không phải logic nghiệp vụ — không cần đổi.
- `tests/conftest.py`, `tests/test_g4_kho_gia_von.py`, `tests/test_nguong_bien.py`,
  `tests/test_loader.py` — dữ liệu test, đã cập nhật/không cần đổi (xem mục 5).
- `app/web/app.js` (dòng ~135): tham chiếu `UnitCost`/`Quantity9` trong tập cột số hiển thị
  (`COT_SO_HIEN_THI` ở `base.py`) là tử code — `tao_ket_qua()` luôn cắt cột chi tiết về
  `COT_CHUAN` (không có `UnitCost`/`Quantity9`), nên hai tên này không bao giờ khớp cột thật.
  Đã có từ trước, không phải do defect này gây ra, không đụng tới (ngoài phạm vi yêu cầu).

**Kết luận:** không còn chỗ nào khác trong logic nghiệp vụ khóa vào `UnitCost` theo cách bị
defect này làm sai lệch. C4.2 là chỗ duy nhất còn dùng `UnitCost`, và nó dùng đúng — chỉ thiếu
minh bạch về phạm vi (đã sửa bằng cách đổi tên).

---

## 5. Test

`tests/test_g4_kho_gia_von.py`:
- `test_c41_khong_bao_khi_unitcost_0_nhung_amount_duong` (mới) — dòng `Quantity9=60,
  UnitCost=0, Amount=1.466.848` (đúng hình dạng dòng gây khiếu nại của khách hàng) **không**
  bị C4.1 bắt.
- `test_c41_bao_khi_amount_0_du_unitcost_0` (mới) — cùng dòng nhưng `Amount=0` **phải** bị bắt.
- `test_nghi_chua_tinh_gia_khong_bao_khi_co_gia_tri_du_khong_co_don_gia` (mới) — 200 dòng xuất
  đều `UnitCost=0` nhưng `Amount=264.000` (>0): `thong_ke_xuat_kho` trả `(0, 200)`,
  `nghi_chua_tinh_gia` là `False`, C4.1 sạch — tỷ lệ rebase không kích hoạt khi giá trị đã có.
- Các test C4.1 cũ (`test_c41_xuat_kho_gia_0`, các test tỷ lệ `dong_xuat(...)`) đã tương thích
  sẵn với predicate mới (dựng dữ liệu với `Amount` và `UnitCost` cùng 0/cùng khác 0), không
  cần sửa logic — chỉ số liệu, không đổi.

`tests/test_trang_thai.py`:
- `test_chua_tinh_gia_xuat_kho_thi_chua_lam` — cập nhật chuỗi mong đợi "chưa có đơn giá" →
  "chưa có giá trị".
- Kịch bản mới `xuat_kho_amount_du_khong_don_gia` trong `KICH_BAN` (100 dòng `UnitCost=0`,
  `Amount=264.000`) + test mới `test_amount_du_khong_don_gia_thi_da_lam` — hồi quy đúng lỗi
  gốc ở tầng bước-khóa-sổ: toàn bộ dòng xuất không có đơn giá nhưng có giá trị thật phải ra
  `da_lam`, không phải `chua_lam`.

Kết quả: **181 test** (176 cũ + 5 mới), xanh, sạch dưới `-W error`:
```
PYTHONUTF8=1 python -m pytest -q -W error
........................................................................ [ 39%]
........................................................................ [ 79%]
.....................................                                    [100%]
181 passed
```

---

## 6. Khuyến nghị không thực hiện trong task này

- `app/web/app.js` dòng ~135 (`soCot`/`COT_SO_HIEN_THI` chứa `UnitCost`, `Quantity9` chết
  code) — vô hại, có thể dọn ở một task riêng, ngoài phạm vi defect này.
- 10 dòng C4.1 còn lại (PX, Nợ 6214/Có 1521) là phát hiện thật — cần kế toán xác nhận đây có
  phải phiếu xuất bị bỏ sót khỏi lần chạy giá bình quân cuối kỳ hay không; không phải lỗi
  phần mềm, không sửa thêm.
