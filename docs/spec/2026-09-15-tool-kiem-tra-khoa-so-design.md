# SPEC — Tool Kiểm Tra Khóa Sổ Cuối Kỳ

- **Ngày:** 2026-09-15
- **Trạng thái:** Draft để duyệt
- **Chế độ kế toán:** Thông tư 200 · **Ngành:** Sản xuất · **Kỳ:** Khóa sổ tháng
- **Nguồn dữ liệu:** Bảng kê chứng từ xuất từ Bravo (Excel)

---

## 1. Mục tiêu

Xây dựng một **ứng dụng desktop** giúp kế toán **tự động rà soát bảng kê chứng từ cuối kỳ** trước khi khóa sổ, phát hiện sai sót/thiếu sót nghiệp vụ (đặc biệt **tính giá vốn** và **kết chuyển chi phí cuối kỳ**), và **xuất báo cáo Excel** liệt kê chi tiết từng vấn đề để kế toán sửa trong Bravo.

Tool thay thế việc dò tay thủ công, bám theo chuẩn kiểm tra đối chiếu của phần mềm kế toán (MISA/AMIS) và thực hành khóa sổ theo TT200.

## 2. Người dùng & bối cảnh

- **Người dùng:** Kế toán tổng hợp / kế toán trưởng (không cần biết lập trình).
- **Tần suất:** Hàng tháng, mỗi lần với một file bảng kê mới của kỳ đó.
- **Máy:** Windows 11, đã có Python. (Giai đoạn sau có thể đóng gói `.exe` để chạy máy không cài Python.)

## 3. Kiến trúc tổng thể

Ứng dụng desktop kiểu **pywebview**: một cửa sổ native hiển thị giao diện web (HTML/CSS/JS), backend là Python.

```
┌─────────────────────────────────────────────────────────┐
│  Cửa sổ pywebview (native window)                         │
│  ┌───────────────────────────────────────────────────┐   │
│  │  Frontend: HTML + CSS + JS (Segoe UI, light mode)  │   │
│  │  - Chọn/kéo-thả file bảng kê                        │   │
│  │  - Nút "Kiểm tra"                                   │   │
│  │  - Hiển thị bảng điểm & chi tiết lỗi               │   │
│  │  - Nút "Xuất báo cáo Excel"                         │   │
│  └───────────────────────────────────────────────────┘   │
│                   ▲  gọi qua js_api (bridge)               │
│                   ▼                                        │
│  Backend Python:                                          │
│   ├── api.py        (lớp js_api: cầu nối JS ↔ Python)     │
│   ├── loader.py     (đọc & chuẩn hóa bảng kê -> DataFrame)│
│   ├── checks/       (mỗi nhóm kiểm tra 1 module)          │
│   ├── report.py     (xuất báo cáo Excel bằng xlsxwriter)  │
│   └── main.py       (khởi tạo cửa sổ webview)             │
└─────────────────────────────────────────────────────────┘
```

**Nguyên tắc thiết kế:** mỗi bộ check là một hàm độc lập, nhận `DataFrame` chuẩn hóa, trả về một `CheckResult` thống nhất → dễ thêm/bớt check, dễ test từng cái riêng.

## 4. Cấu trúc thư mục dự án

