# Thiết kế lại giao diện — Swiss/Minimal, light mode

Ngày: 2026-09-15. Phạm vi: chỉ ba file `app/web/index.html`, `app/web/style.css`,
`app/web/app.js`. **Không sửa một dòng Python nào** — hợp đồng cầu nối
(`lay_file_moi_nhat`, `chon_file`, `nap_file`, `chay_kiem_tra`, `lay_chi_tiet`,
`xuat_bao_cao`, `mo_file`, `mo_thu_muc`, `window.onTienTrinh(ten, phan_tram)`) giữ nguyên.

File thật dùng để dựng mẫu và soi giao diện: `1. Source/Bang ke chung tu 082027.xlsx`
(79.450 dòng, kỳ 08/2026, tổng phát sinh 836.867.804.478).

---

## 1. Lỗi đã sửa: thanh tiến trình không nhúc nhích

### Nguyên nhân thật

`JsApi._nap_file()` phát tiến trình **0%** ngay trước `doc_bang_ke(path)` rồi **85%**
ngay sau. Giữa hai mốc đó là ~8,4 giây pandas đọc Excel — Python chặn luồng, không một
lệnh `evaluate_js` nào tới được trình duyệt. Mọi thanh chạy theo phần trăm **bắt buộc**
đứng im ở giá trị JS đặt trước khi `await`. Đó đúng là hiện tượng khách báo, và không có
cách nào chữa bằng cách gọi callback dày hơn: callback không đi qua được.

### Cách sửa

Một khung tiến trình, hai chế độ, chuyển chế độ theo `pct` mà Python gửi:

| Pha | Ai sinh chuyển động | Chế độ | Chữ hiển thị |
|---|---|---|---|
| Đọc Excel (~8,4s, Python chặn luồng) | **Trình duyệt** — `@keyframes chay-ngang` dịch một vệt sáng rộng 38% máng bằng `translateX`, 1,15s/lượt, lặp vô hạn | `.tien-trinh-nen.khong-xac-dinh` | "Đang đọc file…" + "Đang xử lý…" |
| Chạy 29 check (~0,7s, callback tới thật) | Python — `on_progress` của `chay_tat_ca` (0/16/33/50/66/83/100) | thanh phần trăm, `transform: scaleX(pct/100)` | "Đang kiểm tra: Kho & giá vốn…" + "50%" |

Quy tắc trong `datTienTrinh(nhan, pct)`:

- `pct` không phải số dương → chế độ **không xác định**. JS tự bật chế độ này **trước
  khi** `await` bất kỳ lời gọi cầu nối nào có thể chặn (`taiFile()`, `chayKiemTra()`), nên
  thanh đã chạy sẵn lúc Python còn chưa kịp nói gì.
- `pct > 0` → chế độ **xác định**: `aria-valuenow` thật, chữ "NN%".

Hai chi tiết cố ý:

- Thanh xác định phóng bằng `transform: scaleX()`, **không animate `width`/`height`** —
  đúng yêu cầu và cũng là đường compositor-only.
- `_nap_file` gửi `("Đã đọc N dòng", 85)` ngay khi đọc xong, nên lúc đó thanh tự nhảy
  sang chế độ xác định ở 85% — trung thực: phần chờ lâu nhất đã qua.

### `prefers-reduced-motion: reduce`

Vệt sáng chạy ngang bị thay bằng **một dải sọc chéo tĩnh phủ kín máng**
(`repeating-linear-gradient(135deg, var(--chinh-hover) 0 8px, var(--chinh) 8px 16px)`,
`width: 100%`, `transform: none`) kèm **nhịp mờ/rõ chậm 2,4s chỉ trên `opacity`**
(1 → .55 → 1). Không có chuyển động ngang, không có dịch chuyển vị trí — đây là kiểu
thay đổi không gây khó chịu tiền đình. **Không để im hoàn toàn**, và cũng không bao giờ
chỉ dựa vào chuyển động: `#tien-trinh-ten` nói pha đang chạy, `#tien-trinh-pct` nói
"Đang xử lý…" hoặc "NN%", `role="progressbar"` + `aria-busy="true"` +
`aria-valuetext="Đang xử lý, chưa đo được tiến độ"` nói với trình đọc màn hình. Cùng
media query, mọi `transition-duration` bị rút về 0,01ms.

