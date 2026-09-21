# Spec: Kiểm soát thay đổi từ khi chốt sổ

- Ngày: 2026-09-18
- Trạng thái: **ĐÃ HIỆN THỰC** 2026-09-21, commit `3fb3878` (một sai sót thiết kế phát
  hiện lúc code — xem §4.1)
- Liên quan: [chốt sổ & đối chiếu kỳ](2026-09-16-kho-chot-so-va-doi-chieu-ky-design.md),
  [nhập & đối chiếu CĐPS](2026-09-17-cdps-nhap-doi-chieu-design.md)

## 1. Mục tiêu

Cho phép kế toán **dò ra bút toán và chỉ số bị thay đổi so với bản đã chốt** trong
database, để kiểm soát các bút toán phát sinh sau khi đã khóa sổ một kỳ.

Bốn kết quả người dùng cần:

1. **Bút toán bị SỬA** trên bảng kê chứng từ — không chỉ thêm/bớt dòng như hiện tại.
2. **CĐPS đối chiếu với bản CHỐT** thường trực (không chỉ lúc nạp lại file).
3. Một **màn gộp "Thay đổi từ khi chốt"** liệt kê mọi thay đổi ở một nơi.
4. **Xuất Excel** danh sách thay đổi làm bằng chứng kiểm soát.

## 2. Bối cảnh hiện trạng (đã có trên main)

| Nguồn | Cơ chế | Mức chi tiết |
|---|---|---|
| Bảng kê vs bản CHỐT | `chot_so.doi_chieu` + `dien_diff`; UI `lay_diff_chot` | **Chỉ THÊM / BỚT dòng** — chứng từ bị sửa hiện thành 1 bớt + 1 thêm |
| CĐPS vs bản đang lưu | `luu_tru.so_sanh_cdps` (chạy khi nạp lại, trước khi ghi đè) | THÊM / MẤT / **ĐỔI** theo TK, kèm cũ→mới, cột lệch |
| Bảng kê ↔ CĐPS cùng kỳ | C9.5 | Đã có |
| Kỳ này vs kỳ trước | G11 (C11.1–C11.4) | Đã có |

Hai điểm nền tảng:

- **Bảng kê được đóng băng khi chốt** (`snapshot` + `snapshot_du_lieu` BLOB gzip JSON,
  `orient="table"`). `chot_so()` → `kho.luu_snapshot(..., df=d.df, ...)`.
- **CĐPS KHÔNG được đóng băng.** Bảng `cdps` là bảng sống keyed theo
  `(chi_nhanh, ky_nam, ky_thang)`, ghi đè sạch khi nạp lại. `so_sanh_cdps` so
  *bản mới vs bản đang lưu* — không gắn với sự kiện chốt.
- Bảng kê chỉ có khóa **DocCode+DocNo** (định danh chứng từ), **không có STT dòng**
  trong một chứng từ.

## 3. Quyết định thiết kế (đã chốt với người dùng)

- **D1.** Mốc "bản chốt CĐPS" = **đóng băng CĐPS ngay khi chốt sổ** (schema v4).
- **D2.** Phát hiện bút toán sửa ở **mức chứng từ + liệt kê dòng lệch** (tái dùng băm
  dòng sẵn có). KHÔNG so từng ô (bảng kê không có STT dòng → đoán cặp dễ sai).
- **D3.** Màn gộp: **theo chi nhánh đang xem** làm mặc định + nút **"Xem tất cả chi
  nhánh"** (một bảng, thêm cột Chi nhánh).
- **D4.** Chỉ đối chiếu với **snapshot đang hiệu lực** (`con_hieu_luc=1`); kho vẫn
  append-only, bản cũ xem ở Lịch sử.

## 4. Kiến trúc — tái dùng trước

```
Chốt sổ ─► đóng băng BẢNG KÊ (đã có) + CĐPS (mới) vào snapshot
Kiểm tra lại kỳ đã chốt ─► api.thay_doi_tu_khi_chot(pham_vi)
      ├─ Bảng kê: chot_so.dien_diff_ct(df_chốt, df_hiện) → THÊM / BỚT / SỬA chứng từ
      └─ CĐPS:    cdps.so_sanh(cdps_đóng_băng, cdps_sống) → THÊM / MẤT / ĐỔI tài khoản
   ─► Màn "Thay đổi từ khi chốt" ─► Xuất Excel
```

### 4.1 Logic thuần — `app/chot_so.py`

Thêm hàm mới, **giữ nguyên** `dien_diff` cũ (và `lay_diff_chot` không vỡ):