```
Check List Khoa So Ke Toan/
├── 1. Source/                     # người dùng đặt file bảng kê vào đây
│   └── Bang ke chung tu 082027.xlsx
├── 2. Report/                     # tool xuất báo cáo Excel ra đây (tự tạo)
├── app/
│   ├── main.py                    # entry point, mở cửa sổ pywebview
│   ├── api.py                     # JsApi: chon_file, chay_kiem_tra, xuat_bao_cao
│   ├── loader.py                  # đọc Excel -> DataFrame chuẩn hóa
│   ├── checks/
│   │   ├── __init__.py            # đăng ký danh sách check theo thứ tự
│   │   ├── base.py                # CheckResult, mức độ, tiện ích chung
│   │   ├── g1_chung_tu.py         # Nhóm 1: hình thức chứng từ
│   │   ├── g2_dinh_khoan.py       # Nhóm 2: định khoản bất thường
│   │   ├── g3_thue_gtgt.py        # Nhóm 3: thuế GTGT
│   │   ├── g4_kho_gia_von.py      # Nhóm 4: kho & giá vốn
│   │   ├── g5_ket_chuyen.py       # Nhóm 5: kết chuyển cuối kỳ
│   │   └── g6_tong_quan.py        # Nhóm 6: thống kê & soát xét
│   ├── report.py                  # xuất báo cáo Excel
│   └── web/
│       ├── index.html
│       ├── style.css              # Segoe UI, light mode
│       └── app.js
├── Kiem_tra_khoa_so.bat           # bấm để chạy app (python app/main.py)
├── requirements.txt
└── docs/spec/2026-09-15-tool-kiem-tra-khoa-so-design.md
```

## 5. Luồng hoạt động (UX) — "1 nút, xem ngay trong app"

**Nguyên tắc:** kết quả kiểm tra hiển thị **trực tiếp trong cửa sổ app**. File Excel chỉ là tùy chọn xuất để lưu trữ/gửi người khác — không bắt buộc phải mở Excel mới xem được kết quả.

1. Người dùng bấm `Kiem_tra_khoa_so.bat` → cửa sổ app mở ở **Màn hình 1 — Chọn file**.
2. App **tự nhận file mới nhất** trong `1. Source` và hiện thông tin: tên file, kỳ (min–max `DocDate`), số dòng, tổng phát sinh. Có thể kéo-thả / chọn file khác.
3. Bấm **"Kiểm tra"** (1 nút duy nhất) → backend chạy toàn bộ check (hiện thanh tiến trình) → app **tự chuyển sang Màn hình 2 — Kết quả**.
4. **Màn hình 2 — Kết quả** gồm thanh tóm tắt trên cùng + 2 tab:

   **Thanh tóm tắt:** kỳ đang kiểm · tổng số dòng · số 🔴 / 🟡 · kết luận lớn: **"SẴN SÀNG KHÓA SỔ"** (không còn 🔴) hoặc **"CHƯA SẴN SÀNG — còn N việc"**.

   **Tab A — "Trạng thái khóa sổ" (xem *cái gì chưa làm*):** danh sách các bước nghiệp vụ cuối kỳ, mỗi bước một dòng với trạng thái suy ra từ dữ liệu:
   - ✅ **Đã làm** — phát hiện có bút toán tương ứng
   - ❌ **Chưa làm** — có phát sinh liên quan nhưng thiếu bút toán
   - ⚠️ **Cần rà** — làm rồi nhưng số liệu bất thường (vd còn net ≠ 0)
   - ➖ **Không áp dụng** — kỳ này không có phát sinh liên quan

   Danh sách bước (nguồn dữ liệu từ check tương ứng ở mục 7):

   | Bước | Suy ra từ |
   |------|-----------|
   | Tập hợp CP NVL trực tiếp 621 → 154 | C4.4 |
   | Tập hợp CP nhân công trực tiếp 622 → 154 | C4.4 |
   | Tập hợp & phân bổ CP SXC 627 → 154 | C4.4 |
   | Nhập kho thành phẩm 154 → 155 (tính giá thành) | C4.5 |
   | Xuất kho có đầy đủ giá (không dòng giá = 0) | C4.1 |
   | Kết chuyển giá vốn 632 → 911 | C5.2 |
   | Kết chuyển doanh thu 511/515/711 → 911 | C5.3 |
   | Kết chuyển chi phí 635/641/642/811 → 911 | C5.4 |
   | Khấu trừ thuế GTGT 33311 ↔ 1331 | C5.6 |
   | Kết chuyển lãi/lỗ 911 ↔ 421 | C5.5 |
   | TK đầu 5/6/7/8 đã về 0 (kết chuyển hết) | C5.1 |

   Click một bước → mở bảng chi tiết chứng minh (các dòng bút toán liên quan hoặc số net theo TK).

   **Tab B — "Lỗi & cảnh báo" (xem *lỗi ở đâu*):** dãy thẻ (card) theo 6 nhóm với số lỗi & màu mức độ. Click thẻ → bảng chi tiết các dòng vi phạm (`DocNo`, ngày, TK Nợ/Có, số tiền, diễn giải, lý do), có **ô tìm kiếm** và **lọc theo mức độ**, sắp xếp theo cột. Bảng dài dùng phân trang/cuộn ảo để không đơ.