---

## 2. Token màu

Khai báo **một lần duy nhất** ở `:root`; không một mã màu thô nào xuất hiện trong quy
tắc thành phần (kể cả màu bên trong `box-shadow` — nên hai bóng đổ cũng là token). Không
có khối chế độ tối.

| Token | Giá trị | Dùng cho |
|---|---|---|
| `--nen` | `#F1F5F9` | nền trang, chip "không áp dụng", nền hàng bảng khi rê chuột |
| `--be-mat` | `#FFFFFF` | mọi thẻ, khối, hàng danh sách |
| `--be-mat-chim` | `#F8FAFC` | dòng chẵn của bảng, nền hover nhẹ |
| `--chu` | `#0F172A` | chữ chính, nền toast |
| `--chu-phu` | `#475569` | **mọi chữ phụ** (xem mục 6 — đây là một sai lệch có chủ ý) |
| `--chu-mo` | `#94A3B8` | chỉ trang trí: kính lúp trong ô tìm, viền nút khi hover |
| `--chu-nghich` | `#FFFFFF` | chữ trên nền thương hiệu / toast |
| `--vien` / `--vien-dam` | `#E2E8F0` / `#CBD5E1` | đường chia, viền nút & ô nhập |
| `--chinh` / `--chinh-hover` | `#1F4E79` / `#2E75B6` | thương hiệu: logo, nút chính, đầu bảng |
| `--tieu-diem` | `#2E75B6` | vòng focus |
| `--do` `--do-nen` `--do-vien` `--do-dam` | `#DC2626` `#FEF2F2` `#FECACA` `#991B1B` | nghiêm trọng / chưa làm |
| `--vang` … `--vang-dam` | `#D97706` `#FFFBEB` `#FDE68A` `#92400E` | cảnh báo / cần rà |
| `--xanh` … `--xanh-dam` | `#16A34A` `#F0FDF4` `#BBF7D0` `#166534` | đạt / đã làm |
| `--bong-the` / `--bong-noi` | `0 1px 2px rgba(15,23,42,.06)` / `0 10px 28px rgba(15,23,42,.18)` | thẻ / toast |
| `--r` / `--r-nho` | `8px` / `6px` | bo góc |

Ba token `*-dam` là phần **thêm** so với bảng màu được giao: `#DC2626` trên `#FEF2F2`
chỉ đạt 4,43:1, chưa tới 4,5:1 cho chữ nhỏ. Màu gốc (`--do`/`--vang`/`--xanh`) vì vậy
chỉ dùng cho biểu tượng và chấm mức độ (ngưỡng phi-văn-bản 3:1, đều đạt), còn **chữ**
trên nền màu dùng `*-dam` (6,8–7,6:1).

---

## 3. Bộ biểu tượng

Mọi emoji cũ đã bị gỡ khỏi cả ba file web (kiểm tra bằng cách quét toàn bộ điểm mã
≥ U+1F000, U+2600–27BF, U+FE00–FE0F, U+2190–21FF, U+2B00–2BFF — không còn ký tự nào).
Thay bằng **một họ SVG nội tuyến duy nhất**: `viewBox="0 0 24 24"`, `fill="none"`,
`stroke="currentColor"`, `stroke-width="1.75"`, `stroke-linecap/linejoin="round"`. Không
`xmlns` (trong tài liệu HTML không cần, và chuỗi `http://www.w3.org/2000/svg` sẽ làm
hỏng bài kiểm tra offline). Biểu tượng đứng cạnh chữ đã hiện đều `aria-hidden="true"`;
không có nút nào chỉ có biểu tượng mà thiếu tên.

