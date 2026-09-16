# SPEC — Kho Chốt Sổ & Đối Chiếu Theo Kỳ

- **Ngày:** 2026-09-16
- **Trạng thái:** Draft để duyệt
- **Bối cảnh:** Mở rộng "Tool Kiểm Tra Khóa Sổ Cuối Kỳ" (xem `docs/spec/2026-09-15-tool-kiem-tra-khoa-so-design.md`)
- **Chế độ kế toán:** Thông tư 200 · **Ngành:** Sản xuất (Việt Xô) · **Kỳ:** Khóa sổ tháng · **Đa chi nhánh**

---

## 1. Vấn đề & mục tiêu

Tool hiện **không lưu trạng thái**: mỗi lần chạy đọc lại file Bravo, kiểm tra, rồi quên. Rủi ro: **một tháng đã khóa bị sửa về sau mà không có gì để đối chiếu**.

Mục tiêu đợt này:

1. **Chốt sổ từng kỳ** — người dùng chủ động "đóng băng" số liệu của một cặp *(chi nhánh × kỳ)* sau khi kiểm tra xong.
2. **Kho dữ liệu nhỏ (mini data warehouse)** — gom mọi kỳ đã chốt vào **một file SQLite** để lưu lịch sử và **truy vấn chéo kỳ**.
3. **Đối chiếu tự động** — khi mở lại một kỳ đã chốt, phát hiện dữ liệu nguồn có bị đổi so với bản đã chốt hay không, và **chỉ ra chỗ đổi**.
4. **Giao diện chốt sổ + xác nhận cập nhật** đẹp, thông minh, đồng bộ hệ "Premium Light".
5. **Sao lưu/di chuyển cực đơn giản** — copy một file là xong, cài máy khác dùng ngay.

**Nguyên tắc bất di bất dịch (kế thừa):** *chỉ cảnh báo khi có bằng chứng.* Cảnh báo "dữ liệu đã đổi" **chỉ** bật khi kỳ đó **đã có snapshot** — không suy diễn từ sự vắng mặt.

## 2. Quyết định thiết kế (đã chốt)

| # | Quyết định | Chọn |
|---|---|---|
| 1 | Đơn vị chốt | **(chi nhánh × kỳ)** — mỗi cặp chốt riêng |
| 2 | Nội dung snapshot | Vân tay + kết luận + **toàn bộ dòng nguồn** của kỳ |
| 3 | Cách chốt | **Thủ công** (bấm nút), cho **Mở lại** / **Chốt lại** |
| 4 | Engine kho | **SQLite nhúng** (`sqlite3` stdlib — không thêm dependency); thay thế parquet |
| 5 | Lịch sử | **Append-only** — mỗi lần chốt là bản ghi bất biến + cờ hiệu lực |
| 6 | Tái cấu trúc | Chỉ **thêm package `app/kho/`**, không đụng phần còn lại |
| 7 | Bảng "Lịch sử chốt sổ" | **Làm trong đợt này** |
| 8 | Sao lưu | **Một file `.sqlite`** → copy là xong; có nút sao lưu 1 chạm |
| 9 | Check C7.5 (413) | **Hạ xuống nhắc nhẹ** (không kéo kết luận) |

## 3. Kiến trúc

Giữ nguyên kiến trúc pywebview hiện tại, **thêm một lớp kho** tách biệt IO khỏi logic:

```
app/
├── api.py                (js_api — thêm phương thức chốt/mở lại/đối chiếu/lịch sử)
├── loader.py             (giữ nguyên)
├── checks/               (giữ nguyên; sửa g7 cho C7.5)
├── report.py             (giữ nguyên; +xuất lịch sử — tùy chọn)
├── trang_thai.py         (giữ nguyên)
├── chot_so.py     ★MỚI   (logic thuần: vân tay, đối chiếu, diff — nhận repository)
└── kho/           ★MỚI   (lớp lưu trữ SQLite)
    ├── __init__.py
    ├── schema.py         (DDL các bảng + PHIEN_BAN_SCHEMA)
    ├── ket_noi.py        (mở sqlite, resolve path, migration nhẹ tự viết)
    └── luu_tru.py        (KhoChotSo: repository lưu/đọc/liệt kê snapshot & phát sinh)
```

**Ranh giới rõ ràng:**
- `kho/` chỉ biết SQL; không biết pandas check hay UI. Nhận/trả `dict`/`DataFrame` và các dataclass thuần.
- `chot_so.py` chỉ biết logic nghiệp vụ (tính vân tay, so sánh, sinh diff); nhận `KhoChotSo` qua tham số → **test bằng SQLite `:memory:`**, không cần cửa sổ.
- `api.py` chỉ nối UI ↔ hai module trên; không chứa SQL.

## 4. Kho dữ liệu (SQLite)