5. Nút hành động ở footer Màn hình 2:
   - **"Xuất báo cáo Excel"** → tạo file trong `2. Report/`; xong hiện toast kèm 2 nút **"Mở file Excel"** và **"Mở thư mục"**.
   - **"Kiểm tra file khác"** → quay lại Màn hình 1.
   - **"Kiểm tra lại"** → chạy lại trên file hiện tại (sau khi kế toán đã sửa & xuất lại bảng kê).

## 6. Đặc tả dữ liệu đầu vào

File Excel 1 sheet (`Table1`), dòng 1 là header, 79 cột. Các cột tool sử dụng:

| Cột | Ý nghĩa | Dùng cho |
|-----|---------|----------|
| `DocCode` | Loại chứng từ (BT, BC, NM, CP, PN…) | phân loại, thống kê |
| `DocNo` | Số chứng từ | định danh, nghi trùng |
| `DocDate` | Ngày chứng từ | kiểm tra ngoài kỳ |
| `Description` | Diễn giải | thiếu diễn giải |
| `DebitAccount` (= `Account`) | TK Nợ | mọi check định khoản |
| `CreditAccount` (= `CrspAccount`) | TK Có | mọi check định khoản |
| `Amount` (= `DebitAmount`) | Số tiền VND | mọi check số tiền |
| `OriginalAmount` | Số tiền nguyên tệ | check ngoại tệ |
| `CurrencyCode`, `ExchangeRate` | Loại tiền, tỷ giá | check ngoại tệ |
| `TaxCode` | Mã thuế (V10, V08, R10A…) | check thuế GTGT |
| `CustomerCode`, `CustomerName` | Đối tượng | thiếu đối tượng 131/331 |
| `ItemCode`, `ItemName` | Vật tư/hàng | check kho |
| `WarehouseName` | Kho | check kho |
| `Quantity9` | Số lượng | check giá xuất kho |
| `UnitCost` | Đơn giá | check giá xuất kho |
| `CreatedByName` | Người lập | thống kê |
| `CashFlowName`, `ExpenseCatgName`, `DeptName` | Chiều phân tích | thống kê |

**Chuẩn hóa trong `loader.py`:**
- Đổi chuỗi `"NULL"`, `""`, khoảng trắng → `NA`.
- Ép `Amount`, `Quantity9`, `UnitCost`, `ExchangeRate`, `OriginalAmount` về số (lỗi ép → 0, ghi log).
- Ép `DocDate` về ngày.
- TK Nợ/Có ép về chuỗi, cắt khoảng trắng.
- Tạo cột phụ `Kỳ` = tháng/năm suy từ `DocDate` để xác định kỳ đang kiểm.
- Xác định **kỳ chính** = tháng xuất hiện nhiều nhất trong `DocDate` (dùng cho check "ngoài kỳ").

## 7. Danh mục kiểm tra chi tiết (v1)

Mỗi check có: **mã**, **tên**, **logic**, **mức độ mặc định**, **các cột xuất ra** khi có vi phạm.
Mức độ: 🔴 Nghiêm trọng (phải sửa trước khóa sổ) · 🟡 Cảnh báo (rà soát) · 🟢 Đạt.