| Khóa | Hình | Dùng ở đâu |
|---|---|---|
| `kiem` | vòng tròn + dấu tích | trạng thái `da_lam`; ô thống kê "Đạt"; banner `san_sang`; mức độ nhóm `xanh` |
| `loi` | vòng tròn + chữ thập | trạng thái `chua_lam`; ô "Nghiêm trọng"; banner `chua_san_sang`; nhóm `do` |
| `canh-bao` | tam giác + chấm than | trạng thái `can_ra`; ô "Cảnh báo"; banner `can_ra_soat`; nhóm `vang` |
| `bo-qua` | vòng tròn + dấu trừ | trạng thái `khong_ap_dung` |
| `thong-ke` | biểu đồ cột | nhóm G6 và mọi check `la_thong_ke` (thay số đếm) |
| `bang-tinh` | file có ô kẻ | nút "Chọn file…", thẻ file, "Kiểm tra file khác", toast "Mở file Excel" |
| `tim-kiem` | kính lúp | ô tìm kiếm, trạng thái rỗng của bảng |
| `mui-phai` | chevron phải | dấu hiệu "mở được" trên hàng checklist; nút "Sau" |
| `mui-trai` | chevron trái | nút "Trước" |
| `tai-ve` | mũi tên xuống khay | "Xuất báo cáo Excel" |
| `thu-muc` | thư mục | toast "Mở thư mục" |
| `lam-lai` | hai mũi tên vòng | "Kiểm tra lại" |
| (tải lên) | mũi tên lên khay | vùng kéo-thả, chỉ trong `index.html` |

Vì `stroke="currentColor"`, biểu tượng trạng thái tự lấy đúng token màu của hàng bao
quanh — điều emoji không làm được.

---

## 4. Thay đổi theo màn hình

### Màn 1 — chọn file

- Cột hẹp 560px, canh giữa; vùng kéo-thả đổi từ viền đứt 2px + emoji 📄 sang viền đứt
  1px + biểu tượng tải lên, đổi màu viền/nền/biểu tượng khi kéo qua (không dịch layout).
- Thẻ file: tên file trên một hàng riêng, ba ô `Kỳ / Số dòng / Tổng phát sinh` trong một
  `<dl>` lưới 3 cột. Nhãn in hoa nhỏ; hai ô số căn phải, `tabular-nums`, **nhãn căn cùng
  chiều với số** để mép phải thẳng hàng.
- Khung tiến trình thành một thẻ có viền, gồm hàng chữ (tên pha ↔ phần trăm) và máng 6px.

### Màn 2 — kết quả

- **Vỏ ứng dụng cố định**: `body` là flex-column `overflow: hidden`; header, banner,
  tab-bar và footer đứng yên, chỉ `.vung-cuon` trôi. Banner và tabs không bao giờ bị đẩy
  khỏi tầm mắt khi cuộn danh sách.
- **Banner** đọc như một status header: biểu tượng mức kết luận + câu kết luận
  (19px/700) + dòng phụ "Kỳ 08/2026 · tên file · 79.450 dòng", rồi **ba ô thống kê** thay
  cho ba chip nhỏ cũ — mỗi ô có biểu tượng + nhãn chữ + con số 24px `tabular-nums`. Ba
  mức `chua_san_sang` / `can_ra_soat` / `san_sang` giữ nguyên từ backend, mỗi mức một bộ
  nền/viền/chữ riêng. **Không mức nào chỉ phân biệt bằng màu** — luôn có biểu tượng và chữ.
