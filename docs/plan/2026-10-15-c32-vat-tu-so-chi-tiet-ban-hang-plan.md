# Thuế GTGT từ Sổ chi tiết bán hàng — sửa C3.2, thêm C3.4 (521), lưu kho 3 nguồn

Ngày: 2026-10-15 (cập nhật lần 5: C3.4 làm cùng đợt; nhận sổ bán hàng đủ các chi nhánh; làm MỘT đợt, không chia phase) · Trạng thái: **ĐÃ CODE (1.3.0)** — kết quả & các chỗ lệch plan: `docs/ket-qua/thue-gtgt-so-chi-tiet-ban-hang.md`

## 1. Vấn đề

C3.2 hiện chạy trên **bảng kê chứng từ** ở mức **chứng từ**: một hóa đơn có Có 511 + mã thuế
chịu thuế mà *cả chứng từ* không có dòng 33311 thì bắt. Bảng kê không thể làm tốt hơn: dòng
33311 là **một dòng gộp, không mang ItemCode**, nên không biết thuế của dòng hàng nào.

Cách đúng (KTTH chốt): mở **Sổ chi tiết bán hàng** → lọc **Có 511** → đối ứng **Nợ 131** →
dòng nào **thuế = 0** là chưa nhập VAT. Sổ này có thuế **theo từng dòng hàng**.

## 2. Cấu trúc file sổ chi tiết bán hàng (đã soi A01 08 + 09/2026)

1 sheet `Table1`, 60 cột, header dòng 1, **không có BranchCode** → chi nhánh + kỳ lấy từ tên
file `So chi tiet ban hang A01 092026.xlsx` (mã CN đứng GIỮA tên, khác CĐPS đứng đầu).

| Cột | Nghĩa (đã kiểm bằng số) |
|---|---|
| `DebitAccount2` / `CreditAccount2` | TK đối ứng doanh thu (1311/51111…) |
| `Amount2` | **Doanh thu** = Quantity × UnitPrice (khớp 98,3%) |
| `Amount3` | **Thuế GTGT đầu ra** của dòng (`TotalAmount = Amount2 + Amount3` khớp 100%) |
| `Amount` | Giá vốn (= Quantity × UnitCost) — KHÔNG phải doanh thu |
| `TransCode`, `DocCode`, `DocNo`, `DocDate`, `CustomerCode/Name`, `ItemCode/Name`, `Quantity`, `UnitPrice` | như bảng kê |

**Khớp số với bảng kê 09/2026 (A01) tuyệt đối:** Σ doanh thu Nợ131/Có511 = **22.128.560.379**
cả hai bên; Σ thuế Nợ131/Có33311 (bảng kê) = Σ `Amount3` (sổ bán hàng) = **1.839.234.953**.
Sổ bán hàng thừa 88 dòng — toàn dòng **hàng tặng/khuyến mại giá 0** (`Amount2 = 0`).

## 3. Đo trên dữ liệu thật — check cũ sai ở đâu

| A01 | Check cũ (bảng kê) | Quy tắc mới (sổ bán hàng) |
|---|---|---|
| 09/2026 | 19 dòng · 11 CT · 42,06 tr | **31 dòng · 20 CT · 121,96 tr** |
| 08/2026 | 21 HĐ · 371 tr (memory 21/09) | **131 dòng · 58 CT · 488 tr** |

09/2026: mới ⊇ cũ (11 CT trùng, cũ không có CT nào mà mới thiếu). 9 CT check cũ **bỏ lọt**,
do hai nguyên nhân gốc:

1. **Chứng từ "thuế một phần" (5 CT, 5 dòng):** hóa đơn có dòng 33311 nhưng vài dòng hàng
   thuế = 0 → check mức chứng từ cho qua. Vd `0051998`: 3 dòng hàng, 2 có thuế, dòng
   `H101PK0000072` 1.386.000 không thuế. Cùng loại: `0051113`, `0051551`, `0051566`, `0051976`.
2. **Dòng không gắn TaxCode (4 CT, 6 dòng, 74,4 tr — khách FOD):** check cũ đòi
   `TaxCode` chịu thuế mới xét → dòng để trống mã thuế (chính là quên nhập VAT) bị loại.
   `0052763`, `0053483`, `0053678`, `0054063`.