Cột chuẩn cho mọi sheet chi tiết lỗi: `DocNo | DocDate | DebitAccount | CreditAccount | Amount | Description | Lý do`.

### Nhóm 1 — Hình thức chứng từ (`g1_chung_tu.py`)
| Mã | Tên | Logic | Mức độ |
|----|-----|-------|--------|
| C1.1 | Thiếu diễn giải | `Description` rỗng | 🟡 |
| C1.2 | Ngày ngoài kỳ | `DocDate` không thuộc kỳ chính | 🔴 |
| C1.3 | Nghi trùng bút toán | Trùng toàn bộ (`DocNo`,`DebitAccount`,`CreditAccount`,`Amount`,`Description`) ≥ 2 lần | 🟡 |
| C1.4 | Nợ = Có cùng tài khoản | `DebitAccount == CreditAccount` | 🔴 |
| C1.5 | Số tiền ≤ 0 | `Amount <= 0` | 🔴 |
| C1.6 | Thiếu số chứng từ / ngày | `DocNo` hoặc `DocDate` rỗng | 🔴 |

### Nhóm 2 — Định khoản bất thường (`g2_dinh_khoan.py`)
| Mã | Tên | Logic | Mức độ |
|----|-----|-------|--------|
| C2.1 | Thiếu mã đối tượng ở TK công nợ | TK Nợ/Có bắt đầu `131`/`331` nhưng `CustomerCode` rỗng | 🟡 |
| C2.2 | TK không đúng định dạng | TK không khớp mẫu số hệ thống (chỉ số, độ dài ≥ 3) | 🟡 |
| C2.3 | Định khoản qua TK trung gian bất thường | Nợ và Có cùng nhóm tiền (`111`↔`111`, `112`↔`112`) | 🟡 |
| C2.4 | Chênh lệch quy đổi ngoại tệ | `CurrencyCode≠VND` và `|Amount − OriginalAmount×ExchangeRate|` vượt ngưỡng 1đ | 🟡 |

### Nhóm 3 — Thuế GTGT (`g3_thue_gtgt.py`)
| Mã | Tên | Logic | Mức độ |
|----|-----|-------|--------|
| C3.1 | Có mã thuế nhưng thiếu TK thuế | `TaxCode` có giá trị (≠V00/rỗng) nhưng cả Nợ lẫn Có đều không thuộc `1331`/`33311` trong cùng `DocNo` | 🟡 |
| C3.2 | Doanh thu thiếu thuế đầu ra | Trong 1 `DocNo` có TK Có `511*` với `TaxCode` chịu thuế nhưng không có dòng `33311` | 🟡 |
| C3.3 | Bảng tổng hợp thuế | Tổng thuế vào (`1331`) & ra (`33311`) theo `TaxCode`/thuế suất (bảng tham chiếu, không phải lỗi) | 🟢 |

### Nhóm 4 — Kho & giá vốn ⭐ (`g4_kho_gia_von.py`)
| Mã | Tên | Logic | Mức độ |
|----|-----|-------|--------|
| C4.1 | Xuất kho giá = 0 | Dòng có `Quantity9>0` và TK kho (`152/155/156…`) nhưng `UnitCost=0` hoặc `Amount=0` | 🔴 |
| C4.2 | Lệch tiền = SL × đơn giá | `|Amount − Quantity9×UnitCost|` vượt ngưỡng làm tròn | 🟡 |
| C4.3 | Giá vốn không đi kèm kho | Nợ `632*` nhưng TK Có không thuộc `155/156/154` | 🟡 |
| C4.4 | Chưa tập hợp chi phí SX về 154 | Có phát sinh `621/622/627` nhưng **thiếu bút toán kết chuyển sang `154`** (không có dòng Nợ `154`/Có `621|622|627`) | 🔴 |
| C4.5 | Chưa nhập kho thành phẩm | Có Nợ `154` (kết chuyển) nhưng **thiếu** dòng Nợ `155`/Có `154` | 🟡 |
| C4.6 | Đơn giá xuất kho lệch mặt bằng mã hàng | Đơn giá suy ra (`Amount/Quantity9`) trên dòng xuất gấp ≥10 lần hoặc ≤1/10 **trung vị của chính mã hàng đó** trong kỳ; chỉ xét mã xuất ≥3 lần | 🟡 |