- **Tab A** thành một checklist thật: một khối có đầu mục ("11 BƯỚC KHÓA SỔ CUỐI KỲ" +
  dòng đếm "8 đã làm · 0 chưa làm · 3 cần rà · 0 không áp dụng"), các hàng chia bằng
  đường kẻ 1px thay vì 11 thẻ rời. Mỗi hàng: số thứ tự · biểu tượng trạng thái · tên bước
  + tóm tắt · chip trạng thái (biểu tượng + chữ) · chevron.
  Hàng **mở được dựng bằng `<button>` thật** (có focus ring, đi được bằng bàn phím,
  `cursor: pointer`, nền đổi khi hover); hàng **không mở được dựng bằng `<div>`**, không
  chevron, không hover, `cursor: default` — khác biệt nhìn thấy ngay.
  Thứ tự 11 bước giữ đúng thứ tự backend trả về (đó là trình tự nghiệp vụ khóa sổ), không
  sắp xếp lại theo trạng thái.
- **Tab B**: sáu thẻ nhóm trong lưới 3 cột. Đầu thẻ là một `<button>` (mã nhóm, tên, mức
  độ có biểu tượng, con số lớn), bên dưới là danh sách check, mỗi check là một `<button>`
  riêng với chấm mức độ và số lỗi `tabular-nums`. Trước đây thẻ là một `<div>` bắt click
  và bên trong lại có `<li>` bắt click — **không phần tử tương tác nào lồng nhau nữa**, và
  mọi đường vào đều tới được bằng phím Tab. Check thống kê hiện biểu tượng biểu đồ thay
  cho số.
- **Bảng chi tiết**: đầu bảng dính (`position: sticky`, nền `--chinh`, chữ trắng 8,66:1),
  sọc ngựa vằn, hàng rê chuột đổi nền, cột số căn phải + `tabular-nums` + `nowrap`, cột
  chữ căn trái. Bảng cuộn **trong khung của chính nó**
  (`max-height: clamp(180px, 36vh, 420px)`, `overflow: auto`). Trạng thái rỗng có biểu
  tượng kính lúp + câu giải thích (phân biệt "không có dòng nào" với "không khớp từ khóa").
  Phân trang giữ nguyên cơ chế cũ, thêm dải "Dòng 1–100 / 30.000". Ô tìm kiếm giữ
  debounce 300ms, thêm kính lúp và `aria-label`.
- **Footer**: ba nút có biểu tượng; "Kiểm tra file khác" đẩy sang phải vì nó rời bỏ kết
  quả hiện tại, khác nhóm với hai nút kia.

### Chữ số kế toán

`font-variant-numeric: tabular-nums` + `font-feature-settings: "tnum" 1` áp cho: ba ô
thống kê banner, ba ô thẻ file, số thứ tự bước, số lỗi mỗi nhóm và mỗi check, phần trăm
tiến trình, mọi ô `cot_so` của bảng chi tiết, và dải phân trang. Mọi ô số căn phải.

---

## 5. Kiểm tra đã chạy

**Tự động** — `python -m pytest` (pytest.ini đặt `filterwarnings = error`):
**186 passed, 0 warning**, đúng bằng số trước khi sửa. Không nới lỏng một khẳng định nào;
`tests/test_web_static.py` giữ nguyên từng dòng.

**Kiểm bằng script trên chính ba file web:**

- 40 id được `app.js` tham chiếu, **cả 40 đều có trong `index.html`**; và ngược lại,
  `index.html` không khai báo id thừa nào mà `app.js` không dùng.
- Không có `http://` hay `https://` trong bất kỳ file nào (offline tuyệt đối, Segoe UI
  là font hệ thống, mọi SVG nội tuyến).
- Không còn ký tự emoji/pictograph nào.
- Không có mã màu thô nào ngoài `:root`; không token nào dùng mà chưa khai báo, không
  token nào khai báo mà không dùng.
