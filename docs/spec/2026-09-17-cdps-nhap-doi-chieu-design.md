# Spec — Nạp CĐPS (Bảng cân đối số phát sinh) — MVP

_2026-09-17. Trạng thái: chờ duyệt để chuyển sang plan/implement._

## 1. Vấn đề
Bảng kê chứng từ **không chứa số dư đầu kỳ**, nên C7.6 (911→8211) không thấy được
**lỗ lũy kế** → dương tính giả. Ví dụ A08 kỳ 08/2026: riêng kỳ **lãi 1.571.960.518**
(Nợ 911/Có 4212) nhưng **dư đầu 4212 Nợ 2.981.950.998** (lỗ lũy kế) > lãi kỳ → sau
chuyển lỗ, thu nhập tính thuế = 0 → **không phát sinh 8211 là ĐÚNG**. Cần nạp thêm
**CĐPS** để có số dư đầu kỳ.

## 2. Quyết định (đã chốt với người dùng)
- **Chi nhánh + kỳ suy từ TÊN FILE** (BranchCode trong file để trống). Quy ước:
  `A08 082026 BANG CAN DOI PHAT SINH.xlsx` → chi nhánh `A08`, kỳ `08/2026`.
- **UI đặt ở màn nhập chính** (cạnh nạp bảng kê), có trạng thái "đã nhập/chưa".
- **MVP trước:** parser + lưu SQLite + trạng thái + **sửa C7.6**. **Drift** và
  **đối chiếu CĐPS↔bảng kê** để **đợt sau**.
- Lưu trong **kho SQLite hiện có** (1 file, không thêm file thứ 2).

## 3. Cấu trúc file nguồn
1 sheet `Table1`, header dòng 0, cột tiếng Anh. Cột dùng:
`Account`, `AccountName`, `DebitBal1`/`CreditBal1` (dư đầu Nợ/Có),
`DebitAmount`/`CreditAmount` (PS kỳ Nợ/Có), `DebitBal2`/`CreditBal2` (dư cuối Nợ/Có),
`IsGroup` (True = dòng tổng nhóm), `Level`. **Cộng tổng phải lọc dòng lá
(`IsGroup=False`)** để không đếm trùng cha–con; đọc số dư một TK cụ thể thì lấy đúng
dòng `Account` đó.

## 4. Thiết kế MVP

### 4.1 Parser — `app/cdps.py`
- `suy_branch_ky(ten_file) -> (ma, nam, thang) | None`: regex
  `^\s*([A-Za-z]+\d+)\s+(\d{2})(\d{4})\b` (mã CN + MMYYYY). Không khớp → None.
- `doc_cdps(path) -> (DataFrame, MetaCdps)`: đọc `Table1`, chuẩn hóa cột →
  `account, ten, du_dau_no, du_dau_co, ps_no, ps_co, du_cuoi_no, du_cuoi_co,
  is_group, level`; ép số (rỗng→0.0). Thiếu cột chuẩn/không phải CĐPS → nêu lỗi rõ.
  Meta gồm `(ma, nam, thang)` suy từ tên file (thiếu → lỗi "không suy được kỳ").

### 4.2 Lưu — kho SQLite (schema v2→v3)
- Bảng `cdps(chi_nhanh, ky_nam, ky_thang, account, ten, du_dau_no, du_dau_co,
  ps_no, ps_co, du_cuoi_no, du_cuoi_co, is_group, level, thoi_diem_nap)`, index theo
  (chi_nhanh, ky_nam, ky_thang, account).
- `KhoChotSo`:
  - `luu_cdps(chi_nhanh, ky_nam, ky_thang, df, thoi_diem)`: **thay toàn bộ kỳ đó**
    (xóa cũ theo (chi_nhanh,ky) rồi chèn) — nạp lại là ghi đè sạch.
  - `doc_cdps(chi_nhanh, ky_nam, ky_thang) -> DataFrame` (rỗng nếu chưa nhập).
  - `du_dau_theo_prefix(chi_nhanh, ky, prefix) -> (no, co)`: tổng dư đầu Nợ/Có các
    dòng lá khớp prefix (cho 421x).
  - `trang_thai_cdps() -> list[(chi_nhanh, ky_nam, ky_thang, thoi_diem_nap)]`.
- `mo_kho` nâng v3 tự tạo bảng (đã có cơ chế migrate `pb < PHIEN_BAN_SCHEMA`).

### 4.3 Sửa C7.6 — bơm lỗ lũy kế qua `BoiCanh`
- `BoiCanh` thêm `lo_luy_ke_dau: float | None = None` (None = **chưa có CĐPS**).
  Giá trị = `du_dau_no(421x) − du_dau_co(421x)` (dương = lỗ lũy kế đầu kỳ).
- `api._chay...` (nơi tạo `ctx = BoiCanh(...)`, api.py ~222): tra kho CĐPS theo
  (chi nhánh, kỳ); có thì set `ctx.lo_luy_ke_dau`. Check vẫn thuần, không mở SQLite.
- Logic C7.6 mới (`g7_phan_bo_trich_lap.py`):
  - `lai_ky = net(Nợ911/Có421) − net(Nợ421/Có911)` (giữ cách hiện tại).
  - Nếu `ctx.lo_luy_ke_dau is None` (chưa nhập CĐPS): **giữ hành vi hiện tại**
    (cảnh báo khi `lai_ky>0 và no_821==0`), thêm ghi chú "nạp CĐPS để loại trừ lỗ
    lũy kế".
  - Nếu có CĐPS: chỉ cảnh báo khi **`lai_ky > max(0, lo_luy_ke_dau)`** và
    `no_821==0` (còn thu nhập tính thuế sau bù lỗ). A08: 1,57 tỷ < 2,98 tỷ → im.

### 4.4 UI — màn nhập chính (`ChonFile`)
- Khu "CĐPS": nút **Nạp CĐPS (thư mục)** + danh sách trạng thái đã nhập/chưa theo
  (chi nhánh × kỳ) cho các chi nhánh đang nạp từ bảng kê.
- api: `nap_cdps_thu_muc()` (đọc mọi .xlsx CĐPS trong thư mục nguồn, suy CN+kỳ, lưu),
  `trang_thai_cdps()` cho UI.

## 5. Test (TDD)
- `suy_branch_ky`: "A08 082026 …" → ("A08",2026,8); tên lạ → None.
- parser: df giả/đúng cột → dư đầu 4212 = 2.981.950.998; lọc dòng lá.
- kho: lưu/đọc cdps; `du_dau_theo_prefix("A08",ky,"421")`; nạp lại thay kỳ;
  `trang_thai_cdps`; migrate v2→v3.
- C7.6: lỗ lũy kế > lãi → **không** cảnh báo; lỗ lũy kế < lãi → cảnh báo;
  `lo_luy_ke_dau=None` → giữ cảnh báo + ghi chú.
- api: sau khi nạp CĐPS, `ctx.lo_luy_ke_dau` được set đúng cho chi nhánh.

## 6. Để lại (đợt sau)
- **Drift**: lưu CĐPS từng kỳ; nạp lại số khác → cảnh báo (như drift chốt sổ).
- **Đối chiếu CĐPS↔bảng kê**: PS Nợ/Có từng TK (dòng lá) so tổng phát sinh từ bảng
  kê chứng từ.
- Chuyển lỗ 5 năm: chỉ dùng dư đầu 421x làm proxy, không kiểm hạn 5 năm.