> C4.1 và C4.6 đã được sửa sau khi đối chiếu dữ liệu thật — xem
> `docs/ket-qua/sua-c41-gia-xuat-kho.md` và `docs/ket-qua/nhieu-chi-nhanh-va-don-gia.md`.

### Nhóm 5 — Kết chuyển cuối kỳ ⭐ (`g5_ket_chuyen.py`)
Xây "sổ phát sinh theo TK" (net theo mỗi TK = Σ phát sinh Nợ − Σ phát sinh Có, khớp theo prefix).

| Mã | Tên | Logic | Mức độ |
|----|-----|-------|--------|
| C5.1 | TK đầu 5/6/7/8 chưa kết chuyển hết | Với mỗi TK đầu `5,6,7,8`: net phát sinh trong kỳ ≠ 0 → nghi chưa kết chuyển về `911` | 🟡 |
| C5.2 | Thiếu kết chuyển giá vốn | Không có dòng Nợ `911`/Có `632*` dù có phát sinh `632*` | 🔴 |
| C5.3 | Thiếu kết chuyển doanh thu | Có `511/515/711` nhưng thiếu dòng Nợ `511/515/711`/Có `911` | 🔴 |
| C5.4 | Thiếu kết chuyển chi phí | Có `635/641/642/811` nhưng thiếu dòng Nợ `911`/Có tương ứng | 🔴 |
| C5.5 | Thiếu kết chuyển lãi/lỗ | Có phát sinh `911` nhưng không có dòng `911`↔`421` | 🟡 |
| C5.6 | Thiếu khấu trừ thuế GTGT | (tùy chọn) không có dòng `33311`↔`1331` khi cả hai đều có số dư | 🟢/🟡 |

*Ghi chú:* C5.1 để mức 🟡 vì có DN chỉ kết chuyển cuối năm — báo cáo nêu rõ để kế toán tự quyết.

### Nhóm 6 — Thống kê & soát xét (`g6_tong_quan.py`)
| Mã | Tên | Nội dung |
|----|-----|----------|
| C6.1 | Top giao dịch giá trị lớn | Top 50 dòng `Amount` lớn nhất để soát xét thủ công |
| C6.2 | Phát sinh theo tài khoản | Bảng Σ theo TK Nợ / TK Có |
| C6.3 | Phát sinh theo loại chứng từ | Bảng Σ theo `DocCode` |
| C6.4 | Phát sinh theo người lập | Bảng Σ & đếm theo `CreatedByName` |
| C6.5 | Phân bố theo ngày | Σ theo `DocDate`, đánh dấu ngày dồn bút toán bất thường |

## 8. Đặc tả báo cáo Excel đầu ra

- **Tên file:** `Bao cao kiem tra khoa so - <kỳ> - <yyyymmdd_hhmm>.xlsx` trong `2. Report/`.
- **Sheet `Tổng quan`:** tiêu đề kỳ; bảng mỗi nhóm/mã check: tên, số dòng vi phạm, mức độ (tô màu), kết luận. Ô "Mức độ sẵn sàng khóa sổ": Đạt nếu không còn 🔴.
- **Mỗi check có vi phạm → 1 sheet chi tiết:** tên sheet = mã check; cột chuẩn ở mục 7; đóng băng dòng tiêu đề, auto-filter, tô màu theo mức độ.
- **Sheet thống kê (Nhóm 6):** các bảng tổng hợp.
- Định dạng: Segoe UI, header nền xanh đậm chữ trắng, số có phân tách hàng nghìn.

