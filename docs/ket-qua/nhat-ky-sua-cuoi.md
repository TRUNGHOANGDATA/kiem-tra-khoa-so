# Đợt sửa cuối — báo cáo

Nhánh `feat/tool-kiem-tra-khoa-so`, base `28df7df`.
Bốn commit: `1d7222f` (A), `46b6065` (B), `a7a247a` (C), `f462784` (D).
Suite: **91 → 168 test, xanh, sạch dưới `-W error`.**

---

## ⚠️ Việc cần người quyết trước khi bàn giao — A1

**Quy tắc phát hiện của A1 KHÔNG kích hoạt trên file thật 08/2026.**

Đề bài mô tả: *"there are stock rows with quantity, and **not one** of them carries a
positive `UnitCost`"*, kèm nhận định *"Every stock-issue line has UnitCost = 0 while
purchase lines carry real prices."* Đo trên chính file thật thì mệnh đề này sai:

| Nhóm dòng kho có số lượng | Số dòng | Có `UnitCost > 0` |
|---|---:|---:|
| Tất cả dòng kho có SL | 45.985 | **15.483** |
| Dòng **xuất** (Có TK kho) | 32.519 | **2.017** |
| Dòng **nhập** (Nợ TK kho) | 16.342 | 13.699 |

2.017 dòng xuất *có* đơn giá nằm rải trên đúng các TK (152/153/155/156) và đúng các loại
chứng từ (HD/PX/LR/DC) như 30.502 dòng không có đơn giá — không tách được thành một
nhóm riêng. Vì vậy `not one of them carries a positive UnitCost` = **False**, và:

- `GHI_CHU_CHUA_TINH_GIA` **không** được gắn vào C4.1 trên file thật;
- bước 5 vẫn ra `can_ra` "Còn 30502 dòng kho có số lượng nhưng giá = 0", **không phải**
  `chua_lam` "Chưa tính giá xuất kho bình quân cuối kỳ" như khách hàng mong đợi.

**Đã làm:** cài đúng quy tắc như đề bài, có test hai chiều. Code đúng với ca nó mô tả
(kỳ thật sự chưa chạy tính giá lần nào).
**Không làm:** tự đặt ngưỡng thay thế (ví dụ "≥ 90% dòng xuất không có đơn giá", hoặc chỉ
xét dòng xuất). Chọn ngưỡng là quyết định nghiệp vụ của khách hàng, không phải của đợt sửa
này — theo đúng chỉ dẫn "nếu một finding sai thì dừng và báo, đừng ép".

**Cần hỏi khách hàng:** 2.017 dòng xuất có đơn giá kia là gì? Nếu chúng là ngoại lệ hợp lệ
(hàng mua về bán thẳng, xuất theo giá đích danh…) thì quy tắc nên đổi thành "không dòng
xuất nào có đơn giá, bỏ qua N ngoại lệ" hoặc một ngưỡng tỉ lệ. Chỗ cần sửa khi đó chỉ là
biến `chua_tinh_gia` trong `app/checks/g4_kho_gia_von.py` — mọi thứ phía sau (ghi chú,
rẽ nhánh bước 5, test) đã sẵn sàng.

---

## Kết quả trên file thật sau đợt sửa

`1. Source/Bang ke chung tu 082027.xlsx` — 79.450 dòng, kỳ 08/2026.

### Ba check đổi số

| Check | Trước | Sau | Ghi chú |
|---|---:|---:|---|
| C1.1 Thiếu diễn giải | 26.958 | **4.157** | đúng bằng con số khách hàng dự kiến |
| C1.4 TK Nợ = TK Có | 2.488 | **0** | DC 2.298 · LR 152 · BN 25 · BT 13 — loại hết |
| C4.1 Xuất/nhập kho giá = 0 | 30.502 | **30.502** | giữ nguyên (xem cảnh báo A1) |

Phụ: C3.1 = 157, C3.2 = 68 sau khi gộp theo `(DocCode, DocNo)`.

