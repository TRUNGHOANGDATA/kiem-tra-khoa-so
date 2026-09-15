# Sửa "Không có kết quả C4.1" + thêm thanh tiến trình khi đọc file

Ngày: 2026-09-15. File thật dùng để kiểm chứng: `1. Source/Bang ke chung tu 082027.xlsx`
(79.450 dòng, kỳ 08/2026).

---

## 1. Vấn đề 1 — "Không có kết quả C4.1" khi bấm bước Tab A

### Chẩn đoán

`JsApi._nap_file()` (được gọi từ `lay_file_moi_nhat`, `chon_file`, `nap_file`) luôn xóa
`self._kq = {}` mỗi khi nạp một file — kể cả khi màn hình kết quả (màn 2) từ lần kiểm tra
trước vẫn còn đang hiển thị trên UI. `self._tt`/`self._df` vẫn được gán lại (không bao giờ
`None` sau một lần nạp thành công), nhưng `self._kq` thì trống. Khi người dùng bấm vào một
bước Tab A hoặc thẻ Tab B lúc đó, `lay_chi_tiet(ma_check)` tra `self._kq.get(ma_check)` ra
`None` và trả thẳng `{"loi": f"Không có kết quả {ma_check}"}` — một mã nội bộ vô nghĩa với
người dùng, trong khi chính dòng số liệu trên màn hình (do `_tom_tat()` build từ
`self._ket_qua`/`self._trang_thai` tại thời điểm `chay_kiem_tra()` chạy) vẫn đúng.

Không cần truy đúng thao tác nào của người dùng kích hoạt lại `_nap_file` (khởi động lại app
tự tìm file, JS gọi lại `lay_file_moi_nhat`, một lần "Kiểm tra lại" trung gian, v.v.) — theo
đúng yêu cầu, việc cần làm là loại bỏ hẳn kiểu lỗi này, không đi tìm nguyên nhân kích hoạt.

### Thay đổi

`app/api.py`:

- Trích `_chay_lai_kiem_tra(on_progress=None)` từ phần thân cũ của `chay_kiem_tra` — chạy
  29 check + suy trạng thái từ `self._df`/`self._tt` đã có sẵn, dùng chung bởi `chay_kiem_tra`
  và cơ chế tự phục hồi mới.
- `lay_chi_tiet()`: khi `self._kq.get(ma_check)` ra `None`:
  - Nếu `self._df`/`self._tt` cũng chưa có (chưa từng nạp file nào) → trả lỗi hướng dẫn hành
    động: `"Chưa có dữ liệu — hãy chọn file và bấm Kiểm tra"`, không nêu mã nội bộ.
  - Ngược lại (file đã đọc, chỉ cache `_kq` bị mất) → gọi `_chay_lai_kiem_tra()` một lần để
    dựng lại `_kq`/`_ket_qua`/`_trang_thai`, rồi tra lại `ma_check`. Chi phí ~1,3s (chỉ chạy
    lại 29 check trên `self._df` đã có sẵn trong RAM — không đọc lại Excel).
  - Chỉ thử dựng lại **một lần**: nếu sau khi chạy lại vẫn không có `ma_check` (mã không tồn
    tại thật, ví dụ lỗi gõ nhầm), trả lỗi rõ ràng `"Không tìm thấy kết quả {ma_check} sau khi
    chạy lại kiểm tra"` thay vì tự gọi lại chính nó — tránh vòng lặp dựng-lại vô ích.

### Test thêm (`tests/test_api.py`)

- `test_lay_chi_tiet_tu_phuc_hoi_khi_kq_bi_xoa` — chạy kiểm tra, xóa tay `api._kq = {}` (mô
  phỏng đúng triệu chứng khách hàng gặp), gọi `lay_chi_tiet("C1.1")` → phải trả kết quả đúng
  (không lỗi), và `_kq`/`_ket_qua`/`_trang_thai` phải được dựng lại đầy đủ.