## 9. Đặc tả giao diện (frontend)

- **Font:** `Segoe UI` toàn bộ. **Chế độ:** Light mode (nền trắng/xám nhạt, chữ tối).
- **Bảng màu:**
  - Nền: `#FFFFFF` / vùng phụ `#F5F7FA`
  - Chữ chính: `#1F2937`; chữ phụ `#6B7280`
  - Nhấn (primary): `#1F4E79` (xanh kế toán), hover `#2E75B6`
  - Trạng thái: 🔴 `#DC2626` / 🟡 `#D97706` / 🟢 `#16A34A`
  - Viền: `#E5E7EB`
- **Bố cục (2 màn hình, chuyển cảnh trong cùng cửa sổ):**
  - Header cố định: tên app "Kiểm tra khóa sổ cuối kỳ" + logo chữ; bên phải hiện tên file/kỳ đang kiểm (khi có).
  - **Màn hình 1 — Chọn file:** khung kéo-thả (dashed border) + nút "Chọn file"; thẻ thông tin file (tên, kỳ, số dòng, tổng phát sinh); nút **"Kiểm tra"** primary, lớn, ở giữa. Khi chạy: thanh tiến trình + tên check đang chạy.
  - **Màn hình 2 — Kết quả:**
    - *Thanh tóm tắt* (banner): kết luận lớn "SẴN SÀNG KHÓA SỔ" nền xanh nhạt / "CHƯA SẴN SÀNG — còn N việc" nền đỏ nhạt; kèm 3 con số 🔴 🟡 🟢.
    - *Tab bar:* "Trạng thái khóa sổ" · "Lỗi & cảnh báo".
    - *Tab A:* danh sách bước dạng checklist: icon trạng thái (✅ ❌ ⚠️ ➖) · tên bước · số liệu tóm tắt (vd "Nợ 154 / Có 621: 8.607 dòng, 120,5 tỷ") · mũi tên mở chi tiết.
    - *Tab B:* lưới thẻ 6 nhóm (số lỗi lớn + nhãn mức độ màu) → bên dưới là bảng chi tiết của thẻ đang chọn: ô tìm kiếm, bộ lọc mức độ, header bấm để sắp xếp, phân trang 100 dòng/trang.
    - *Footer:* "Xuất báo cáo Excel" (primary) · "Kiểm tra lại" · "Kiểm tra file khác". Sau khi xuất: toast + "Mở file Excel" · "Mở thư mục".
- Responsive tối thiểu cho cửa sổ ~1000×700, cuộn dọc khi bảng dài; bảng chi tiết cuộn trong khung riêng để header/tab luôn thấy.
- Không dùng CDN ngoài (chạy offline) — CSS/JS để local trong `app/web/`.

## 10. Cầu nối Backend ↔ Frontend (js_api)

Lớp `JsApi` expose các hàm (pywebview gọi từ JS qua `window.pywebview.api`):

| Hàm | Vào | Ra |
|-----|-----|-----|
| `chon_file()` | – | mở hộp thoại chọn file, trả `{path, ten, ky, so_dong, tong_ps}` |
| `lay_file_moi_nhat()` | – | tự tìm file mới nhất trong `1. Source` |
| `chay_kiem_tra(path)` | đường dẫn | `{tomtat:{ky, so_dong, tong_ps, so_do, so_vang, san_sang}, trang_thai:[{buoc, trang_thai, tom_tat, ma_check}], nhom:[{ma, ten, so_loi, muc_do, checks:[{ma, ten, muc_do, so_loi}]}]}` |
| `lay_chi_tiet(ma_check, trang, tim_kiem, muc_do)` | mã check + phân trang/lọc | `{tong, dong:[{DocNo, DocDate, DebitAccount, CreditAccount, Amount, Description, ly_do}]}` — trả theo trang để UI không phải nhận 79k dòng một lúc |
| `xuat_bao_cao()` | – (dùng kết quả đã chạy) | `{path}` file Excel đã tạo |
| `mo_file(path)` | đường dẫn | mở file bằng ứng dụng mặc định (Excel) |
| `mo_thu_muc(path)` | đường dẫn | mở Explorer tại thư mục |