### Kết luận headline mới

```
chua_san_sang | CHƯA SẴN SÀNG KHÓA SỔ — còn 3 việc phải xử lý
so_do=3  so_vang=8  so_chua_lam=0  so_can_ra=3  con_viec=3  san_sang=False
```

Còn **3 check đỏ** (trước là 4 — C1.4 rơi khỏi nhóm đỏ vì về 0):
C1.5 Số tiền ≤ 0 (243) · C4.1 Xuất/nhập kho giá = 0 (30.502) · C5.4 Thiếu kết chuyển chi phí → 911 (1).

Ba bước cần xử lý, **cả ba đều có bảng chứng minh** (`co_chung_cu=True`):
Tính giá xuất kho → C4.1 · Kết chuyển chi phí 635/641/642/811 → C5.4 · TK đầu 5/6/7/8 → C5.1.

Đáng chú ý: nếu khách hàng xử lý xong 3 lỗi đỏ, băng kết luận **không** nhảy sang xanh nữa
mà sang hổ phách "CÒN 11 MỤC CẦN RÀ SOÁT" (8 vàng + 3 cần rà) — đây chính là lỗi B4.

---

## Phần A — quyết định nghiệp vụ (`1d7222f`)

| Mục | Đã làm | Test |
|---|---|---|
| **A1** | `GHI_CHU_CHUA_TINH_GIA` trong `g4_kho_gia_von.py`; biến `chua_tinh_gia` = có dòng kho kèm SL **và** không dòng nào `UnitCost > 0`. Bước 5 đổi tên thành **"Tính giá xuất kho (mọi dòng xuất có đơn giá)"** (hằng `BUOC_TINH_GIA_XUAT_KHO`) và rẽ nhánh bằng cách **so sánh hằng số ghi chú**, không match chuỗi con. | `test_g4`: `test_c41_ghi_chu_chua_tinh_gia_khi_khong_dong_kho_nao_co_don_gia`, `test_c41_khong_ghi_chu_chua_tinh_gia_khi_co_dong_co_don_gia` · `test_trang_thai`: `test_chua_tinh_gia_xuat_kho_thi_chua_lam` |
| **A2** | `DOC_DIEU_CHUYEN = ("DC","LR","BN","BT")`; C1.4 loại trừ, nói rõ trong cả `ly_do` (mỗi dòng) lẫn `ghi_chu` (thẻ nhóm). Thêm luôn guard `notna()` đối xứng cho vế Có (được phép vì đang sửa đúng dòng đó). | `test_c14_loai_tru_chung_tu_dieu_chuyen`, `test_c14_bo_qua_khi_ca_hai_tk_deu_trong` |
| **A3** | C1.1 chỉ báo khi **cả** `Description` **và** `ItemName` trống. | `test_c11_item_name_duoc_tinh_la_dien_giai` |

**Hai test cũ phải sửa theo, đều là đổi hành vi có chủ đích:**
- `conftest.MAC_DINH["DocCode"]`: `"BT"` → `"PC"`. `BT` nay là loại chứng từ điều chuyển,
  để mặc định là `BT` thì mọi dòng test sẽ được C1.4 miễn trừ và test C1.4 cũ mất ý nghĩa.
- `test_xuat_kho_gia_va_tk_pl_ve_0`: fixture cũ chỉ có 1 dòng kho không đơn giá nên nay rơi
  vào ca A1 (`chua_lam`). Thêm một dòng nhập kho có đơn giá để nó tiếp tục kiểm nhánh `can_ra`.

---

## Phần B — bắt buộc sửa (`46b6065`)

### B1 — ngày dạng text suy sai kỳ ✅ (có điều chỉnh cách sửa)

Tái hiện đúng như mô tả: `["05/08/2026","12/08/2026","20/08/2026","31/08/2026"]` →
`[2026-05-08, 2026-12-08, NaT, NaT]`, `xac_dinh_ky` trả `(5, 2026)`, `nhat_ky` rỗng.

