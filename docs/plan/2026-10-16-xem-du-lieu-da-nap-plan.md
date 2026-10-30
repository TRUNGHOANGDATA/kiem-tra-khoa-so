# Xem dữ liệu đã nạp (Sổ bán hàng · Bảng kê · CĐPS) + nhận sổ bán hàng gộp A00

Ngày: 2026-10-16 · Trạng thái: **PLAN, chưa code** · Đích: **1.3.1** (một đợt, không chia phase)

## 1. Vì sao

Từ 1.3.0 kho đã giữ **3 nguồn** theo (chi nhánh × kỳ), nhưng app chỉ cho **xem CĐPS**
(`ui/src/CanDoi.tsx`). Bảng kê và sổ bán hàng nằm trong kho mà không mở ra được. Người dùng
không biết mình đã nạp bản nào, nạp lúc nào, có đúng kỳ không. Họ cũng không tự soát lại
được cách KTTH đang làm tay: lọc Có 511, xem cột thuế.

## 2. Việc phải sửa trước: sổ bán hàng GỘP mọi chi nhánh (file `A00`)

File người dùng xuất 16/10: `So chi tiet ban hang A00 092026.xlsx` — **66.745 dòng, 8 chi
nhánh trong 1 file, KHÔNG có cột chi nhánh** (60 cột y hệt file A01). Bản 1.3.0 lấy mã chi
nhánh từ tên file ⇒ sẽ lưu cả file thành chi nhánh "A00", và A01–A08 đều báo **✕ thiếu sổ
bán hàng** ⇒ nút Kiểm tra bị khóa.

**Đã đo cách tách:**

| Khóa thử | Kết quả |
|---|---|
| (DocCode, DocNo) | ✕ **11.067 / 35.414** chứng từ trùng số giữa các chi nhánh |
| **`Id`** | ✓ `Id` của sổ bán hàng = `Id` chứng từ trong bảng kê (A01: 100%). **0 / 70.313** Id thuộc >1 chi nhánh. Tách được **66.727 / 66.745** dòng; phần A01 tách ra **trùng khít** file A01 riêng (18.359 dòng, cùng tập Id) |
| 18 dòng không khớp | toàn `Amount2 = 0`: hàng tặng, C3.2/C3.4 vốn đã loại |

Tách được: A01 18.359 · A02 12.047 · A03 12.098 · A04 10.801 · A05 5.351 · A06 4.203 ·
A07 1.942 · A08 1.926.

**Cách làm (không cần thứ tự nạp):**
- `so_ban_hang.chuan_hoa` giữ thêm cột **`Id`**. Hiện chưa giữ — kho đang có 0 sổ bán hàng
  nên không cần di trú.
- Lưu nguyên file theo mã trong tên (`A00` hoặc `A01`…), **không tách lúc nạp**.
- Lúc kiểm tra một chi nhánh: lấy dòng sổ có `Id` ∈ tập `Id` trong bảng kê của chính chi
  nhánh đó. Ưu tiên sổ mang đúng mã chi nhánh, không có thì dùng sổ gộp của kỳ đó. Một luật
  chạy cho cả file riêng lẫn file gộp.
- `thieu_so_ban_hang`: chi nhánh coi như **có sổ** khi kỳ đó có sổ mang mã của nó, hoặc
  có một sổ gộp chứa `Id` của nó.
- Bảng kê không có cột `Id` (định dạng xuất khác) → chỉ nhận sổ riêng theo tên file, báo rõ.

## 3. Màn "Dữ liệu đã nạp" (thay màn "Cân đối phát sinh" hiện có)

Một màn, **3 tab: CĐPS · Sổ bán hàng · Bảng kê**. Khung giống `CanDoi.tsx` hiện tại để
không phải học lại: lọc **Kỳ / Chi nhánh** → danh sách (chi nhánh × kỳ) → bấm một dòng → bảng
chi tiết.