Phân bố 31 dòng 09/2026: **30 dòng TransCode 2304** (khách Thép Việt Xô & các CN, Vhome,
FOD), 1 dòng 2301. Theo chốt 21/09 của KTTH: ngoài 2303/2110, thiếu thuế = thiếu thật.

**Danh mục loại giao dịch** (`1. Source/Danh mục loại giao dịch.xlsx`) xác nhận luật này:

| Mã | Tên trong danh mục | Pháp nhân | Phải có VAT |
|---|---|---|---|
| 2301 / 2305 / 2306 | Bán hàng công nợ khách hàng (chung / Hải Phòng / Nghệ An) | khác | có |
| **2304** | Bán hàng công nợ **Công ty nội bộ** | **khác** (công ty trong nhóm) | **có** |
| 2303 | Bán hàng công nợ **Chi nhánh** | cùng | không |
| 2307 | Bán hàng công nợ Chi nhánh – Kho trung gian | cùng | không |
| 2107 | Nhập lại hàng bán trả lại khách hàng | khác | có |
| **2112** | Nhập lại hàng bán trả lại **Công ty nội bộ** | **khác** | **có** |
| 2110 | Nhập lại hàng bán trả lại **Chi nhánh** | cùng | không |

⇒ "nội bộ" theo nghĩa thuế = **Chi nhánh** (cùng pháp nhân), KHÔNG phải "Công ty nội bộ".
**2307** cũng là chi nhánh nhưng chưa nằm trong `TRANSCODE_NOI_BO`: ở A01 nó chỉ đi Nợ
1368/Có 13882 (không chạm 511) nên vô hại. Khi có đủ chi nhánh mà 2307 xuất hiện ở Nợ 131/Có
511 → hỏi KTTH thêm vào danh sách (§11), không tự thêm.

## 4. Quy tắc mới (C3.2 khi có sổ bán hàng)

Bắt dòng thỏa **tất cả**:
- `CreditAccount2` bắt đầu `511` **và** `DebitAccount2` bắt đầu `131`
- `Amount3 == 0`
- `Amount2 != 0` — loại hàng tặng/KM giá 0 (không có doanh thu thì không có thuế để thiếu)
- `TransCode` ∉ `TRANSCODE_NOI_BO` (2303/2110) — giữ lá chắn cũ: memory 21/09 ghi có 6 dòng
  nội bộ hạch toán qua 1311/1388, lọc Nợ 131 thôi chưa đủ. Bán nội bộ Nợ 1368/Có 511 tự rơi
  khỏi diện vì không phải Nợ 131.

Chi tiết xuất **từng dòng hàng**: DocNo, DocDate, TransCode, Khách hàng, Mã hàng, SL, Đơn
giá, Doanh thu (`Amount2`), Thuế (`Amount3`). Mức độ giữ **VANG** như cũ.

Ngoài phạm vi (không làm): thuế ≠ 0 nhưng lệch thuế suất (vài dòng tỷ lệ 0,188/0,115) —
làm khi KTTH yêu cầu.

## 4b. Check MỚI C3.4 — Hàng bán trả lại chưa điều chỉnh thuế (Nợ 521 / Có 131)

Cách KTTH: sổ chi tiết bán hàng → lọc **cột AM `DebitAccount2` = 521**, **đối ứng
`CreditAccount2` = 131** → dòng nào **`Amount3 = 0`** kéo hết ra (khách trả lại mà không giảm
thuế đầu ra tương ứng). Đối xứng với C3.2 (Nợ 131/Có 511).

Đo thật (sổ bán hàng chỉ chứa **5213 hàng bán trả lại**; giảm giá 5212 không có trong sổ này):

| Cặp TK trong sổ 09/2026 | TransCode | Dòng | Thuế 0 | Vào diện C3.4? |
|---|---|---|---|---|
| 52131 / 1311 | 2107 | 268 | 6 | **có** |
| 52132 / 1311 | 2112 | 9 | 0 | **có** |
| 52133 / 1368 | 2110 (nội bộ) | 26 | 26 | không — đối ứng 1368, không phải 131 |