**`dayfirst=True` cho cả cột là không đủ và gây lỗi mới.** Trên pandas 3.0.2, cờ này áp cho
*cả* chuỗi bắt đầu bằng năm:

| Giá trị | `dayfirst=False` | `dayfirst=True` |
|---|---|---|
| `"05/08/2026"` | 2026-05-08 ❌ | 2026-08-05 ✅ |
| `"2026-08-05"` | 2026-08-05 ✅ | 2026-05-08 ❌ |
| `"2026-08-20"` | 2026-08-20 ✅ | **NaT** ❌ |

Test có sẵn `test_doc_bang_ke_tra_thong_tin` (fixture dùng `"2026-08-05"`) đỏ ngay — đổi một
lỗi im lặng lấy một lỗi im lặng khác. Đã thay bằng hàm `loader.doc_ngay()`: cột datetime thật
trả nguyên; chuỗi **bắt đầu bằng năm** vốn không nhập nhằng nên đọc thẳng; **chỉ phần còn lại**
mới bật `dayfirst`. Số ngày không đọc được nay được ghi vào `nhat_ky` giống hệt phép ép kiểu số.

Test: `test_ngay_dang_text_doc_theo_kieu_viet_nam` (khẳng định `(8, 2026)` như đề bài yêu cầu),
`test_ngay_dang_text_iso_khong_bi_dao_thang`, `test_doc_ngay_giu_nguyen_cot_datetime_that`,
`test_ngay_khong_doc_duoc_ghi_vao_nhat_ky`.

### B2 — `abs(net)` vs số dư có dấu ✅

`_ket_chuyen` dùng số dư **có dấu** và `NGUONG_CON_LAI` dùng chung (bỏ `0.5` viết cứng).
Chiều vượt nói *"Đã kết chuyển vượt 800 — phát sinh Có 621 lớn hơn phát sinh Nợ"* thay vì
*"còn net -800"*.

Vì C4.4/C5.2 **chỉ bắt chiều thiếu** (`ps_no - ps_co > ngưỡng`), ca vượt không thể có dòng
chứng minh. Thay vì để nó dẫn tới bảng trống, đã thêm trường `BuocKhoaSo.co_chung_cu`
(mặc định `True`, `False` ở đúng nhánh này). Front-end dùng nó để không gắn handler/mũi tên —
cùng cơ chế với C3. Đây cũng là "ngoại lệ khai báo tường minh" mà D1 yêu cầu.

Test: `test_ket_chuyen_vuot_noi_dung_dung_chieu`, `test_ket_chuyen_thieu_van_bao_so_duong_va_co_chung_cu`,
`test_ket_chuyen_trong_nguong_con_lai_thi_da_lam`.

### B3 — cầu nối không được ném ✅

`mo_file` / `mo_thu_muc` bọc try/except, trả `{"loi": ...}`. `app.js` bọc hai nút của toast
qua `baoLoi(await api.mo_file(...))`. Giữ nguyên chữ `api.mo_file(` để test tĩnh có sẵn còn
bắt được, và tránh truyền hàm không bound.

Test: `test_mo_file_tra_loi_khi_file_da_bi_xoa`, `test_mo_thu_muc_tra_loi_khi_duong_dan_khong_ton_tai`,
`test_moi_phuong_thuc_nhan_duong_dan_deu_tra_loi_thay_vi_nem`.

### B4 — kết luận ba mức ✅

Hàm dùng chung `trang_thai.tinh_ket_luan(ket_qua, trang_thai)` — `api.py` và `report.py` gọi
cùng một chỗ nên không thể lệch nhau. Trả `muc_do_ket_luan` ∈ {`chua_san_sang`, `can_ra_soat`,
`san_sang`}, `so_can_ra`, `cau_ket_luan`, và `con_viec` **đếm lại đúng theo câu đang hiển thị**.
`san_sang` vẫn là bool "không còn gì tồn đọng". `app.js` vẽ đủ ba trạng thái; `style.css` thêm
`.banner.can-ra-soat` (`#D97706` trên `--vang-nhat`).