**Vị trí:** `3. Chot so/kho_chot_so.sqlite` (thư mục mới ở gốc repo, **git-ignored**). Một file chứa **tất cả** (metadata + dòng nguồn đã đóng băng) → sao lưu = copy file này.

**Schema (star nhỏ):**

```
snapshot                       -- header mỗi lần chốt (append-only)
  id              INTEGER PK
  ky_nam          INTEGER
  ky_thang        INTEGER
  chi_nhanh       TEXT
  thoi_diem_chot  TEXT          -- ISO-8601
  ghi_chu         TEXT          -- ghi chú tùy chọn khi chốt
  so_dong         INTEGER
  tong_ps         REAL
  van_tay         TEXT          -- sha256 canonical của dòng nguồn
  ket_luan_ma     TEXT          -- SAN_SANG / CAN_RA_SOAT / CHUA_SAN_SANG
  so_do, so_vang, so_chua_lam, so_can_ra  INTEGER
  con_hieu_luc    INTEGER       -- 1 = bản chốt hiện hành của (kỳ,chi nhánh); 0 = đã bị thay
  INDEX (ky_nam, ky_thang, chi_nhanh, con_hieu_luc)

snapshot_check                 -- 40 check tại thời điểm chốt
  snapshot_id  INTEGER FK
  ma, ten      TEXT
  muc_do       TEXT
  so_loi       INTEGER
  la_thong_ke  INTEGER

snapshot_du_lieu               -- dòng nguồn đã đóng băng của kỳ (1 hàng / snapshot)
  snapshot_id  INTEGER FK (UNIQUE)
  du_lieu      BLOB          -- gzip của df.to_json(orient="records", date_format="iso")
  -- Lưu cả frame làm BLOB nén, không phải bảng cột: mỗi kỳ/chi nhánh có thể có bộ
  -- cột khác nhau (Bravo xuất khác nhau) → BLOB tránh phải migrate cột. Vẫn nằm
  -- trong CÙNG file .sqlite (một file = toàn bộ dữ liệu, sao lưu = copy 1 file).

schema_version                 -- 1 dòng: theo dõi phiên bản để migration
  phien_ban  INTEGER
```

**Append-only + hiệu lực:** chốt lại kỳ đã chốt → chèn `snapshot` mới `con_hieu_luc=1`, và `UPDATE` bản cũ về `con_hieu_luc=0` (giữ nguyên, không xóa). "Mở lại kỳ" → `UPDATE con_hieu_luc=0` cho bản hiện hành (không xóa dữ liệu). Toàn bộ trong **một transaction**.

**Vân tay (drift detection):** `van_tay(df)` = sha256 trên chuỗi canonical hóa của dòng nguồn:
- Sắp cột theo tên; ép kiểu ổn định (số → chuỗi cố định số lẻ, ngày → ISO, chuỗi giữ nguyên); nối theo thứ tự dòng đã sắp ổn định.
- Mục tiêu: **cùng dữ liệu → cùng hash** qua lưu/đọc; **đổi 1 dòng → khác hash**. Kèm `so_dong`, `tong_ps` (làm tròn VND) làm mô tả người-đọc-được.

## 5. Đối chiếu & diff

Khi `chay_kiem_tra` một cặp *(chi nhánh × kỳ)*:
1. Tìm `snapshot` `con_hieu_luc=1` của cặp đó.
2. Không có → trạng thái **Chưa chốt** (im lặng, không cảnh báo).
3. Có → tính vân tay dữ liệu hiện tại, so với `snapshot.van_tay`:
   - **KHỚP** → trạng thái **Đã chốt ✓ · khớp** (dải nhẹ emerald, trấn an).
   - **LỆCH** → trạng thái **Đã chốt ⚠ · dữ liệu đã đổi**; tính tóm tắt lệch: Δsố dòng, Δtổng PS, số chứng từ ảnh hưởng.

**Diff chi tiết** (`dien_diff(df_da_chot, df_hien_tai)`): vì đã lưu đủ dòng, so hai tập:
- Băm từng dòng → **dòng thêm** (có ở hiện tại, không ở bản chốt) và **dòng bớt** (ngược lại) bằng hiệu đa tập.
- Gom kết quả theo **chứng từ (DocCode+DocNo)** và tài khoản, kèm chênh tổng PS → chỉ đúng chỗ thay đổi thay vì đổ hàng chục nghìn dòng thô.
- *Stretch (đợt sau):* diff mức từng ô ba chiều (sửa nội dung cùng chứng từ).

## 6. Giao diện (Premium Light — đẹp & thông minh)

Hệ màu kế thừa: header gradient indigo `#1E40AF`; trạng thái emerald/amber/rose; đổ bóng mềm; bo góc rộng.

