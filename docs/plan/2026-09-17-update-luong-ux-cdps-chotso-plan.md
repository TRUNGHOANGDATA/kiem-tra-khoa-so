# Plan — Cập nhật luồng nhập, UX lỗi/cảnh báo, xem CĐPS, filter chốt sổ

_2026-09-17. Nhánh dự kiến: nối tiếp `feat/cdps-nhap` (hoặc nhánh mới). Trạng thái: chờ duyệt._

Bốn việc người dùng nêu sau khi C7.6 (lỗ lũy kế) đã chạy đúng trên A08.

---

## Việc 1 — Phân biệt LỖI (nghiêm trọng) vs CẢNH BÁO rõ ràng
**Vấn đề:** banner ghi "Nghiêm trọng 1" nhưng mục đỏ nằm lẫn trong tab "Lỗi & cảnh báo",
đỏ/vàng chỉ khác nhau chấm nhỏ → khó tìm cái phải xử lý.

**Thay đổi (UI, `KetQua.tsx`):**
- Tách tab "Lỗi & cảnh báo" thành **2 khu rõ**: **🔴 NGHIÊM TRỌNG (N)** ở trên (nền/viền
  đỏ, icon ✕), **🟡 CẢNH BÁO (N)** dưới (vàng). Chỉ liệt kê check `so_loi>0 & !la_thong_ke`.
  Mục thống kê/checklist gom vào khu xám thu gọn cuối.
- **Đếm số trên nhãn tab**: "Lỗi & cảnh báo · 1 đỏ / 4 vàng".
- Bấm **pill "Nghiêm trọng"** ở banner → nhảy sang tab và cuộn tới khu đỏ.
- Mỗi dòng check nặng: nền đỏ nhạt + viền trái đỏ (khác hẳn vàng).

**Không đổi backend.** Bounded, làm trước (giá trị ngay).

---

## Việc 2 — Đảo luồng nhập: CĐPS = Phase 1 (bắt buộc) → Bảng kê = Phase 2
**Ý người dùng:** nhập CĐPS trước và **bắt buộc**, rồi mới tới bảng kê.

**Thay đổi (UI `ChonFile.tsx` + api):**
- Màn nhập thành **stepper 2 bước**: **Bước 1 — Cân đối phát sinh (CĐPS)** (nút chọn thư
  mục, hiện kỳ/chi nhánh đã nhập), **Bước 2 — Bảng kê chứng từ**.
- Sau khi nạp bảng kê: đối chiếu chi nhánh × kỳ với CĐPS đã có → hiện **✓ đã nhập / ⚠ thiếu**.

**QUYẾT ĐỊNH CẦN CHỐT — mức "bắt buộc":**
- (a) **Cứng:** chi nhánh thiếu CĐPS thì **không cho Kiểm tra** (chặn).
- (b) **Mềm (đề xuất):** vẫn cho Kiểm tra, nhưng chi nhánh thiếu CĐPS bị **cảnh báo nổi bật**
  và C7.6 mất khả năng trừ lỗ lũy kế (ghi chú rõ). Tránh kẹt khi chưa xuất kịp CĐPS.

---

## Việc 3 — Màn xem CĐPS theo từng chi nhánh × tháng
**Thay đổi (UI màn mới + api):**
- Nút **"Cân đối phát sinh"** ở header (cạnh "Lịch sử chốt sổ") → màn mới:
  - Bảng liệt kê **(chi nhánh × kỳ)** đã nhập (từ `trang_thai_cdps`), filter theo **tháng/năm**
    + **chi nhánh**.
  - Bấm 1 dòng → chi tiết các TK: số hiệu, tên, **dư đầu N/C · PS N/C · dư cuối N/C**; tìm theo
    số hiệu TK; ẩn/hiện dòng nhóm.
- Backend: đã có `KhoChotSo.doc_cdps/trang_thai_cdps`; thêm api `chi_tiet_cdps(chi_nhanh, nam, thang)`.

---

## Việc 4 — Lịch sử chốt sổ filter được (theo tháng)
**Thay đổi (UI `LichSu.tsx`):**
- Thêm thanh filter: **kỳ (tháng/năm)**, **chi nhánh**, **chỉ hiệu lực**. Lọc phía client trên
  danh sách đã tải (dữ liệu chốt không lớn). Không đổi backend.

---

## Thứ tự đề xuất
1. Việc 1 (UX lỗi/cảnh báo) — nhanh, giá trị ngay.
2. Việc 4 (filter lịch sử) — nhỏ, độc lập.
3. Việc 3 (màn xem CĐPS) — vừa, dùng lại dữ liệu đã có.
4. Việc 2 (đảo luồng + bắt buộc) — lớn nhất, đụng flow chính; làm sau khi chốt mức bắt buộc.

Mỗi việc: TDD phần backend (nếu có) + build lại React + nghiệm thu mắt thường.
Drift + đối chiếu CĐPS↔bảng kê (từ spec CĐPS) vẫn để sau cùng.