Test: `tests/test_ket_luan.py` — ba fixture (sẵn sàng / cần rà soát / chưa sẵn sàng) khẳng định
câu kết luận ở **cả API lẫn báo cáo Excel**, cộng `test_api_va_bao_cao_luon_dong_y_nhau` và
`test_tk_toan_bo_de_trong_khong_duoc_bao_san_sang` (đúng ca file toàn TK trống mà reviewer nêu).

---

## Phần C — nên sửa (`a7a247a`)

| Mục | Đã làm | Test |
|---|---|---|
| **C1** | `g3._khoa_chung_tu()` gộp theo `(DocCode, DocNo)`. File thật: 16.385 DocNo / 16.411 cặp. | `test_c31_c32_gom_theo_ca_loai_va_so_chung_tu` (hai DocCode trùng số) |
| **C2** | Giữ `tieuDe` trong state `chiTiet` (cách được ưu tiên), bỏ hẳn regex tách DOM ở cả phân trang lẫn ô tìm kiếm. | `test_web_static` hiện có |
| **C3** | Bước `khong_ap_dung` (và bước `co_chung_cu=false`) không gắn handler, không hiện `›`; thêm `.buoc.khong-bam`. | `test_web_static` |
| **C4** | `base.TEN_COT` + `ten_cot()`; áp ở `report._ghi_bang` và truyền qua cầu nối (`nhan`, `cot_so`) cho JS. Cột bool → "Có"/"Không" ở cả hai nơi. | `test_tieu_de_cot_deu_la_tieng_viet` (quét **mọi sheet**), `test_moi_cot_cac_check_sinh_ra_deu_co_nhan_tieng_viet` (quét **cả 29 check**), `test_c65_bat_thuong_ghi_co_khong` |
| **C5** | Trang bìa dùng `fmt_so`. | `test_trang_bia_dung_dau_cham_kieu_viet_nam` |
| **C6** | `base.COT_SO_HIEN_THI` dùng chung; báo cáo hết sót `so_dong`. | `test_lay_chi_tiet_kem_nhan_tieng_viet_va_cot_so` |
| **C7** | Loader có thông báo riêng cho file rỗng; `g4._so()` ép `astype("string")`. | `test_doc_bang_ke_file_rong_bao_dung_nguyen_nhan`, `test_frame_rong_khong_lam_vo_g4` |
| **C8** | Bỏ assert tự-đúng (thay bằng `freeze_panes == "A6"`), xóa `_records`, C5.1 dùng `NGUONG_CON_LAI`. | `test_xuat_bao_cao_tao_du_sheet` |
| **C9** | Ghi chú C5.5 nói rõ điểm mù 911 ↔ 421 (chỉ kiểm tra sự tồn tại, cần số dư đầu kỳ mới bắt được sai số tiền). | — |

C7 đã tái hiện trước khi sửa: `chay_tat_ca` trên frame 0 dòng ném
`UFuncTypeError: ufunc 'add' did not contain a loop ... (dtype('<U6'), dtype('float64'))`.

---

## Phần D — test (`f462784`)

| Mục | Đã làm |
|---|---|
| **D1** | Gom toàn bộ kịch bản của `test_trang_thai.py` vào `KICH_BAN` (21 kịch bản, gồm `621_ket_chuyen_vuot`), test bất biến parametrise trên từng cái. Ngoại lệ duy nhất khai báo qua `co_chung_cu=False` + khẳng định `"vượt" in tom_tat` và bảng đúng bằng 0 dòng — không nới lỏng. Thêm `test_kich_ban_phu_du_bon_trang_thai` để bất biến không rỗng nghĩa. |
| **D2** | `tao_df([])` ra frame rỗng đúng kiểu; fixture `df_rong`, `df_tk_null`, `df_description_nan`; `tests/test_du_lieu_bien.py` chạy cả pipeline trên từng cái. |
| **D3** | 6 test loader mới (xem B1) + nhánh `ValueError` toàn NaT + dòng log ép kiểu số + cột mã float lẻ. |
| **D4** | `tests/test_nguong_bien.py` — 8 test, cặp biên tại **đúng** giá trị ngưỡng cho C4.2 (0,1%+1đ, cả ca số lớn), C2.4 (cả hai chiều dấu), C6.5 (`m + 2s`), C4.4 (`NGUONG_CON_LAI`). |
| **D5** | `test_sheet_nhat_ky_ghi_dung_canh_bao_cua_loader` + ca không có cảnh báo. |
| **D6** | `pytest.ini` thêm `filterwarnings = error`. |