- `test_lay_chi_tiet_bao_loi_ro_rang_khi_chua_co_du_lieu` — `JsApi()` mới toanh, gọi
  `lay_chi_tiet` ngay → đúng câu lỗi hướng dẫn hành động.
- `test_lay_chi_tiet_ma_khong_ton_tai_sau_khi_chay_lai_khong_lap_vo_han` — sau khi xóa `_kq`,
  hỏi một mã không tồn tại → lỗi rõ ràng một lần, không đệ quy/lặp.

---

## 2. Vấn đề 2 — không có phản hồi khi đang đọc file

### Chẩn đoán

`_tien_trinh()` (gọi `window.onTienTrinh` qua `evaluate_js`) trước đây chỉ được gọi từ bên
trong `checks.chay_tat_ca()` — tức là chỉ trong lúc chạy 29 check (~1,3s). Việc đọc Excel
(~85% thời gian chờ thật, đo trên file thật bên dưới là ~8,4s/9,1s tổng) diễn ra hoàn toàn im
lặng bên trong `_nap_file()`, được gọi từ `lay_file_moi_nhat`/`chon_file`/`nap_file` — không
có sự kiện tiến trình nào phát ra trong suốt quãng đó. Vì Python (pywebview) chặn luồng UI khi
đọc, cửa sổ đứng im hoàn toàn — đúng như phản ánh của khách hàng.

### Thay đổi backend (`app/api.py`)

- `_nap_file()` phát hai mốc quanh việc đọc: `"Đang đọc file…"` ở 0% **trước** khi gọi
  `doc_bang_ke()`, và `f"Đã đọc {n} dòng"` ở 85% **sau** khi đọc xong (số dòng định dạng kiểu
  Việt Nam qua `_dinh_dang_so`, ví dụ `"Đã đọc 79.450 dòng"`).
- `chay_kiem_tra()`: nếu lần gọi này vừa phải đọc lại file (`self._tt is None` hoặc
  `self._tt.path != path`), phần kiểm tra chỉ còn 85–100% thanh tiến trình (đọc đã chiếm
  0–85%). Nếu file đã có sẵn từ trước (trường hợp thường gặp: màn 1 đã tự nạp xong, người
  dùng bấm "Kiểm tra" — lúc đó việc của riêng lần gọi này chỉ là chạy check), kiểm tra được
  trọn 0–100% — không bị "co lại" một cách vô lý khi bản thân nó không phải đợi đọc gì cả.
  Việc rescale nằm ở `_tien_trinh_kiem_tra(ti_le_bat_dau)`, bọc ngoài `on_progress` truyền vào
  `checks.chay_tat_ca` — không đụng vào `chay_tat_ca()`/`TEN_NHOM` (giữ nguyên hợp đồng đã có
  test riêng ở `tests/test_chay_tat_ca.py`).

### Thay đổi frontend (`app/web/app.js`)

- `onTienTrinh(ten, pct)` rút gọn: hiển thị thẳng `ten` do backend gửi (backend giờ luôn gửi
  câu hoàn chỉnh: `"Đang đọc file…"`, `"Đã đọc N dòng"`, `"Đang kiểm tra: <nhóm>…"`,
  `"Hoàn tất"`) — bỏ việc JS tự ghép chữ "Đang kiểm tra:" cứng, vì câu đó không còn đúng cho
  pha đọc file.
- Thêm `taiFile(hamGoiApi, nhanBatDau)`: khóa nút "Kiểm tra" + mở thanh tiến trình (gọi
  `onTienTrinh` để `classList.remove("an")`) **trước khi `await`** lệnh cầu nối — vì Python
  chặn luồng lúc đọc, mở thanh sau khi có callback đầu tiên là quá trễ (cửa sổ đã đứng im từ
  trước đó). Dùng `try/finally` để luôn ẩn lại thanh và khôi phục trạng thái nút dù thành công
  hay lỗi (khôi phục về trạng thái *trước đó* của nút, không phải luôn bật — nếu file mới nạp
  lỗi thì file cũ vẫn còn dùng được, không nên khóa vĩnh viễn nút "Kiểm tra").
