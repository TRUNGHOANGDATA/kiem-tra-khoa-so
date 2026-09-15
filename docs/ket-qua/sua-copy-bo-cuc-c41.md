# Sửa 3 việc khách gặp khi dùng thật: không copy được — nửa dưới cửa sổ bỏ trống — C4.1 còn 10 dòng oan

Nhánh `main`. Trước khi sửa: 186 test xanh dưới `-W error`. Sau khi sửa: **194 test xanh**
(thêm 8 test mới, cộng các khẳng định bổ sung vào test e2e sẵn có). File thật dùng để đo: `1. Source/Bang ke chung tu 082027.xlsx` (79.450 dòng, kỳ 08/2026),
chỉ đọc, không ghi.

---

## 1. Không copy được — nguyên nhân gốc

Lời khách: *"mở mấy cái xem thì không copy được dữ liệu. ví dụ như số CT để đi tra thực tế nhỉ?"*

### Nguyên nhân

Không nằm trong ba file web. `style.css` không có `user-select: none` nào, không có
`pointer-events`, không có lớp phủ, không có handler nào nuốt `mousedown`.

Thủ phạm là **pywebview**. `webview.create_window()` có tham số `text_select` **mặc định
`False`**, và khi đó `webview/js/customize.js` chạy lúc trang nạp xong:

```js
var disableText = '%(text_select)s' === 'False';
var disableTextCss = 'body {-webkit-user-select: none; -khtml-user-select: none; ' +
                     '-ms-user-select: none; user-select: none; cursor: default;}'
…
if (disableText) {
    var css = document.createElement("style");
    css.innerHTML = disableTextCss;
    document.head.appendChild(css);      // nối vào CUỐI <head>
}
```

(đã kiểm chứng trên bản đang cài: pywebview 6.2.1,
`…/site-packages/webview/js/customize.js` dòng 4–5 và 33–38; `webview/__init__.py`
dòng 333 `text_select: bool = False`.)

Thẻ `<style>` đó nối vào **cuối** `<head>`, tức là **sau** `style.css` của ứng dụng.
Ở cùng độ đặc trưng (`body`, 0-0-1) thì quy tắc đến sau thắng, nên không một dòng CSS
nào của chúng ta cãi lại được. Kết quả đúng như khách mô tả: bôi đen không ăn, `Ctrl+C`
không có gì để chép, và con trỏ trên bảng là mũi tên (`cursor: default`) chứ không phải
que chữ — chính cái làm người dùng nghĩ "bảng này chỉ để nhìn".

### Cách sửa

**`app/main.py`** — bật `text_select=True` khi tạo cửa sổ. Đây là nguyên nhân gốc và là
sửa chữa đủ.

**`app/web/style.css`** — thêm lớp phòng thủ thứ hai, phòng khi bản pywebview khác đổi
mặc định hoặc chèn lại:

```css
html body { -webkit-user-select: text; user-select: text; cursor: auto; }
```

`html body` có độ đặc trưng (0-0-2), thắng `body` (0-0-1) bất kể thứ tự. Đã kiểm chứng
trong trình duyệt: tiêm đúng chuỗi CSS của pywebview vào trang rồi đo lại,
`getComputedStyle(td).userSelect === "text"`.

Mặc định là **chọn được**; chỉ phần vỏ điều khiển (header, footer, tab, nút, thẻ bước,
thẻ nhóm, phân trang, chip trạng thái) mới tắt bôi đen, để kéo chuột lên nút không
quét trúng nhãn nút.

### Các lối chép đã thêm

Bôi đen trong bảng dày là việc khó, nên có thêm ba lối ngắn hơn:

| Lối | Thao tác | Kết quả |
|---|---|---|
| **Chép một ô** | Bấm vào ô | Đúng nội dung ô, ví dụ `PX2608-000366` |
| **Chép cả dòng** | Nút biểu tượng ở đầu mỗi dòng | 2 dòng TSV: tiêu đề cột + giá trị |
| **Chép cả trang** | Nút "Chép cả trang" ở đầu bảng | 101 dòng TSV (1 tiêu đề + 100 dòng) |
| **Bôi đen tự do** | Quét chuột rồi `Ctrl+C` | Cơ chế gốc của trình duyệt |

Chi tiết đáng lưu ý:

- **Bấm-để-chép không tranh chỗ với bôi đen.** Handler `click` bỏ qua nếu con trỏ dịch
  quá 4px giữa `mousedown` và `click` (tức là người dùng đang kéo để chọn), hoặc nếu
  `document.getSelection().isCollapsed === false` (đang có sẵn vùng bôi đen). Đã kiểm
  chứng: giả lập kéo 40px thì không phát toast nào.