### Kiểm chứng bằng mutation (đã chạy, đã khôi phục file)

| Mutation | Kết quả |
|---|---|
| Bỏ `co_chung_cu=False` ở nhánh kết chuyển vượt | **3/21 kịch bản đỏ** (`621_ket_chuyen_vuot`, `154_qua_632`, `154_qua_157`) |
| C4.2 `>` → `>=` | bị bắt |
| C2.4 `>` → `>=` | bị bắt |
| C6.5 `>` → `>=` | bị bắt |
| C4.4 `>` → `>=` | bị bắt |

Ghi chú: `154_qua_632` / `154_qua_157` cũng chạm nhánh "kết chuyển vượt" vì fixture chỉ có vế
`Có 621` mà không có `Nợ 621` (ps_no = 0, ps_co > 0). Là đặc thù fixture, nhưng xác nhận nhánh
này có thật và cờ `co_chung_cu` xử lý đúng.

---

## Lệnh đã chạy

```
python -m pytest -q                → 91 passed   (base, trước khi sửa)
python -m pytest -q                → 97 passed   (sau A)
python -m pytest -q                → 122 passed  (sau B)
python -m pytest -q                → 137 passed  (sau C)
python -m pytest -q                → 168 passed in 34.29s  (sau D, có filterwarnings=error)
python -W error -m pytest -q       → 168 passed in 32.74s
```

Không chạy GUI (`webview.start()` chặn luồng). Mọi kiểm chứng đều không tương tác; test ghi vào
`tmp_path`. Không `git add` bất kỳ thứ gì trong `1. Source/` hay `2. Report/` (cả hai đã nằm
trong `.gitignore`); có xuất một file báo cáo thật vào `2. Report/` để kiểm tra, không commit.

---

## Không thay đổi, và vì sao

**Theo ruling (giữ nguyên, không đụng):** lệch mức độ Tab A/Tab B · `lay_chi_tiet` stringify lại
mỗi lần tìm · tên class CSS `muc-do-` · `dropna=True` của `so_phat_sinh_tai_khoan` · `tao_ket_qua`
âm thầm bỏ cột. Guard `notna()` bất đối xứng của C1.4 **đã** thêm, vì A2 sửa đúng dòng đó.

**Phát hiện thêm, cố ý không sửa (ngoài phạm vi, báo để người chủ nhánh quyết):**

1. **`_ket_chuyen` khi `ps_no == 0` mà `ps_co > 0` và không có bút toán kết chuyển** → `chua_lam`
   trích dẫn C4.4, nhưng C4.4 đòi `ps_no > 0` nên bảng rỗng. Cùng lớp lỗi với B2 nhưng ở nhánh
   khác, và cần một dòng `Có 621` đối ứng TK không phải 154 mới xảy ra — rất bất thường về
   nghiệp vụ. Không có trong danh sách phải sửa nên không tự ý mở rộng; bất biến D1 sẽ bắt ngay
   nếu ai đó thêm kịch bản đó.
2. **Bước 11 trên frame rỗng ra `da_lam`** ("Mọi TK doanh thu/chi phí đã về 0" khi không có dòng
   nào). Đúng về mặt logic C5.1, hơi lạ về mặt câu chữ. Đã ghi nhận trong
   `test_frame_rong_khong_sinh_viec_phai_lam` thay vì đổi hành vi.