```python
def dien_diff_ct(df_chot, df_hien_tai) -> dict:
    """Phân loại thay đổi theo CHỨNG TỪ: thêm / bớt / sửa."""
    d = dien_diff(df_chot, df_hien_tai)              # tái dùng: dòng thêm/bớt (hiệu đa tập)
    ct_them, ct_bot = set(_so_ct(d["them"])), set(_so_ct(d["bot"]))
    ct_sua = {c for c in ct_them & ct_bot if c and c != "·"}
    sua = [{"so_ct": c,
            "dong_cu":  d["bot"][_so_ct(d["bot"]) == c].reset_index(drop=True),
            "dong_moi": d["them"][_so_ct(d["them"]) == c].reset_index(drop=True)}
           for c in sorted(ct_sua)]
    them = d["them"][~_so_ct(d["them"]).isin(ct_sua)].reset_index(drop=True)   # chỉ thêm
    bot  = d["bot"][~_so_ct(d["bot"]).isin(ct_sua)].reset_index(drop=True)     # chỉ bớt
    tom_tat = {"ct_them": int(_so_ct(them).nunique()),
               "ct_bot": int(_so_ct(bot).nunique()),
               "ct_sua": len(ct_sua)}
    return {"them": them, "bot": bot, "sua": sua, "tom_tat": tom_tat}
```

"Dòng cũ/mới" của một chứng từ SỬA là **các dòng lệch** (hiệu đa tập) trong chứng từ
đó — đúng chỗ kế toán cần soi; không đoán cặp từng ô nên không sai cặp.

> **SỬA LÚC HIỆN THỰC (2026-09-21).** Đoạn mã trên SAI ở một ca: nó lấy giao của hai
> phía DIFF (`ct_them & ct_bot`), nên chứng từ **chỉ được THÊM một dòng** (không bớt
> dòng nào) chỉ xuất hiện ở phía "thêm" và bị xếp nhầm thành *chứng từ mới*, trong khi
> nó vẫn có mặt trong bản chốt — đó là chứng từ **bị sửa**.
>
> Phải xét sự tồn tại trên **FRAME ĐẦY ĐỦ**, không trên kết quả diff:
> ```python
> co_o_chot, co_o_moi = set(_so_ct(df_chot)), set(_so_ct(df_hien_tai))
> chung = {c for c in set(ct_them) | set(ct_bot)          # HỢP, không phải GIAO
>          if c and c != "·" and c in co_o_chot and c in co_o_moi}
> ```
> Test `test_dien_diff_ct_them_bot_dong_trong_cung_chung_tu` khóa đúng ca này lại.

### 4.2 Logic thuần — CĐPS `app/cdps.py`

Rút ruột `luu_tru.so_sanh_cdps` thành **hàm thuần 2 DataFrame** (giữ cộng gộp mã TK
lặp — bug `64dbbf9`):

```python
def so_sanh(df_cu, df_moi, nguong=0.5) -> dict | None:
    """Diff 2 CĐPS theo mã TK: thêm / mất / đổi (cũ→mới, cột lệch). None nếu y hệt/rỗng."""
```

`luu_tru.so_sanh_cdps` gọi lại hàm này (đường nạp-lại giữ nguyên hành vi). Đường "vs
chốt" đọc CĐPS đóng băng rồi gọi **cùng** hàm.

### 4.3 Kho / schema — `schema.py`, `ket_noi.py`, `luu_tru.py`

- `PHIEN_BAN_SCHEMA = 4`. DDL mới:
  ```sql
  CREATE TABLE IF NOT EXISTS snapshot_cdps (
      snapshot_id INTEGER PRIMARY KEY REFERENCES snapshot(id),
      du_lieu BLOB NOT NULL);
  ```
- Migration v3→v4: tạo bảng. Snapshot cũ không có bản CĐPS đóng băng (xử lý ở §7).
- `luu_snapshot(...)`: sau khi ghi `snapshot_du_lieu`, đọc `cdps` của đúng
  `(chi_nhanh, ky_nam, ky_thang)`; có dữ liệu → `_nen(df_cdps)` vào `snapshot_cdps`
  (dùng lại đúng cơ chế nén BLOB của bảng kê). Không có CĐPS → bỏ qua (không đóng băng).
- Reader mới `doc_cdps_snapshot(snapshot_id) -> DataFrame` (rỗng nếu chưa có).

### 4.4 API — `app/api.py`

```python
def thay_doi_tu_khi_chot(self, pham_vi="dang_xem"):
    """pham_vi: 'dang_xem' (chi nhánh đang chọn) | 'tat_ca' (duyệt self._dv)."""
```

> **BỎ PHÂN TRANG so với bản thiết kế (2026-09-21).** Spec ban đầu có
> `trang/kich_thuoc/tim_kiem` theo mẫu `lay_diff_chot`. Không dùng được: payload ở đây
> **lồng theo chi nhánh** (mỗi chi nhánh có 3 nhóm chứng từ + danh sách CĐPS, riêng
> nhóm SỬA còn lồng thêm dòng cũ/mới), phân trang phẳng sẽ cắt ngang giữa một chứng từ.
> Mà số thay đổi kể từ khi chốt vốn phải NHỎ — nếu lớn tới mức cần phân trang thì bản
> chốt đã mất ý nghĩa, và con số tóm tắt ở đầu màn mới là thứ đáng nhìn. Cần lọc sâu
> thì xuất Excel (§4.6).