- **Phản hồi không thể nhầm.** Toast ở `role="status" aria-live="polite"` đọc thành lời
  (`Đã chép “PX2608-000366”`) **và** ô/dòng vừa chép nháy nền xanh ~0,8s. Không bao giờ
  chỉ có màu làm tín hiệu.
- **Chép đúng cái đang nhìn thấy.** TSV dựng ngược từ DOM, nên số vẫn là `337.834` kiểu
  Việt Nam, ngày vẫn `01/08/2026`, `true/false` vẫn là `Có/Không` — dán vào Excel tiếng
  Việt ra đúng cột, đúng giá trị. Tab và xuống dòng lọt vào ô bị gộp thành dấu cách để
  không phá cấu trúc TSV.
- **`navigator.clipboard.writeText` trước, `document.execCommand('copy')` dự phòng.** Cả
  hai hỏng thì toast nói thẳng: *"Không chép được vào bộ nhớ tạm — hãy bôi đen bằng chuột
  rồi nhấn Ctrl+C"*. Im lặng là kiểu hỏng tệ nhất cho thao tác chép; đường này đã chạy
  thật trong lúc kiểm chứng (trang không có focus) và báo đúng.
- **Số CT không bị bẻ dòng nữa.** Giá trị ≤ 30 ký tự nhận `white-space: nowrap`; trước đó
  `PX2608-000366` bị xuống dòng thành `PX2608-` / `000366`, vừa khó đọc vừa khó quét
  trúng một mã.

### Bàn phím & trợ năng giữ nguyên

- Nút chép của mỗi dòng là `<button>` thật → vào được bằng `Tab`, có focus ring
  (`:focus-visible` toàn cục), có `aria-label="Chép cả dòng N"` vì chỉ có biểu tượng.
- Cột nút có `<th scope="col">` kèm nhãn `.an-chu` cho trình đọc màn hình.
- Nút "Chép cả trang" / "Danh sách" có chữ hiện + `title`.
- Bấm-vào-ô là lối tắt **chỉ dành cho chuột**; mọi dữ liệu nó chép đều lấy được bằng bàn
  phím qua nút chép dòng hoặc bôi đen + `Ctrl+C`.
- Không có gì truyền đạt bằng màu đơn độc.

---

## 2. Nửa dưới cửa sổ bị bỏ phí

### Đo trước khi sửa (Chromium, viewport đúng 1000×700, dữ liệu thật của C4.2)

| Chỉ số | Trước |
|---|---|
| `.vung-cuon` (vùng kết quả) | cao 380px nhưng `scrollHeight` **1.094px** — là một khung cuộn dài gần gấp ba |
| Vị trí bảng sau khi bấm một bước | `top = 975px` trên cửa sổ cao 700px → **nằm hẳn dưới mép dưới**, phải cuộn tay mới thấy |
| Khung bảng `.bang-cuon` | 252px cố định (`max-height: clamp(180px, 36vh, 420px)`) = **36% cửa sổ** |
| Chiều cao một dòng | 67px (diễn giải kẹp 3 dòng) |
| **Số dòng dữ liệu nhìn thấy** | **3** |
| `body.scrollWidth` | 1000 (= viewport, không tràn ngang) |

Đúng ảnh khách gửi: bảng là một khe ngang ba dòng, và phần lớn việc cuộn là để đi tìm nó.

### Đã sửa gì

- `body` vốn đã là cột flex cao trọn cửa sổ — giữ nguyên, ghi chú rõ lại.
- `.vung-cuon` **thôi làm khung cuộn**: `overflow: hidden`, là cột flex chiếm phần chiều
  cao còn lại. Mỗi khối con cuộn trong khung của chính nó.
- `.noi-dung` (danh sách 11 bước / lưới 6 thẻ nhóm): `flex: 1 1 auto; min-height: 0;
  overflow: auto` → lấp đầy vùng kết quả và cuộn tại chỗ khi chưa mở bảng.
- `.khung-chi-tiet`: `flex: 1 1 auto; min-height: 0` + là cột flex — đầu bảng và chân
  bảng cố định, `.bang-cuon` **bỏ `max-height`**, nhận `flex: 1 1 auto` và nở theo cửa sổ.
- Gợi ý cách chép đứng **cùng hàng** với phân trang (`.chi-tiet-chan`) thay vì chiếm một
  dòng riêng — lấy lại ~26px cho bảng.