3. **A1 — xem cảnh báo ở đầu báo cáo.** Đây là mục duy nhất trong cả đợt không đạt được hiệu
   quả mong muốn trên file thật, và là mục duy nhất cần khách hàng trả lời thêm.

---

# Đợt bổ sung — theo ruling của điều phối (commit `f6b4a9a`)

Suite: **168 → 176 test, xanh, sạch dưới `-W error`.**

> Cảnh báo A1 ở đầu báo cáo này **đã được giải quyết** bằng quy tắc tỷ lệ dưới đây.
> Phần mô tả cũ giữ nguyên để lưu vết vì sao quy tắc "không một dòng nào" bị thay.

## A1 — quy tắc tỷ lệ thay cho all-or-nothing

```python
TY_LE_NGHI_CHUA_TINH_GIA = 0.8   # tỷ lệ dòng xuất kho không có đơn giá đủ để nghi chưa chạy tính giá
SO_DONG_XUAT_TOI_THIEU = 100     # dưới mức này tỷ lệ không nói lên điều gì
```

**Mẫu số là dòng XUẤT kho có số lượng (Có TK kho), không phải mọi dòng kho.** Con số ≈ 0,94
mà điều phối nêu ứng với mẫu số này; lấy mọi dòng kho có số lượng thì tỷ lệ chỉ còn 0,66 và
**không** vượt ngưỡng 0,8:

| Mẫu số | Chưa có đơn giá / tổng | Tỷ lệ | Kích hoạt? |
|---|---:|---:|---|
| **Chỉ dòng xuất có SL** (đang dùng) | 30.502 / 32.519 | **0,9380** | ✅ |
| Mọi dòng kho có SL | 30.502 / 45.985 | 0,6633 | ❌ |

Về nghiệp vụ mẫu số này cũng đúng hơn: dòng **nhập** luôn mang giá mua nên gộp vào chỉ pha
loãng tỷ lệ và che mất đúng thứ cần phát hiện. Cách diễn đạt cũng khớp: ghi chú và tóm tắt
bước 5 đều nói "dòng xuất kho".

Hai hàm mới trong `g4_kho_gia_von.py`, dùng chung cho cả check lẫn `trang_thai` nên định nghĩa
chỉ nằm một chỗ: `thong_ke_xuat_kho(df) -> (chưa có giá, tổng)` và `nghi_chua_tinh_gia(df)`.

Ghi chú mới (đã làm nhẹ đi đúng như ruling):
`"Nghi chưa chạy tính giá xuất kho bình quân cuối kỳ — phần lớn dòng xuất kho chưa có đơn giá"`

**Trên file thật:** tỷ lệ 30.502/32.519 = 0,9380 ≥ 0,8 → **kích hoạt**. C4.1 giữ mức đỏ và
giữ nguyên 30.502 dòng chi tiết để tra cứu, nhưng bước 5 nay đọc là **một việc**:

```
chua_lam | Tính giá xuất kho (mọi dòng xuất có đơn giá)
         | Chưa tính giá xuất kho bình quân cuối kỳ — 30502/32519 dòng xuất kho chưa có đơn giá
```

**Test:** `test_c41_ghi_chu_chua_tinh_gia_khi_ty_le_dat_nguong` (80/100 = đúng ngưỡng → kích
hoạt) · `test_c41_khong_ghi_chu_khi_ty_le_duoi_nguong` (79/100 → không) ·
`test_c41_it_dong_thi_khong_ket_luan_theo_ty_le` (99 dòng, tỷ lệ 100% → không) ·
`test_thong_ke_xuat_kho_chi_dem_dong_xuat` (500 dòng nhập không được làm loãng mẫu số) ·
`test_chua_tinh_gia_xuat_kho_thi_chua_lam` (90/100 → `CHUA_LAM`, câu tóm tắt đầy đủ) ·
`test_duoi_nguong_ty_le_thi_van_la_can_ra` (70/100 → rơi về `CAN_RA` như cũ).