- Duyệt tay **toàn bộ 45 chỗ nội suy `${…}`** trong `app.js`: mỗi chỗ hoặc là hằng nội
  bộ của file, hoặc là số qua `fmt()`, hoặc đã qua `esc()`, hoặc đi vào `textContent` chứ
  không vào `innerHTML`. Chuỗi backend duy nhất vào thuộc tính (`title` của ô mô tả dài)
  cũng qua `esc()` — hàm này escape cả `"`. Ba khóa do backend cấp mà bị ghép vào tên
  class (`trang_thai`, `muc_do`, `muc_do_ket_luan`) đều đi qua `khoaTT`/`khoaMD`/`khoaKL`
  để ép về tập giá trị đã biết trước.

**Kiểm bằng mắt** — dựng một trang mẫu tạm nạp đúng kết quả thật của file 79.450 dòng qua
một `window.pywebview.api` giả, chạy ở viewport **1000×700** (kích thước cửa sổ tối thiểu):

- `document.body.scrollWidth === 1000` ở cả ba màn (màn 1, Tab A, Tab B, bảng mở) —
  **không tràn ngang cửa sổ**.
- Bảng chi tiết 7 cột thật và bảng ép 9 cột với mô tả 180 ký tự: cả hai vừa trong khung
  889px, không tràn ra ngoài; chiều cao hàng ổn định ở 67px.
- Thanh tiến trình: chế độ không xác định → `animation-name: chay-ngang`, 1,15s, không
  `aria-valuenow`; chế độ xác định ở 50% → `animation: none`,
  `transform: matrix(0.5,0,0,1,0,0)`, `transition: transform .2s`, `aria-valuenow="50"`.
- Biến thể giảm chuyển động: `animation-name: nhip-tien-trinh`, 2,4s, nền sọc chéo,
  `width: 100%`.
- Tab bàn phím đi qua được mọi hàng checklist và mọi check trong thẻ nhóm; vòng focus
  2px hiện rõ, nằm ngoài viền 2px nên không đẩy layout.
- Console không có lỗi nào.

**Tương phản (WCAG, tính bằng script):**

| Cặp | Tỉ lệ | Ngưỡng |
|---|---|---|
| chữ chính / bề mặt | 17,85 | 4,5 ✓ |
| chữ phụ / bề mặt | 7,58 | 4,5 ✓ |
| chữ phụ / dòng chẵn bảng | 7,24 | 4,5 ✓ |
| trắng / `--chinh` (nút chính, đầu bảng) | 8,66 | 4,5 ✓ |
| trắng / `--chinh-hover` (nút chính khi hover) | 4,84 | 4,5 ✓ |
| `--do-dam` / `--do-nen` | 7,60 | 4,5 ✓ |
| `--vang-dam` / `--vang-nen` | 6,84 | 4,5 ✓ |
| `--xanh-dam` / `--xanh-nen` | 6,81 | 4,5 ✓ |
| biểu tượng `--vang` / bề mặt | 3,19 | 3,0 ✓ (phi văn bản) |
| biểu tượng `--xanh` / bề mặt | 3,30 | 3,0 ✓ |
| vòng focus / bề mặt | 4,84 | 3,0 ✓ |
| vòng focus / nền trang | 4,42 | 3,0 ✓ |

Vòng focus dùng `outline-offset: 2px` nên luôn nằm trên nền trang hoặc nền thẻ, **không**
nằm sát nền `--chinh` của nút chính (cặp đó chỉ 1,79:1 — nếu đặt `outline-offset: 0`
vòng focus trên nút chính sẽ gần như tàng hình).

---

## 6. Chỗ tôi làm khác chỉ dẫn