- Diễn giải kẹp **2 dòng** thay vì 3 (chuỗi đầy đủ vẫn trong `title` và vẫn chép nguyên
  văn khi bấm ô) — dòng từ 67px xuống 49px.
- `scrollIntoView` bị bỏ: vùng kết quả không còn tự cuộn nên nó vô nghĩa.

### Quyết định khác đề bài — và lý do

Đề bài hình dung danh sách và bảng cùng hiện, bảng "nở ra ăn phần còn lại". **Ở 1000×700
điều đó không làm được**, và tôi đã đo để chắc chắn chứ không suy đoán:

Vùng kết quả chỉ cao **~380px** (header 67 + banner 92 + tab bar 41 + footer 58 + các
khoảng đệm/khe = 320px đã tiêu). Nếu chia đôi — danh sách ~34%, bảng phần còn lại — thì
panel chi tiết chỉ còn ~241px, trừ vỏ của nó (đầu bảng, chân bảng, viền, đệm ~100px) còn
**~140px bảng = 2 dòng**. Tức là để chữa một khe hẹp, ta tạo ra hai khe hẹp.

Nên: **khi bảng chi tiết mở, nó nhận trọn vùng kết quả và danh sách lui đi**
(`.vung-cuon.co-chi-tiet .noi-dung { display: none }`). Ngữ cảnh không mất:

- tiêu đề bảng ghi rõ đang xem bước/check nào (`Tập hợp CP NVL trực tiếp 621 → 154 —
  chứng minh (C4.4)`);
- banner kết luận và tab bar vẫn đứng nguyên;
- thêm nút **"Danh sách"** ở đầu bảng để quay lại ngay (đổi tab cũng quay lại, như cũ).

### Đo sau khi sửa (cùng viewport 1000×700, cùng dữ liệu)

| Chỉ số | Trước | Sau |
|---|---|---|
| Panel chi tiết | 362px, bắt đầu ở `top = 975` (ngoài màn hình) | **377px, `top = 245`** — hiện ngay, không cần cuộn |
| Khung bảng `.bang-cuon` | 252px (36% cửa sổ) | **267px (38,1% cửa sổ)** |
| Chiều cao một dòng | 67px | **49px** |
| **Số dòng nhìn thấy trọn vẹn** | **3** | **4** (+ dòng thứ 5 hiện một phần) |
| Vùng kết quả có phải khung cuộn dài không | có (1.094px / 380px) | **không** (`overflow: hidden`) |
| `body.scrollWidth` | 1000 | **1000** (= viewport, **không tràn ngang**) |
| `body.scrollHeight` | 700 | **700** (không có thanh cuộn cấp trang) |
| `.bang-cuon` `scrollWidth` vs `clientWidth` | — | **905 = 905** (bảng không tràn ngang ở cỡ này) |
| Footer | 638–686px | **637–686px**, ghim đáy như cũ |
| Banner / tab bar khi bảng cuộn | đứng yên | **đứng yên** |

Ở cửa sổ lớn hơn thì bảng lớn theo (trước đây bị chặn cứng ở 420px):

| Viewport | Khung bảng | Số dòng nhìn thấy | Tràn ngang |
|---|---|---|---|
| 1000×700 (tối thiểu) | 267px — 38,1% | 4 | không (1000/1000) |
| 1400×900 | **467px — 51,9%** | **8** | không (1400/1400) |

Các trạng thái khác đã kiểm: đóng bảng → danh sách lấp đầy 380px và cuộn tại chỗ
(717px nội dung); tab "Lỗi & cảnh báo" tương tự; mở bảng từ thẻ nhóm hoạt động; bảng
rỗng hiện "Không có dòng nào." và nút "Chép cả trang" tự tắt.

> Cách kiểm chứng không cần mở GUI: `.claude/launch.json` phục vụ `app/web` bằng
> `python -m http.server`, nạp `index.html` trong Chromium, giả lập `window.pywebview.api`
> bằng dữ liệu thật đã trích từ file 08/2026 rồi đo `getBoundingClientRect`. Không lần nào
> gọi `webview.start()`.

---

## 3. C4.1 — 10 dòng cuối cũng là báo oan

### Vấn đề

C4.1 bắt dòng kho có số lượng mà `Amount <= 0`. Trên sổ 08/2026 nó còn báo đúng 10 dòng,
và **cả 10 đều mang số tiền ÂM, không dòng nào bằng 0**:

```
-41.722  -34.439  -22.003  -20.079  -13.758  -11.474  -5.737  -4.638  -4.638  -2.748
```