| A01 | C3.4 (Nợ 521 / Có 131, thuế 0) |
|---|---|
| 09/2026 | **6 dòng · 1 CT · −6.810.000** (`NM2609-000806`, Tiến Viên — trả lại do đặt thừa) |
| 08/2026 | **20 dòng · 10 CT · −32.676.776** (vd `NM2608-001234` Vhome 7 dòng, `NM2608-000847` −10,4 tr) |

Lọc đối ứng 131 tự loại trả lại nội bộ 52133/1368. Vẫn giữ điều kiện `TransCode` ∉ nội bộ
(2303/2110) như C3.2 — phòng nội bộ hạch toán qua 1311 (đã gặp ở C3.2, memory 21/09); hiện
không khớp dòng nào nên không đổi số. Không CT nào trong diện có thuế một phần.

Bắt dòng thỏa: `DebitAccount2` bắt đầu `521` · `CreditAccount2` bắt đầu `131` ·
`Amount3 == 0` · `Amount2 != 0` · `TransCode` ∉ nội bộ. Dùng chung một hàm lọc với C3.2
(chỉ khác mặt nạ TK). Chi tiết từng dòng như C3.2 + lý do trả lại (`Description`). Mức
**VANG**, nhóm G3 → tổng check 59 → **60**.

Khớp số 09/2026: Σ Nợ 521/Có 131 sổ bán hàng **256.320.362** = bảng kê Nợ 52131+52132 / Có
1311; Σ thuế **20.865.579** = bảng kê Nợ 33311/Có 131.

## 5. Đầu vào: 3 nguồn, cả 3 lưu vào kho SQLite

Hiện tại: **CĐPS** lưu kho ngay khi nạp (bảng `cdps`, sống, ghi đè theo chi nhánh × kỳ);
**bảng kê** chỉ đọc từ file, chỉ vào kho khi **chốt sổ** (`snapshot_du_lieu`, đóng băng).

Mới: **sổ bán hàng** và **bảng kê** cũng lưu kho ngay khi nạp, giống CĐPS. Lợi ích:
- Mở app là **kiểm tra lại được ngay từ kho**, không phải chọn lại file 30 MB.
- Trạng thái "đã nạp / chưa nạp" **đồng nhất cho 3 nguồn** theo (chi nhánh × kỳ).
- Có `thoi_diem_nap` + `mtime_file` của cả 3 → lá chắn độ tươi (§7) so được mọi cặp.
- Chốt sổ đóng băng **đủ 3 nguồn**.

**Dung lượng (đo thật, gzip JSON như `snapshot_du_lieu`):** bảng kê A01 09/2026 79.284 dòng
→ **3,9 MB** (nén 1,4 s); sổ bán hàng 18.359 dòng → **1,7 MB** (0,4 s). A01 là chi nhánh
lớn nhất ⇒ trần ~**5,6 MB / chi nhánh / tháng**, 8 chi nhánh × 12 tháng ≲ **540 MB/năm**.
Chấp nhận được với SQLite; bản sao lưu lớn theo — ghi rõ ở màn Cài đặt.

### Schema v5 (`app/kho/schema.py`, `PHIEN_BAN_SCHEMA = 5`)

```sql
-- Nguồn SỐNG: một dòng = một (loại × chi nhánh × kỳ); nạp lại = thay sạch.
CREATE TABLE IF NOT EXISTS nguon (
    loai TEXT NOT NULL,              -- 'bang_ke' | 'so_ban_hang'
    chi_nhanh TEXT NOT NULL, ky_nam INTEGER NOT NULL, ky_thang INTEGER NOT NULL,
    du_lieu BLOB NOT NULL,           -- _nen(df): gzip JSON orient="table"
    so_dong INTEGER NOT NULL, van_tay TEXT NOT NULL,
    ten_file TEXT, mtime_file TEXT, thoi_diem_nap TEXT NOT NULL,
    PRIMARY KEY (loai, chi_nhanh, ky_nam, ky_thang)
);
-- Đóng băng sổ bán hàng lúc chốt (bảng kê đã có snapshot_du_lieu).
CREATE TABLE IF NOT EXISTS snapshot_so_ban_hang (
    snapshot_id INTEGER PRIMARY KEY REFERENCES snapshot(id), du_lieu BLOB NOT NULL
);
```
Một bảng `nguon` chung cho 2 loại (cùng dạng BLOB) thay vì 2 bảng. **CĐPS giữ nguyên bảng
`cdps`** (dạng cột, đang được truy vấn SQL theo TK — không dời). Migration v4→v5 chỉ là
`CREATE IF NOT EXISTS`; app cũ mở kho v5 → `PhienBanMoiHon` như cơ chế sẵn có.