| | CĐPS | Sổ bán hàng | Bảng kê |
|---|---|---|---|
| Danh sách | như cũ | chi nhánh · kỳ · số dòng · file · nạp lúc | như sổ bán hàng |
| Đầu bảng (tổng) | — | Doanh thu (Nợ131/Có511) · Thuế ra · Trả lại · Thuế trả lại | Tổng PS · số chứng từ |
| Lọc nhanh | ẩn TK nhóm | **TK Nợ / TK Có** (gõ đầu số, vd `511`) · **chỉ dòng thuế = 0** | **TK Nợ / TK Có** · loại CT |
| Tìm | ô tìm | ô tìm (số CT, khách, mã hàng) | ô tìm |
| Xuất Excel | — | ✓ đúng bộ lọc đang xem | ✓ đúng bộ lọc đang xem |

- **Sổ gộp A00**: ở tab Sổ bán hàng, chọn chi nhánh A03 thì hiện **phần đã tách theo Id**
  của A03, không phải cả file. Dòng nhãn ghi rõ "từ file gộp So chi tiet ban hang A00 …".
- **Phân trang phía Python**, 100 dòng/trang, giống `lay_chi_tiet`. Bảng kê A01 có 79k dòng
  × 80 cột, đẩy hết sang giao diện là treo.
- **Cột hiển thị bảng kê**: chỉ ~14 cột đọc được (Loại CT, Số CT, Ngày, Diễn giải, TK Nợ, TK
  Có, Số tiền, Khách hàng, Mã/Tên hàng, SL, Mã thuế, Loại GD, Người lập). Xuất Excel thì ra
  đủ cột.
- **Nhớ tạm khung đang xem**: giải nén một bảng kê mất ~2,7 s. Giữ 1 khung gần nhất trong bộ
  nhớ để lật trang, đổi lọc mà không giải nén lại.
- Thuế = 0 hiện ký hiệu **✕** cạnh số, không chỉ tô màu (người dùng mù màu).
- Nút header "Cân đối phát sinh" đổi thành **"Dữ liệu đã nạp"**.

**API mới** (`app/api.py`): `xem_nguon(loai, chi_nhanh, ky_nam, ky_thang, trang, kich_thuoc,
tim, loc_no, loc_co, chi_thue_0)` → `{tong, cot, nhan, cot_so, dong, tong_hop, nguon_file}` và
`xuat_nguon(...)` (cùng tham số, ra Excel). `chi_tiet_cdps` giữ nguyên.

## 4. Các bước (một đợt)

1. `so_ban_hang.py`: giữ `Id`. Hàm `cat_theo_chi_nhanh(sbh, bang_ke)` lọc theo tập Id.
2. `api.py`: `_so_ban_hang_cua` + `thieu_so_ban_hang` dùng luật §2; `ky_trong_kho` tính
   `co_so_ban_hang` theo cùng luật.
3. `api.py`: `xem_nguon` / `xuat_nguon` + nhớ tạm 1 khung.
4. `report.py`: xuất bảng nguồn ra Excel. Dùng lại khuôn `xuat_mot_check`.
5. UI: `CanDoi.tsx` → `DuLieuDaNap.tsx` (3 tab), đổi nút header; build.
6. Test (kho ép tmp_path):
   - Sổ gộp 2 chi nhánh trùng DocNo khác Id → tách đúng.
   - Chi nhánh có sổ gộp → không bị chặn.
   - Có cả sổ riêng lẫn sổ gộp → dùng sổ riêng, không nhân đôi dòng.
   - Bảng kê thiếu `Id` → chỉ nhận sổ riêng.
   - `xem_nguon`: phân trang, lọc TK, lọc thuế 0, tổng đầu bảng; tìm theo ngày dd/mm/yyyy.
7. Kiểm thật:
   - Nạp `A00 092026` + bảng kê `092026 A00`.
   - C3.2/C3.4 của A01 phải **y hệt 1.3.0** (31 dòng / 6 dòng).
   - Lấy số C3.2/C3.4 của 7 chi nhánh còn lại cho bảng kiểm §11 plan 15/10.
8. `pytest -W error`, nâng `VERSION` 1.3.1, docs `ket-qua`, build + phát hành theo quy trình cũ.

## 5. Không làm

- Sửa/xóa dữ liệu trong màn xem — màn này chỉ để đọc. Muốn đổi thì nạp lại file.
- Pivot / biểu đồ — xuất Excel là đủ để soát sâu.
- Đọc `Bang ke 632 GIA VON …` (file mới xuất 15/10) — chưa có check nào dùng, chờ yêu cầu.