Cả 10 cùng một hình dạng: `DocCode = PX`, `Nợ 6214 / Có 1521`, diễn giải
`"TĐ từ phiếu TP số: TP2608-…"` — bút toán điều chỉnh/đảo chiều đối ứng một phiếu thành
phẩm. Số lượng đều lẻ: `0,16 · 0,27 · 0,27 · 0,334 · 0,668 · 0,801 · 1,169 · 1,281 ·
2,005 · 2,429`.

**Số tiền âm là MỘT GIÁ TRỊ**, không phải thiếu giá trị. Câu check tự nói ra
("chưa xác định giá trị") sai với từng dòng một trong 10 dòng đó.

### Đã sửa

- `gia_0 = co_sl & (df["Amount"] == 0)` — đúng bằng 0 mới là "chưa gán giá trị".
- `thong_ke_xuat_kho()` dùng **cùng vị từ** (`Amount == 0`). Nếu để lệch, quy tắc tỷ lệ
  hệ thống sẽ đếm những dòng mà bảng chứng minh của C4.1 không còn liệt kê.
- Số tiền âm **không mất khỏi báo cáo**: C1.5 "Số tiền ≤ 0" vẫn liệt kê đủ **243 dòng**
  như vậy của cả file để rà soát — đã khẳng định trong test e2e.

### Số lượng lẻ in ra không còn nói dối

`fmt_so` làm tròn 0 chữ số thập phân, nên `fmt_so(0.16)` ra `"SL 0"` — đọc thành *"không
có số lượng"*, đúng **ngược** điều kiện đang báo ("có số lượng nhưng chưa có giá trị").

Thêm `app/checks/base.fmt_sl()`: in đủ 9 chữ số thập phân (đúng độ rộng cột `Quantity9`
của Bravo) rồi cắt số 0 thừa, ngăn cách kiểu Việt Nam.

| Vào | `fmt_so` (cũ) | `fmt_sl` (mới) |
|---|---|---|
| `0.16` | `0` | `0,16` |
| `2.429` | `2` | `2,429` |
| `10` | `10` | `10` |
| `1234.5` | `1.234` | `1.234,5` |

Áp cho `Quantity9` ở lý do của **C4.1 và C4.2** — cùng một cột, cùng một lời nói sai. Trên
file thật lý do C4.2 nay đọc là `SL 11,36 × đơn giá 29.630 = 336.596 nhưng Amount ghi
337.834 …` (trước là `SL 11 × …`, một phép nhân không khớp trên màn hình).

### Kết quả trên file thật

| | Trước | Sau |
|---|---|---|
| C4.1 số dòng | 10 | **0** |
| C4.1 `ghi_chu` | `""` | `""` |
| Quy tắc tỷ lệ hệ thống `nghi_chua_tinh_gia` | `False` | **`False`** (0/32.519 = 0,0 — xa ngưỡng 0,8) |
| Bước "Tính giá xuất kho" | `can_ra` — "Còn 10 dòng kho…" | **`da_lam`** — "46.522 dòng kho, không dòng nào chưa có giá trị" |
| C1.5 "Số tiền ≤ 0" | 243 | **243** (không đổi — các dòng âm vẫn được rà) |

Băng kết luận:

```
muc_do_ket_luan = chua_san_sang
so_do = 2 · so_vang = 8 · so_chua_lam = 0 · so_can_ra = 2 · con_viec = 2
"CHƯA SẴN SÀNG KHÓA SỔ — còn 2 việc phải xử lý"
```

(trước: `con_viec = 3`, vì `so_chua_lam` hoặc `so_can_ra` còn tính thêm bước tính giá.)

---

## 4. Test

Từ 186 → **194** xanh dưới `-W error` (8 hàm test mới + mở rộng test e2e sẵn có).

Không có test nào bị nới lỏng. Không có test nào trước đây ghim `Amount <= 0` với số tiền
âm (mọi kịch bản "chưa có giá trị" trong suite đều dùng `Amount = 0`), nên không phải sửa
test cũ — chỉ bổ sung:

**`tests/test_g4_kho_gia_von.py`**
- `test_c41_tien_am_la_gia_tri_khong_phai_thieu_gia_tri` — cặp đối xứng: dòng kho có số
  lượng + **tiền âm** → **không** bị bắt; **cùng dòng đó với tiền 0** → **bị bắt**.
  Đổi `==` về `<=` là test đỏ.