`KhoChotSo` thêm: `luu_nguon(loai, cn, nam, thang, df, ten_file, mtime)`,
`doc_nguon(loai, cn, nam, thang) -> df | None`, `co_nguon(...)`, `trang_thai_nguon(loai)`,
`so_sanh_nguon(...)` (theo `van_tay` — trùng thì chỉ chạm `thoi_diem_nap` như
`xac_nhan_cdps`, cùng lý do: không để cảnh báo độ tươi kêu oan). `luu_snapshot` chép thêm
sổ bán hàng sống vào `snapshot_so_ban_hang` (thiếu thì không ghi — "chưa có mốc" ≠ "không đổi").

### Màn nạp (`ui/src/ChonFile.tsx`): 3 bước

| Bước | Nguồn | Cách nạp | Bắt buộc |
|---|---|---|---|
| 1 | CĐPS | thư mục (như hiện tại) | chặn cứng (như hiện tại) |
| 2 | **Sổ chi tiết bán hàng** — MỚI | thư mục, xem trước + chọn kỳ ghi đè (dùng lại khuôn `xem_truoc_cdps`/`nap_cdps_thu_muc`) | **chặn cứng** cho chi nhánh có dòng Nợ 131/Có 511 hoặc Nợ 5213/Có 131 |
| 3 | Bảng kê chứng từ | chọn file / thư mục như hiện tại, **nay ghi luôn vào kho** | — |

Nút **Kiểm tra** dùng kho làm nguồn; thêm lối **"Kiểm tra từ kho"**: chọn (chi nhánh × kỳ)
đã có đủ nguồn, khỏi chọn lại file.

**Chặn cứng có ngoại lệ dựa trên bằng chứng:** chi nhánh mà bảng kê **không có dòng Nợ
131/Có 511 lẫn Nợ 5213/Có 131 nào** (vd văn phòng HO không bán hàng) thì không đòi sổ bán hàng — đòi là chặn
vĩnh viễn một chi nhánh không có gì để nộp. Ký hiệu trạng thái mỗi chi nhánh: **✓ đã nạp ·
✕ thiếu · – không cần** (không chỉ bằng màu).

Vì sổ bán hàng là bắt buộc, **bỏ đường fallback bảng kê của C3.2** (bản plan lần 1 §5):
code C3.2 cũ trên bảng kê được thay hẳn, không giữ hai đường song song.

### Bảng kê vào kho đổi gì ở luồng hiện tại

- `_nap_nhieu`: đọc xong, tách theo chi nhánh → `luu_nguon('bang_ke', …)` từng phần. Một
  file nhiều chi nhánh / một chi nhánh nhiều file vẫn theo `doc_nhieu_bang_ke` như cũ.
- `DonVi` dựng từ kho (`doc_nguon`) thay vì từ frame vừa đọc — một đường duy nhất cho cả
  "vừa nạp" lẫn "kiểm tra từ kho".
- **Drift sau chốt:** nay so `van_tay` của bảng kê **sống trong kho** với snapshot. Bỏ cơ chế
  `chay_kiem_tra` tự đọc lại file khi kỳ đã chốt (`_co_don_vi_da_chot`) — muốn cập nhật thì
  nạp lại file (Bước 3), giống CĐPS. Một nguồn sự thật cho mỗi kỳ = kho (mặc định đã chọn, §9).
- `api.cdps_cu()` (CĐPS cũ hơn bảng kê) chuyển sang so `thoi_diem_nap`/`mtime_file` trong kho.


## 6. C3.2 / C3.4 đọc gì

`BoiCanh.so_ban_hang: pd.DataFrame | None` (`app/checks/base.py`), bơm ở chỗ dựng
`BoiCanh(...)` trong `api.py` (~dòng 384) từ `doc_nguon('so_ban_hang', …)`. `None` chỉ xảy ra
ở chi nhánh "không cần" (§5) → C3.2/C3.4 ra 0 dòng kèm `ghi_chu` "Không có bán hàng / trả lại
trong kỳ".