## Hai mục lệch trạng thái ↔ chứng cứ — đã đóng

### Latent 1 — `ps_no == 0 < ps_co`

`_ket_chuyen` nay nhận tham số `chi_bat_ben_no`, bật cho ba bước trích dẫn **C4.4** (621/622/627)
vì check đó chỉ lập dòng khi `ps_no > 0`. Khi không có phát sinh Nợ mà vẫn có phát sinh Có:

```
can_ra | Không có phát sinh Nợ 621 nhưng có phát sinh Có 100 — bút toán bất thường, cần rà soát
       | co_chung_cu = False
```

Trước đây là `chua_lam` "chưa có bút toán kết chuyển" trỏ tới một bảng rỗng — vừa sai nghĩa
(không có gì để tập hợp) vừa dẫn vào ngõ cụt. Bước 632 **không** đổi: C5.2 có lập dòng cho ca
này (`ps_no <= 0 and ps_co <= 0` mới bỏ qua), nên `chua_lam` ở đó vẫn có chứng cứ.

Test: `test_chi_co_phat_sinh_ben_co_thi_khong_goi_la_chua_ket_chuyen`.

### Latent 2 — bước 11 trên frame không có TK 5/6/7/8

Thêm nhánh `not co_pl` → `KHONG_AP_DUNG` "Kỳ này không có phát sinh TK đầu 5/6/7/8", thay vì
`DA_LAM` "Mọi TK doanh thu/chi phí đã về 0" (khẳng định một việc chưa từng có gì để làm).
File rỗng nay cho **cả 11 bước** `khong_ap_dung`.

Test: `test_khong_co_tk_5678_thi_buoc_11_khong_ap_dung`,
`test_frame_rong_thi_ca_11_buoc_deu_khong_ap_dung`.

### D1 mở rộng

Thêm 4 kịch bản vào `KICH_BAN` (25 tổng): `chua_tinh_gia_xuat_kho` (90/100),
`sot_dong_xuat_chua_co_gia` (70/100), `621_chi_co_ben_co`, `khong_co_tk_pl`. Nhánh ngoại lệ
nay liệt kê **đúng hai** ca được phép bỏ bảng chứng minh (kết chuyển vượt · chỉ có bên Có),
và thông báo lỗi in ra `tom_tat` nếu xuất hiện ca thứ ba.

Mutation (đã chạy, đã khôi phục file) — cả ba nhánh mới đều bị bắt:

| Mutation | Kết quả |
|---|---|
| Bỏ `co_chung_cu=False` ở nhánh kết chuyển vượt | 2 test đỏ |
| Vô hiệu nhánh `chi_bat_ben_no` | 2 test đỏ |
| Vô hiệu nhánh "không có TK 5/6/7/8" ở bước 11 | 2 test đỏ |

## Headline mới trên file thật

```
chua_san_sang | CHƯA SẴN SÀNG KHÓA SỔ — còn 4 việc phải xử lý
so_do=3  so_vang=8  so_chua_lam=1  so_can_ra=2  con_viec=4  san_sang=False
```

So với trước đợt bổ sung (`còn 3 việc`, `so_chua_lam=0`, `so_can_ra=3`): bước tính giá xuất kho
chuyển từ `can_ra` sang `chua_lam`, nên đếm vào `con_viec` theo đúng ý khách hàng — một việc
phải làm trước khi khóa sổ, chứ không phải một mục rà soát.

Ba check đỏ giữ nguyên: C1.5 (243) · C4.1 (30.502) · C5.4 (1).
C1.1 = 4.157 · C1.4 = 0 · C4.1 = 30.502 (không đổi số dòng; đổi cách trình bày).

## Lệnh đã chạy (đợt bổ sung)

```
python -m pytest -q           → 176 passed in 34.52s
python -W error -m pytest -q  → 176 passed in 34.07s
```

Không chạy GUI. `doc_ngay()` của B1 giữ nguyên theo ruling.