**6.1. Badge chốt trên thanh chi nhánh** (mở rộng `veThanhDonVi`): mỗi thẻ chi nhánh thêm một nhãn trạng thái chốt:
- *Chưa chốt* — viền xám, nhãn "Chưa chốt".
- *Đã chốt · khớp* — chấm emerald + 🔒, nhãn "Đã chốt dd/mm".
- *Đã chốt · lệch* — chấm amber/rose + ⚠, nhãn "Dữ liệu đã đổi".

**6.2. Khối "Chốt sổ" trong chi tiết chi nhánh** (dưới banner kết luận):
- Chưa chốt → nút chính **"🔒 Chốt sổ kỳ này"**.
- Bấm → **modal xác nhận**: hiện kỳ · chi nhánh · số dòng · tổng PS (định dạng VN) · kết luận (màu) · ô **ghi chú** tùy chọn · nút **"Chốt sổ"** (indigo) / "Hủy".
- Sau chốt → khối đổi thành thẻ **"Đã chốt"** (ngày, ghi chú) + nút phụ **"Mở lại kỳ"**, **"Chốt lại"**.

**6.3. Luồng xác nhận cập nhật dữ liệu mới (drift — điểm "thông minh"):**
- Kỳ đã chốt mà **LỆCH** → **banner nổi bật** đầu vùng kết quả: "⚠ Kỳ 08/2026 (CN-A) đã chốt dd/mm — dữ liệu nguồn hiện tại **KHÁC** bản đã chốt", kèm tóm tắt Δdòng / Δtổng PS / số chứng từ.
- Hai hành động:
  - **"Xem thay đổi"** → modal diff (bảng dòng thêm/bớt gom theo chứng từ+TK; có tìm kiếm & phân trang, tái dùng kiểu `lay_chi_tiet`).
  - **"Cập nhật & chốt lại"** → xác nhận đóng băng bản mới (append-only: bản cũ thành hết hiệu lực nhưng vẫn lưu để tra ngược).
- **KHỚP** → chỉ một dải nhẹ emerald "✓ Dữ liệu khớp bản đã chốt dd/mm" (không ồn).

**6.4. Tab "Lịch sử chốt sổ":** bảng liệt kê mọi `snapshot`:
- Cột: kỳ · chi nhánh · ngày chốt · kết luận lúc chốt · trạng thái đối chiếu hiện tại · ghi chú.
- Lọc theo chi nhánh/kỳ; bản hết hiệu lực hiển thị mờ (badge "đã thay").
- Click một dòng → xem kết luận đã đóng băng của bản đó.
- **Thanh công cụ kho** (đầu tab): **Sao lưu kho** · **Phục hồi từ file…** · **Nhập & gộp từ file…** · **Mở thư mục kho** (chi tiết ở §7). Thao tác đè dữ liệu đều qua modal xác nhận.
- *(Tùy chọn)* nút "Xuất lịch sử (Excel)".

## 7. Sao lưu, phục hồi & nhập dữ liệu

**Toàn bộ dữ liệu nằm trong một file** `3. Chot so/kho_chot_so.sqlite`. Ba thao tác, tất cả chỉ làm việc trên **một file `.sqlite`** để đơn giản và di động:

**7.1. Sao lưu (backup)** — nút **"Sao lưu kho"**:
- Chép nguyên file sang `3. Chot so/backup/kho_YYYYMMDD-HHmm.sqlite` (dùng `sqlite3` backup API để an toàn cả khi kho đang mở, không chỉ copy byte thô).
- Nút **"Mở thư mục kho"** → mở Explorer để tự chép file đi USB/máy khác.

**7.2. Phục hồi (restore — thay thế)** — nút **"Phục hồi từ file…"**:
- Chọn một file `.sqlite`; kiểm tra hợp lệ (đúng schema, kiểm phiên bản, migrate nếu cũ hơn).
- **Tự sao lưu kho hiện tại trước** khi đè (an toàn — không bao giờ mất trắng), rồi thay thế kho hiện hành bằng file được chọn.
- Có **modal xác nhận** nêu rõ: kho hiện tại có N kỳ đã chốt, sẽ được sao lưu rồi thay bằng file mới có M kỳ.

**7.3. Nhập/gộp (import — merge)** — nút **"Nhập & gộp từ file…"**:
- Dùng khi nhiều máy/nhiều người cùng chốt rồi muốn dồn về một kho.
- Đọc kho nguồn, duyệt từng `snapshot`; **bỏ qua bản trùng** (cùng `ky_nam, ky_thang, chi_nhanh, thoi_diem_chot, van_tay`), chèn bản mới (kèm `snapshot_check` + `phat_sinh`) với id cục bộ mới.
- Sau khi gộp, **tính lại cờ `con_hieu_luc`** theo từng cặp *(kỳ × chi nhánh)*: bản có `thoi_diem_chot` mới nhất = 1, còn lại = 0 → giữ đúng ngữ nghĩa append-only.
- Báo cáo kết quả gộp: đã thêm X bản, bỏ qua Y bản trùng.