- Áp `taiFile` cho cả 3 đường nạp file: `khoiTao()` (tự nạp lúc khởi động),
  `btn-chon-file` ("Chọn file…"), và sự kiện `drop` (kéo-thả).
- `chayKiemTra()` ("Kiểm tra"/"Kiểm tra lại"): vốn đã khóa nút + mở thanh trước khi `await` —
  bọc thêm `try/finally` quanh phần mở khóa nút/ẩn thanh để đảm bảo luôn chạy kể cả khi có lỗi
  bất ngờ ở nhánh code phía sau, không chỉ ở nhánh `kq.loi` đã kiểm tra tường minh.

### Trình tự tiến trình đo được trên file thật

Nạp lần đầu (chưa từng gọi `lay_file_moi_nhat`) rồi bấm "Kiểm tra" ngay — phải đọc + kiểm tra
trong cùng một lệnh gọi `chay_kiem_tra()`, thanh chia đúng theo tỉ lệ đọc (0–85%) / kiểm tra
(85–100%):

```
"Đang đọc file…"                         0
"Đã đọc 79.450 dòng"                    85
"Đang kiểm tra: Hình thức chứng từ…"     85
"Đang kiểm tra: Định khoản bất thường…"  87
"Đang kiểm tra: Thuế GTGT…"              89
"Đang kiểm tra: Kho & giá vốn…"          92
"Đang kiểm tra: Kết chuyển cuối kỳ…"     94
"Đang kiểm tra: Thống kê & soát xét…"    97
"Hoàn tất"                              100
```

Luồng UI thật (màn 1 tự nạp lúc khởi động, rồi người dùng bấm "Kiểm tra" ở một thời điểm
khác) là hai phiên thanh tiến trình tách biệt: phiên nạp file (0→85, ẩn đi ngay sau khi
`lay_file_moi_nhat` trả về) và phiên kiểm tra (0→100, vì lúc đó không cần đọc lại gì) — đo
được:

```
[phiên nạp file, ẩn sau khi xong]
"Đang đọc file…"           0
"Đã đọc 79.450 dòng"      85

[phiên bấm "Kiểm tra", ~0,7-1,3s]
"Đang kiểm tra: Hình thức chứng từ…"     0
"Đang kiểm tra: Định khoản bất thường…" 16
"Đang kiểm tra: Thuế GTGT…"             33
"Đang kiểm tra: Kho & giá vốn…"         50
"Đang kiểm tra: Kết chuyển cuối kỳ…"    66
"Đang kiểm tra: Thống kê & soát xét…"   83
"Hoàn tất"                             100
```

---

## 3. Vấn đề 3 — có đọc file hai lần không?

### Kết luận: **không** — đã xác nhận trên file thật, không đổi mã cho phần này

Đo trực tiếp bằng cách gắn spy lên `pandas.read_excel` rồi chạy đúng luồng thật:
`lay_file_moi_nhat()` → lấy `info["path"]` → gọi `chay_kiem_tra(info["path"])` (mô phỏng
đúng những gì JS làm: lưu `info.path` rồi trả nguyên văn lại khi bấm "Kiểm tra").

```
lay_file_moi_nhat path: 1. Source\Bang ke chung tu 082027.xlsx
lay_file_moi_nhat time: 8.37s
read_excel calls so far: 1
path giống nhau (is): True
chay_kiem_tra time: 0.70s
read_excel calls total: 1
tổng wall clock lay_file_moi_nhat -> chay_kiem_tra: 9.07s
```

`read_excel` chỉ được gọi **một lần** tổng cộng. Lý do không chỉ đúng cho lần đo này mà đúng
theo cấu trúc mã cho cả ba lối vào (`lay_file_moi_nhat`, `chon_file`, `nap_file`/kéo-thả):
`_nap_file(path)` luôn gán `self._tt.path = path` **y hệt** chuỗi được truyền vào (từ
`doc_bang_ke`/`ThongTinFile`, không có bước biến đổi nào), và chuỗi đó là chuỗi duy nhất được
trả về cho JS trong `info["path"]`. Phía JS chỉ lưu `fileHienTai.path = info.path` rồi trả
nguyên văn khi bấm "Kiểm tra" — JSON round-trip (Python → `evaluate_js`/return value → JS →
`api.chay_kiem_tra(...)`) không biến đổi nội dung chuỗi (không đổi hoa/thường, không đổi dấu
phân cách). Vì vậy `self._tt.path != path` trong `chay_kiem_tra` luôn là `False` ở lượt gọi
thứ hai, không có đường nào trong mã hiện tại khiến hai chuỗi này lệch nhau.