- `test_c41_ly_do_giu_so_luong_le` — lý do phải bắt đầu bằng `Có SL 0,16 nhưng tiền = 0`.
- `test_nghi_chua_tinh_gia_khong_bao_tren_dong_dieu_chinh_am` — 200 dòng xuất toàn tiền âm
  không được kết luận "cả kỳ chưa chạy tính giá"; `thong_ke_xuat_kho == (0, 200)`.

**`tests/test_base.py`**
- `test_fmt_sl_giu_phan_thap_phan` — `0,16 / 2,429 / 0,334 / 10 / 0 / 1.234,5 / -0,27 / NaN`.

**`tests/test_web_static.py`**
- `test_main_bat_text_select` — `app/main.py` phải có `text_select=True` (bỏ đi là tái
  phát đúng lỗi khách báo).
- `test_css_khong_khoa_boi_den_bang` — phải có `html body … user-select: text`, và không
  được có quy tắc tắt bôi đen toàn trang.
- `test_app_js_co_du_ba_loi_chep_va_duong_lui` — có `navigator.clipboard.writeText`,
  `document.execCommand("copy")`, thông báo khi cả hai hỏng, nút chép trang, nút chép dòng,
  nhãn cho nút chỉ có biểu tượng, TSV, và chốt bảo vệ bôi đen (`isCollapsed` + `mousedown`).
- `test_bo_cuc_man_hinh_2_lap_day_cua_so` — không còn `clamp(180px, 36vh, 420px)`, có
  `.vung-cuon.co-chi-tiet .noi-dung`, và không còn `scrollIntoView`.
- `test_index_tham_chieu_file_local_va_du_id` — thêm 3 id mới vào danh mục bắt buộc
  (`vung-cuon`, `btn-chep-trang`, `btn-dong-chi-tiet`).

**`tests/test_e2e_file_that.py`** — mở rộng test có sẵn (không đọc thêm file lần nữa):
C4.1 = 0 dòng và `ghi_chu` rỗng; C1.5 = 243; bước "Tính giá xuất kho" = `da_lam`;
`con_viec == 2` và `so_chua_lam == 0`.

Các bất biến cũ vẫn giữ nguyên hiệu lực: mọi `$("id")` trong `app.js` tồn tại trong
`index.html`; mọi chuỗi từ backend/Excel đi qua `esc()` trước khi vào `innerHTML` (phần
markup mới không nhúng dữ liệu backend vào `innerHTML` — `aria-label` chỉ mang số thứ tự
dòng do JS sinh); không URL ngoài; Segoe UI; không có nhánh chế độ tối.

---

## 5. Đề xuất nhưng chưa làm

1. **`UnitCost` trong lý do C4.2 vẫn làm tròn 0 chữ số thập phân.** Cùng hạng lỗi với
   `Quantity9` vừa sửa: đơn giá lẻ sẽ in ra thành số nguyên và phép nhân trên màn hình
   không khớp. Chưa đổi vì đề bài khoanh vùng ở số lượng, và đơn giá VND phần lớn là số
   nguyên. Đổi `_so` → `_sl` cho `UnitCost` là một từ.
2. **Chép ở dạng số thô (không định dạng).** Hiện chép đúng cái đang nhìn thấy
   (`337.834`), dán vào Excel **tiếng Việt** ra số đúng. Nếu khách có máy chạy Excel
   locale Anh, nên thêm tuỳ chọn "chép số thô". Cần hỏi khách trước.
3. **`Ctrl+A` trong bảng / chép nhiều trang.** Hiện chỉ chép được trang đang xem (tối đa
   100 dòng). Với check 6.735 dòng, người dùng vẫn phải dùng "Xuất báo cáo Excel". Có thể
   thêm "Chép tất cả kết quả" gọi thẳng `lay_chi_tiet` với `kich_thuoc` lớn — nhưng nút
   "Xuất báo cáo Excel" đã phục vụ đúng nhu cầu đó tốt hơn.
4. **Bảng dài 100 dòng dựng bằng `innerHTML` một lần** — thêm 100 `<button>` chép dòng làm
   tab order dài ra. Nếu thấy vướng khi dùng bàn phím, có thể gom nút chép dòng vào một
   `menu` theo dòng hoặc dùng `tabindex="-1"` + phím tắt. Chưa làm vì chưa có bằng chứng
   là vướng thật.
5. **Banner kết luận cao 92px** — ở 1000×700 nó chiếm 13% chiều cao. Thu gọn banner khi
   bảng chi tiết đang mở sẽ lấy thêm ~30px (≈ nửa dòng dữ liệu). Chưa làm vì banner là
   câu trả lời chính của công cụ, không nên co lại lúc người dùng đang xem lỗi.