## 7. Lá chắn độ tươi (bài học CĐPS 21/09)

Khi có cả sổ bán hàng và bảng kê, so 4 tổng (đều đã khớp tuyệt đối trên A01 09/2026):
- Doanh thu: Σ `Amount2` (Nợ131/Có511) vs bảng kê Nợ131/Có511
- Thuế ra: Σ `Amount3` (Nợ131/Có511) vs bảng kê Nợ131/Có33311
- Trả lại: −Σ `Amount2` (Nợ521/Có131) vs bảng kê Nợ5213/Có131
- Thuế trả lại: −Σ `Amount3` (Nợ521/Có131) vs bảng kê Nợ33311/Có131

Lệch > 1đ → C3.2/C3.4 vẫn chạy trên sổ bán hàng nhưng `ghi_chu` cảnh báo *"Sổ bán hàng lệch
bảng kê X đ — kết xuất lại cùng thời điểm"*. Dải vàng ở màn nạp nếu `mtime_file` hai nguồn
cách nhau > 1 ngày (không chặn).

## 8. Các bước thực hiện (một đợt)

1. `app/so_ban_hang.py` (khuôn `app/cdps.py`): `doc_so_ban_hang(path) -> (df, meta)`; regex
   tên file **tìm ở bất kỳ đâu** `\b([A-Za-z]+\d+)\s+(\d{2})(\d{4})\b`; cột bắt buộc `DocNo,
   DocCode, DocDate, TransCode, DebitAccount2, CreditAccount2, Amount2, Amount3`; ép số;
   kỳ tên file ≠ tháng phổ biến `DocDate` → ném `KhongPhaiSoBanHang`.
2. Schema v5: bảng `nguon` + `snapshot_so_ban_hang`; `KhoChotSo.*_nguon`; `luu_snapshot`
   đóng băng thêm sổ bán hàng (§5).
3. `api` sổ bán hàng: `xem_truoc_so_ban_hang`, `nap_so_ban_hang_thu_muc`,
   `thieu_so_ban_hang`, `trang_thai_so_ban_hang` — tham số hóa phần dùng chung với CĐPS
   thay vì chép.
4. `api` bảng kê vào kho: ghi `nguon('bang_ke')` khi nạp; `DonVi` dựng từ kho; lối "Kiểm
   tra từ kho"; drift so kho ↔ snapshot, bỏ đọc-lại-file; `cdps_cu` theo dấu thời gian kho.
5. `g3_thue_gtgt.py`: một hàm lọc chung `_dong_thue_0(sbh, mat_na_tk)`; C3.2 viết lại theo
   §4, **C3.4 mới** theo §4b; phép so 4 tổng §7. Bỏ code C3.2 cũ trên bảng kê.
6. Sao lưu/phục hồi/nhập-gộp (`app/kho/sao_luu.py`) mang theo `nguon` +
   `snapshot_so_ban_hang`; `tom_tat_kho` đếm thêm kỳ có sổ bán hàng/bảng kê.
7. UI (`ChonFile.tsx`): 3 bước, Bước 2 sổ bán hàng + chặn cứng có ngoại lệ, ký hiệu
   ✓ ✕ –; lối "Kiểm tra từ kho"; Cài đặt ghi dung lượng kho. Build `ui`.
8. Báo cáo Excel / màn kết quả: C3.4 tự hiện như check thường (không cần sửa riêng) — kiểm lại.

**Test** (DataFrame tự dựng; **mọi test qua `JsApi` ép `_thu_muc_kho` vào `tmp_path`**):
- C3.2: CT thuế một phần → bắt đúng dòng thuế 0; dòng không TaxCode thuế 0 → bắt; KM
  `Amount2 = 0` → không; TransCode 2303 qua 1311 → không; Nợ 1368/Có 511 → không.
- C3.4: Nợ 52131/Có 1311 thuế 0 → bắt; có thuế → không; Nợ 52133/Có 1368 thuế 0 → không
  (đối ứng không phải 131); Nợ 5213/Có 1311 TransCode 2303 → không; Có 511 thuế 0 →
  không lọt sang C3.4.