Theo đúng nhánh "nếu đã khớp thì không đổi gì" của yêu cầu, **không thêm** bước chuẩn hóa
đường dẫn (`os.path.normcase`/`Path.resolve`) — thêm vào sẽ là mã phòng thủ cho một tình huống
không thể xảy ra với cấu trúc hiện tại, không giải quyết vấn đề thật nào. Đã ghi chú lại lý do
này ngay tại `chay_kiem_tra()` trong `app/api.py` để agent sau không tốn công điều tra lại.

### Test thêm để chặn hồi quy

- `test_chay_kiem_tra_lan_2_cung_duong_dan_khong_doc_lai_file` — gọi `chay_kiem_tra(p)` hai
  lần liên tiếp với cùng path, đếm số lần `doc_bang_ke` được gọi → phải là 1.
- `test_man_hinh_1_roi_kiem_tra_khong_doc_lai_file` — mô phỏng đúng luồng thật:
  `lay_file_moi_nhat()` rồi `chay_kiem_tra(info["path"])` — đếm `doc_bang_ke` → phải là 1.

---

## 4. Kết quả test

```
python -m pytest -q -W error
........................................................................ [ 38%]
........................................................................ [ 77%]
..........................................                               [100%]
186 passed
```

186 test (181 cũ + 5 mới: 3 cho vấn đề 1, 2 cho vấn đề 3 — vấn đề 2 được phủ gián tiếp bởi
`test_gan_window_day_tien_trinh_qua_evaluate_js` đã có sẵn, vẫn xanh sau khi đổi thang tiến
trình, cộng với việc chạy tay trên file thật ở mục 2 và 3). `tests/test_web_static.py` (kiểm
tra id, escape, không URL ngoài) vẫn xanh nguyên — không đổi cấu trúc HTML/JS theo hướng vi
phạm các bất biến đó.

Không sửa logic check, ngưỡng, hay câu kết luận sẵn sàng khóa sổ — chỉ đổi phản hồi tiến
trình và cách `lay_chi_tiet`/`chay_kiem_tra` xử lý trạng thái cache.

---

## 5. Khuyến nghị không thực hiện trong task này

- Không tìm nguyên nhân chính xác nào đã kích hoạt lại `_nap_file` khiến khách hàng gặp "Không
  có kết quả C4.1" (theo đúng yêu cầu — loại bỏ kiểu lỗi thay vì săn nguyên nhân). Nếu muốn
  biết chắc, có thể thêm log tạm thời ghi lại mỗi lần `_nap_file`/`lay_chi_tiet` được gọi kèm
  timestamp trong một bản build thử nghiệm gửi khách hàng.
- Chưa disable các nút khác (`btn-chon-file`, `btn-file-khac`) trong lúc "Kiểm tra" đang chạy,
  hay ngược lại — chỉ làm đúng phạm vi yêu cầu ("Disable nút Kiểm tra"). Nếu khách hàng vẫn có
  thể bấm "Chọn file…" trong lúc đang kiểm tra và muốn chặn luôn, đó là một yêu cầu UX riêng,
  chưa có trong phản ánh gốc.
- Không thêm log/telemetry để tự phát hiện khi cơ chế tự phục hồi ở vấn đề 1 được kích hoạt
  trong thực tế (ví dụ đếm số lần) — nếu muốn theo dõi mức độ phổ biến của triệu chứng gốc sau
  khi phát hành, cần bàn thêm về nơi lưu (không có backend log tập trung trong app desktop
  này).