**`--chu-mo` (#94A3B8) không được dùng cho chữ.** Trên nền trắng nó chỉ đạt **2,56:1** —
dưới xa ngưỡng 4,5:1. Nếu dùng đúng như tên gọi "muted text", thì nhãn thẻ file, dòng đếm
trạng thái, số thứ tự bước, mã nhóm, dải phân trang và trạng thái rỗng của bảng đều là
chữ không đọc nổi — với người dùng là kế toán viên nhìn màn hình cả buổi chiều cuối tháng
thì đó là hỏng thật, không phải chi li về chuẩn. Tôi giữ token trong bảng màu nhưng chỉ
dùng nó cho hai chỗ thuần trang trí (kính lúp bên trong ô tìm, viền nút phụ khi hover);
mọi chữ phụ chuyển sang `--chu-phu` (7,58:1).

**Thêm ba token `*-dam`** như đã nói ở mục 2, vì cặp màu gốc/nền được giao không đủ tương
phản cho chữ nhỏ.

**Mô tả dài bị kẹp 3 dòng.** Ép thử bảng 9 cột với diễn giải 180 ký tự ở đúng 1000px:
nếu để chữ xuống dòng tự do, mỗi hàng cao 8 dòng và khung 260px chỉ còn thấy được 2 hàng
— tức là một bảng 30.000 dòng gần như không quét được. Tôi kẹp ô chữ còn 3 dòng
(`-webkit-line-clamp`, có dấu ba chấm) và đưa nguyên văn vào `title` để rê chuột đọc đủ.
Đây là chỗ cách làm Swiss-tối-giản "thoáng đãng" đi ngược lại việc quét dữ liệu thật, và
tôi chọn mật độ.

**Thẻ nhóm G1–G6 không còn là một vùng click lồng nhau.** Bản cũ đặt `onclick` lên cả thẻ
`<div>` lẫn từng `<li>` bên trong và phải `stopPropagation`. Bản mới tách đầu thẻ thành
một `<button>` riêng, mỗi check là một `<button>` riêng — cùng hai lối vào như trước,
nhưng đi được bằng bàn phím và không có phần tử tương tác nào lồng nhau.

---

## 7. Đề xuất, chưa làm

1. **Tiến trình pha kiểm tra chỉ có 6 mốc.** `chay_tat_ca` gọi `on_progress` một lần mỗi
   nhóm (0/16/33/50/66/83/100) trong ~0,7 giây, nên thanh xác định nhảy vài nhịp rồi hết.
   Nếu muốn nó mượt, phải sửa Python (báo tiến trình theo từng check, 29 mốc) — ngoài
   phạm vi lần này. Với 0,7 giây thì mức hiện tại vẫn đủ trung thực.
2. **Nếu sau này `evaluate_js` trong pha kiểm tra cũng bị gộp lại và chỉ tới ở cuối**,
   thanh sẽ nhảy thẳng 0 → 100. Bản hiện tại đã an toàn trước tình huống đó: JS mở ở chế
   độ không xác định trước khi `await`, nên vẫn có chuyển động suốt thời gian chờ. Không
   cần sửa gì trừ khi hành vi đổi.
3. **Bảng 30.000 dòng vẫn đang phân trang 100 dòng/trang** (42 trang cho C1.1, 300 trang
   cho mẫu ép). Nên thêm hộp "nhảy tới trang" và cho chọn cỡ trang (100/250/500 — backend
   `lay_chi_tiet` đã nhận `kich_thuoc` tới 500). Chỉ cần sửa JS, không đụng Python.
4. **Sắp xếp / lọc cột trong bảng chi tiết** (đặc biệt là cột số tiền) sẽ giúp tìm dòng
   lệch lớn nhất, nhưng phải phân trang phía backend nên cần chạm Python.
5. **Ảnh chụp màn hình cho tài liệu bàn giao**: tôi kiểm giao diện bằng một trang mẫu tạm
   đã xóa sau khi xong, không chạy `webview.start()` (nó chặn cho tới khi có người đóng
   cửa sổ). Nếu cần ảnh chính thức thì phải mở app thật một lần trên máy khách.
6. **Nhóm 11 bước theo giai đoạn** (tập hợp chi phí → tính giá thành → kết chuyển → thuế)
   sẽ giúp đọc hơn nữa, nhưng nhãn giai đoạn phải do `app/trang_thai.py` cấp mới đúng
   nghiệp vụ — lần này giữ nguyên danh sách phẳng theo đúng thứ tự backend.
