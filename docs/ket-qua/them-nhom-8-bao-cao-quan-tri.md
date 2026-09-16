# Thêm Nhóm 8 — Sẵn sàng cho Báo cáo quản trị + nhận chi nhánh đa cột

Ngày 16/09/2026. Nhánh `nhom-8-bao-cao-quan-tri` (tiếp sau Nhóm 7 đã gộp vào main). 258 test xanh dưới `-W error`.

## Nguồn gốc: mổ xẻ file BC quản trị của kế toán tổng hợp

File `VXHN_2607_BC QUAN TRI_KMCP_OK.xlsx` lộ ra quy trình thật: bảng kê Bravo (sheet
BKCT) → phân loại lại theo **khoản mục chi phí (KMCP)** và **bộ phận** (BCQT) →
**sheet CHECK đối chiếu từng TK: Bravo vs Tổng hợp, chênh lệch phải = 0** (đang đầy
`#REF!`). Nguyên nhân gốc của chênh lệch nằm ngay trong file Bravo: dòng chi phí
thiếu khoản mục/bộ phận thì rơi khỏi báo cáo.

## Đã làm

**A — Nhận chi nhánh đa cột.** File này để chi nhánh ở cột **`Đơn vị`** (VXHN 87.008
/ VXHO 615), không phải `BranchCode`. `loader.COT_CHI_NHANH` đổi từ một chuỗi thành
danh sách ưu tiên `("BranchCode", "Đơn vị")`; `ma_chi_nhanh` dùng cột đầu tiên **có
giá trị**. File 08/2026 vẫn tách theo `BranchCode`; file này tách theo `Đơn vị`.

**B — Nhóm 8 (Tab B, không đụng 16 bước khóa sổ):**
- **C8.1** chi phí thiếu mã khoản mục → rơi khỏi báo cáo theo khoản mục.
- **C8.2** chi phí thiếu bộ phận → rơi khỏi báo cáo theo bộ phận.
- **C8.3** (thống kê) tổng hợp chi phí theo khoản mục × TK — cột "Bravo" sạch thay
  cho cột đầy `#REF!` trong sheet CHECK của kế toán.

## Lệch so với plan (do dữ liệu thật quyết định)

Plan v1 định `TK_BCQT = (…,"515","711",…)` — gồm cả TK doanh thu. Nghiệm thu trên
file thật phát hiện **5 dòng dương-tính-giả ở VXHN**: đó là bút toán **kết chuyển
doanh thu** (Nợ 515/711 / Có 911), không mang khoản mục và 515/711 **không bao giờ**
dùng khoản mục ở công ty này. Hai lỗi chồng nhau:

1. TK doanh thu 515/711 chỉ xuất hiện bên Nợ ở bút toán kết chuyển — phân loại
   khoản mục/bộ phận sống ở **bên Nợ của TK chi phí** (Nợ 62x/64x/635/811), không
   phải bên Nợ của TK doanh thu.
2. Guard "cả công ty có dùng khoản mục" quá thô — bắt nhầm dòng của TK vốn không
   dùng khoản mục chỉ vì TK khác có dùng. Đúng bẫy C4.1 ở mức tinh vi hơn.

**Sửa:** (1) thu về `TK_CHI_PHI = ("621","622","627","635","641","642","811")`;
(2) C8.1 chuyển sang **tự suy theo từng nhóm TK cấp 1** — chỉ bắt dòng thiếu khoản
mục trong nhóm TK mà kỳ này *có* dòng đã điền khoản mục — cùng cơ chế với C8.2.
Sau sửa: C8.1 = 0, C8.2 = 0 trên cả VXHN và VXHO. Sổ sạch thì Nhóm 8 im.

Đối chiếu doanh thu (515/711 bên Có) là pattern khác, để lần sau.

## Ngoài phạm vi (spike sau)

- Đối chiếu tự động đầy đủ (tái tạo sheet CHECK): cột "Tổng hợp" ở 641/642 đã bị
  tái phân loại (tool đo: 621/622/627 khớp, 641/642 lệch) — không suy được chỉ từ
  file Bravo. Cần đọc thẳng workbook nhiều sheet.
- Đọc workbook nhiều sheet (tự tìm sheet BKCT): tool hiện đọc sheet đầu; file BC
  quản trị để BKCT ở sheet thứ 3.

## Con số kiểm chứng (file thật, kỳ 07/2026)

| Đơn vị | Dòng | C8.1 thiếu KM | C8.2 thiếu BP | C8.3 |
|--------|------|---------------|---------------|------|
| VXHN | 87.008 | 0 | 0 | 82 dòng (khoản mục × TK) |
| VXHO | 615 | 0 | 0 | 46 dòng |

40 check · 8 nhóm · 16 bước khóa sổ (Nhóm 8 không thêm bước).