- Độ tươi: lệch một trong 4 tổng > 1đ → có `ghi_chu`; khớp → không.
- Parser: mã CN giữa tên file; thiếu cột; kỳ tên file ≠ DocDate.
- Kho: `luu_nguon` → `doc_nguon` round-trip không trôi dtype (DocNo "0051998" giữ số 0);
  nạp lại cùng `van_tay` → chỉ chạm thời điểm; chốt sổ đóng băng sổ bán hàng; migration
  v4→v5 trên kho v4 có sẵn snapshot không mất gì; sao lưu/phục hồi giữ bảng mới.
- Chặn cứng: chi nhánh có Nợ131/Có511 hoặc Nợ5213/Có131 mà thiếu sổ → chặn; không có → không chặn.
- Drift: kỳ đã chốt, nạp bảng kê khác → LỆCH; nạp lại y hệt → KHỚP.

**Kiểm trên file thật** (`1. Source/SO CHI TIET BAN HANG/`):
- C3.2: 09/2026 → 31 dòng / 20 CT / 121.957.260; 08/2026 → 131 dòng / 58 CT / 487.978.969.
- C3.4: 09/2026 → 6 dòng / 1 CT / −6.810.000; 08/2026 → 20 dòng / 10 CT / −32.676.776.
- 4 tổng §7 khớp bảng kê 09/2026.

Ghi kết quả `docs/ket-qua/`. Cuối: `pytest -W error`, build UI, nâng `VERSION`, cập nhật
memory (tổng check 60).

## 9. Quyết định đã chọn mặc định (đổi được, mỗi cái một dòng code)

- **Drift sau chốt theo kho**, bỏ tự đọc lại file bảng kê — một nguồn sự thật cho mỗi kỳ.

## 10. Để lại

- Giảm giá hàng bán 5212 (không có trong sổ bán hàng) và thuế lệch thuế suất — chưa làm.
- Xóa nguồn cũ trong kho (dọn kỳ xa) — thêm khi kho thực sự lớn.

## 11. Dữ liệu đủ các chi nhánh (người dùng đang xuất)

**Quy ước nhận file** — để parser (§8 bước 1) đọc thẳng, không đổi tên tay:
- Tên: `So chi tiet ban hang <MÃ CN> <MMYYYY>.xlsx` (vd `So chi tiet ban hang A05 092026.xlsx`).
- Để ở `1. Source/SO CHI TIET BAN HANG/` (git-ignored). Cùng mẫu báo cáo Bravo như A01 (60 cột,
  sheet `Table1`) — khác mẫu thì parser báo thiếu cột, không đoán.
- **Xuất cùng lúc với bảng kê chứng từ của kỳ đó** (bài học độ tươi 21/09) — nếu không, 4
  tổng §7 lệch và C3.2/C3.4 mang cảnh báo.
- Chi nhánh không bán hàng trong kỳ: không cần file (ngoại lệ chặn cứng §5).

**Khi file về — kiểm trước, rồi mới coi là xong** (bảng ghi vào `docs/ket-qua/`):

| Kiểm | Đạt khi |
|---|---|
| Cấu trúc | mọi file đúng 60 cột như A01; suy được mã CN + kỳ từ tên |
| 4 tổng §7 vs bảng kê/CĐPS | lệch ≤ 1đ từng chi nhánh (mốc tham khảo: 511 bảng kê vs CĐPS khớp 8/8 CN ngày 21/09) |
| TransCode lạ | liệt kê mã ở Nợ131/Có511 và Nợ521/Có131 ngoài 2301/2304/2305/2306/2107/2112 → hỏi KTTH |
| 2307 ở Nợ131/Có511 | có thì hỏi KTTH thêm vào nội bộ |
| C3.2 / C3.4 | bảng số dòng · số CT · tiền theo chi nhánh × kỳ; soi tay vài CT lớn nhất mỗi CN |
| Ground truth 21/09 | A03, A04 phải không có lỗi thật mới bất ngờ; có thì soi trước khi tin |

**Thứ tự làm:** code ngay toàn bộ plan với mẫu A01 (08 + 09) làm dữ liệu kiểm; file các chi
nhánh về thì chạy bảng kiểm trên — không chờ file mới bắt đầu.