Với mỗi `DonVi` trong phạm vi có snapshot hiệu lực (`kho.doc_hieu_luc`):

- Bảng kê: `chot_so.dien_diff_ct(kho.doc_du_lieu(h["id"]), d.df)`.
- CĐPS: `cdps.so_sanh(kho.doc_cdps_snapshot(h["id"]), kho.doc_cdps(d.nhan, ...))`.

Trả về payload cho UI: tóm tắt đếm + danh sách phân trang (mode `tat_ca` thêm khóa
`chi_nhanh`/`chi_nhanh_ten` mỗi dòng). Kỳ chưa chốt → báo rõ "Kỳ này chưa chốt".
`co_cdps_chot=False` khi snapshot cũ không có CĐPS đóng băng.

### 4.5 UI — React (`ui/src/`, build vào `app/webapp`)

- Mục header mới **"Thay đổi từ khi chốt"** (cạnh "Cân đối phát sinh").
- Hai khối:
  - **Chứng từ**: Thêm / Bớt / Sửa (bung xem dòng cũ↔mới).
  - **CĐPS**: Đổi (cột nào, cũ→mới) / Thêm / Mất.
- Nút chuyển **"Chi nhánh đang xem" ↔ "Tất cả chi nhánh"**.
- **Mù màu**: phân biệt bằng ký hiệu **＋ Thêm · － Bớt · ✎ Sửa** kèm nhãn chữ, KHÔNG
  chỉ bằng màu (theo bộ nhớ `nguoi-dung-mu-mau`).
- Tái dùng component bảng/diff của màn `lay_diff_chot`.
- UI không tự test được (pywebview GUI) → cần người dùng kiểm mắt thường; backend test đầy đủ.

### 4.6 Excel — `app/report.py`

`xuat_thay_doi(...) -> path`, 2 sheet:
- **"Chứng từ thay đổi"**: Loại (Thêm/Bớt/Sửa), Chi nhánh, DocCode, DocNo, và với Sửa
  là các dòng cũ/mới.
- **"CĐPS thay đổi"**: Chi nhánh, TK, Loại (Thêm/Mất/Đổi), cột lệch, giá trị cũ, mới.

Nút "Xuất Excel" trên màn mới.

## 5. Đơn vị tách bạch

- `chot_so.dien_diff_ct` — thuần, không chạm DB/UI; input 2 DataFrame, output dict.
- `cdps.so_sanh` — thuần, không chạm DB/UI.
- `luu_tru` — chỉ đọc/ghi SQLite (đóng băng + đọc CĐPS snapshot).
- `api.thay_doi_tu_khi_chot` — cầu nối, ghép 2 hàm thuần + kho, trả payload.
- `report.xuat_thay_doi` — chỉ dựng Excel từ payload.

## 6. Test (pytest -W error)

- `dien_diff_ct`: thêm-thuần / bớt-thuần / **sửa** (chứng từ ở cả 2 phía, đổi 1 dòng) /
  chứng từ nhiều dòng / rỗng.
- `cdps.so_sanh`: đổi / thêm / mất / y hệt (None) / **mã TK lặp** (chặn tái phát `64dbbf9`).
- Kho: migrate v3→v4 (db cũ mở được, có bảng mới); `luu_snapshot` đóng băng CĐPS;
  `doc_cdps_snapshot` round-trip giữ dtype; snapshot cũ → CĐPS rỗng.
- API: happy path (`dang_xem`) / `tat_ca` nhiều chi nhánh / chưa chốt / snapshot cũ
  không có CĐPS (`co_cdps_chot=False`).

## 7. Biên & luật bằng chứng

- **Snapshot cũ (v3) không có CĐPS đóng băng** → khối CĐPS hiện "Bản chốt này chưa lưu
  CĐPS (chốt trước bản cập nhật)", **KHÔNG** báo lệch — theo luật *không cảnh báo từ thứ
  không có bằng chứng* (bộ nhớ `tool-kiem-tra-khoa-so-suc-manh-bang-chung`).
- Ngưỡng lệch tiền CĐPS **0.5** giữ nguyên; mã TK lặp → cộng gộp.
- Chứng từ có DocCode+DocNo rỗng (`·`) không tính vào SỬA.
- Tương thích ngược: `dien_diff` + `lay_diff_chot` không đổi hành vi.
- Kho append-only + auto-backup khi phục hồi (đã có).

## 8. Ngoài phạm vi (làm sau nếu cần)

- So từng ô ba chiều với đoán cặp dòng trong chứng từ (D2 đã chọn mức dòng).
- Bảng change_log lịch sử nhiều mốc (Hướng B — YAGNI).
- Đóng băng lại CĐPS cho các snapshot cũ (không có dữ liệu gốc lúc đó).