Dữ liệu truyền JSON. Kết quả lần chạy (kể cả DataFrame chi tiết từng check) lưu trong bộ nhớ backend; UI chỉ nhận tóm tắt, rồi gọi `lay_chi_tiet` theo trang khi người dùng click — tránh truyền hàng chục nghìn dòng qua bridge một lúc. Tiến trình chạy check báo về UI qua `window.evaluate_js` (callback `onTienTrinh(ten_check, pham_tram)`).

## 11. Xử lý lỗi

- File không đọc được / sai định dạng / thiếu cột bắt buộc → thông báo rõ trên UI, không crash.
- Cột số có giá trị lạ → ép 0 và ghi vào sheet "Nhật ký xử lý" trong báo cáo.
- `2. Report` chưa tồn tại → tự tạo.
- Không có file trong `1. Source` → hướng dẫn người dùng đặt file vào.

## 12. Giới hạn v1 & hướng mở rộng

**Giới hạn (do dữ liệu chỉ có phát sinh trong kỳ):**
- Không có **số dư đầu kỳ** → không kiểm được tồn kho âm tuyệt đối, số dư TK cuối kỳ tuyệt đối.
- Không có **hệ thống tài khoản chuẩn** → C2.2 chỉ kiểm định dạng, chưa đối chiếu danh mục.
- Không có **tờ khai thuế** → chỉ tổng hợp thuế nội bộ, chưa đối chiếu tờ khai.

**Mở rộng tương lai (đã chừa chỗ trong kiến trúc):**
- Nạp thêm file tham chiếu: `SoDuDauKy.xlsx`, `HeThongTaiKhoan.xlsx`, `ToKhaiThue.xlsx`.
- Đổi nguồn từ Excel sang đọc thẳng `vietxo_dwh` (SQL Server) — chỉ thay `loader.py`.
- Đóng gói `.exe` bằng PyInstaller.

## 13. Dependencies & chạy

`requirements.txt`: `pandas`, `openpyxl`, `xlsxwriter`, `pywebview`.
Đã có sẵn trên máy: pandas 3.0.2, openpyxl 3.1.5, xlsxwriter 3.2.9, pywebview 6.2.1.

Chạy: `Kiem_tra_khoa_so.bat` → `python app/main.py`.

## 14. Tiêu chí hoàn thành (acceptance)

1. Mở app, chọn file `Bang ke chung tu 082027.xlsx`, bấm Kiểm tra → chạy < 10 giây, không lỗi.
2. Sau khi bấm Kiểm tra, app **tự chuyển sang màn hình Kết quả** với banner kết luận; **Tab "Trạng thái khóa sổ"** hiện đủ 11 bước với trạng thái ✅/❌/⚠️/➖ đúng theo dữ liệu; **Tab "Lỗi & cảnh báo"** hiện 6 nhóm, click xem được bảng chi tiết có tìm kiếm/lọc/phân trang, không đơ với check có hàng chục nghìn dòng.
3. Xuất báo cáo Excel (tùy chọn) có sheet Tổng quan + sheet "Trạng thái khóa sổ" + các sheet chi tiết đúng định dạng; nút "Mở file Excel" / "Mở thư mục" hoạt động.
4. Các check ⭐ (giá vốn C4.x, kết chuyển C5.x) chạy đúng logic trên dữ liệu thật.
5. Giao diện Segoe UI, light mode, đúng bảng màu; chạy offline.
6. Mỗi module check có test riêng với dữ liệu mẫu nhỏ.
```