**Cài máy khác:** chép file `.sqlite` vào `3. Chot so/` của bản cài mới (hoặc dùng **Phục hồi**) → có ngay toàn bộ lịch sử chốt.

**Khởi tạo:** tự tạo kho rỗng đúng schema nếu file chưa tồn tại (lần chạy đầu). Migration nhẹ nâng schema khi mở file cũ hơn; **từ chối** file có `schema_version` mới hơn bản đang chạy (báo người dùng nâng cấp tool) thay vì làm hỏng dữ liệu.

## 8. API (js_api mới)

- `chot_so(ghi_chu="")` → chốt cặp đang xem; trả trạng thái chốt mới.
- `mo_lai_ky()` → đưa bản hiện hành về hết hiệu lực.
- `lay_diff_chot(trang, kich_thuoc, tim_kiem)` → dữ liệu bảng "Xem thay đổi".
- `lich_su_chot(loc_chi_nhanh=None, loc_ky=None)` → dữ liệu tab lịch sử.
- `sao_luu_kho()` → tạo file backup có dấu thời gian; trả đường dẫn.
- `phuc_hoi_kho(path)` → tự backup kho hiện tại rồi thay bằng file chọn (sau kiểm tra hợp lệ + migrate).
- `nhap_gop_kho(path)` → gộp snapshot chưa trùng từ file nguồn; trả `{da_them, bo_qua_trung}`.
- `mo_thu_muc_kho()` → mở Explorer tại thư mục kho.
- Bơm thêm vào `_tom_tat` & `_danh_sach_don_vi`: `chot` = `{trang_thai, ngay_chot, ghi_chu, doi_chieu, tom_tat_lech}`.

## 9. Thay đổi check C7.5 (413)

Trong `app/checks/g7_phan_bo_trich_lap.py`: đánh dấu **C7.5 là `la_thong_ke`** (nhắc nhẹ/tự xác nhận) → **không** đẩy kỳ ra khỏi "SẴN SÀNG". Giữ nguyên nội dung nhắc để không bỏ sót tháng hiếm hoi thật sự cần đánh giá tỷ giá. Cập nhật `tests/test_g7_phan_bo_trich_lap.py`.

## 10. Kiểm thử

Giữ **259 test cũ xanh** dưới `pytest -W error`. Thêm:
- `chot_so.py`: vân tay ổn định (df giống → hash giống; sửa 1 dòng → khác); `doi_chieu` KHỚP/LỆCH; `dien_diff` thêm/bớt gom theo chứng từ.
- `kho/`: tạo kho mới đúng schema; `luu_snapshot` → `doc` round-trip (dòng nguồn khôi phục nguyên kiểu); append-only (chốt lại tạo bản mới, bản cũ `con_hieu_luc=0`, không mất); `mo_lai`; migration nâng schema; dùng `:memory:` hoặc file tạm trong scratchpad.
- **Sao lưu/phục hồi/nhập:** `sao_luu_kho` tạo file backup mở lại được; `phuc_hoi_kho` tự backup bản cũ rồi thay, từ chối file schema mới hơn; `nhap_gop_kho` bỏ qua bản trùng, thêm bản mới, tính lại `con_hieu_luc` đúng, trả đúng số đã thêm/bỏ qua.
- `api.py`: chốt → `_danh_sach_don_vi` báo "Đã chốt"; sửa dữ liệu → đối chiếu LỆCH.
- Sửa test C7.5 theo mục 9.

## 11. Ngoài phạm vi đợt này

- Diff mức từng ô ba chiều (chỉ làm thêm/bớt).
- Nối DWH SQL Server trung tâm (Việt Xô) — giữ kho cục bộ, portable.
- Tái cấu trúc repo rộng (chỉ thêm `app/kho/`).
- Xuất lịch sử Excel là tùy chọn, có thể để sau.

## 12. Rủi ro & giảm thiểu

- **Vân tay không ổn định qua lưu/đọc** → canonical hóa kiểu dữ liệu chặt + test round-trip trước khi dựng UI.
- **Khóa dòng để diff** (biết known-issue: DocCode+DocNo không dấu tách) → diff dựa trên **băm cả dòng** (không phụ thuộc khóa), chỉ *gom hiển thị* theo chứng từ.
- **Kho phình** → SQLite chịu hàng triệu dòng thoải mái; nếu cần, đợt sau nén/nội suy các kỳ rất cũ.
- **Ghi hỏng giữa chừng** → mọi thao tác chốt/mở lại trong một transaction; sao lưu 1 chạm trước khi chốt lại.
