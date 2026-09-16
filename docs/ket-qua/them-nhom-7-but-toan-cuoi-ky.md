# Thêm Nhóm 7 — Bút toán phân bổ & trích lập cuối kỳ

Ngày 16/09/2026. Nhánh `nhom-7-but-toan-cuoi-ky`. 245 test xanh dưới `-W error`.

## Vì sao có nhóm này

Rà soát bằng skill kế toán (close-management) cho thấy 11 bước cũ **đúng nhưng mới
là nửa sau quy trình**: tool bắt đầu từ chỗ chi phí đã nằm trong 621/627, mà bỏ qua
các bút toán *đưa* chi phí vào — khấu hao, phân bổ, lương — vốn là nhóm hay quên
nhất, ngang với giá vốn. Thêm cả phần cuối kỳ: thuế TNDN, đánh giá tỷ giá, dự phòng.

## Quyết định thiết kế cốt lõi: tách theo sức mạnh bằng chứng

Plan v1 định cho tất cả mức 🟡. **Spike thử → 8 test đỏ**, nặng nhất là
`test_ket_luan` — một bộ sổ sạch cũng không bao giờ đạt "SẴN SÀNG KHÓA SỔ" nữa vì
`tinh_ket_luan` gộp mọi check vàng. Đây là bẫy C4.1 tái diễn: khẳng định dựa trên
sự vắng mặt của bằng chứng.

Cách giải: chia Nhóm 7 làm hai loại.

| Loại | Check | Cơ chế | Kéo kết luận? |
|------|-------|--------|---------------|
| 📋 Checklist | C7.1 khấu hao, C7.2 phân bổ 242, C7.3 lương, C7.4 trích trước 335, C7.7 dự phòng 229 | `la_thong_ke=True` | Không |
| 🟡 Cảnh báo thật | C7.5 tỷ giá, C7.6 thuế TNDN | `VANG` bình thường | Có |

Không có số dư đầu kỳ nên "kỳ này không thấy 214" **không** suy ra được DN quên
khấu hao. Checklist vẫn hiện đủ ở Tab A/Tab B, bấm vào đọc được, chỉ không tự hạ
kết luận thay kế toán. Chỉ C7.5/C7.6 có bằng chứng ngay trong file (ngoại tệ chạm
TK tiền tệ mà thiếu 413; kết chuyển lãi mà thiếu 8211) nên mới là cảnh báo.

## Trạng thái bước mới `TU_XAC_NHAN`

Tab A nâng lên 16 bước: 3 bước Tầng 1 (khấu hao/phân bổ/lương) lên đầu, tỷ giá +
thuế TNDN trước khấu trừ GTGT. Ba bước checklist dùng trạng thái `TU_XAC_NHAN` —
màu xanh trung tính, biểu tượng dấu hỏi, tách hẳn khỏi vàng "cần rà" để mắt không
đọc nhầm thành việc phải xử lý. `TU_XAC_NHAN` không nằm trong `tinh_ket_luan` nên
tự động đứng ngoài kết luận. Trên sổ rỗng, mọi bước Nhóm 7 hạ về "Không áp dụng"
(không báo "Đã làm" trên sổ trắng).

Đường ống trạng thái được nối đủ ba nơi trong một task riêng (trước khi thêm bước):
`report.py` (`TEN_TRANG_THAI`, `MAU`), `app.js` (`ICON_TT`, `NHAN_TT`, hình `hoi`),
`style.css` (`.tt-tu_xac_nhan`). Bỏ sót bất kỳ nơi nào là KeyError lúc xuất Excel
hoặc hiển thị sai nhãn — đã lường trước trong plan v2.

## Kết quả trên file thật (A01, kỳ 08/2026)

| | |
|---|---|
| Số bước / nhóm | **16 / 7** |
| C7.1 khấu hao | ✅ Có 214 = 149.952.590 (đối ứng 641/642/627) |
| C7.2 phân bổ 242 | ✅ Có 242 = 449.969.674 |
| C7.3 lương | ✅ Có 334 = 5.141.384.321 |
| C7.6 thuế TNDN | ✅ 821 Nợ = Có = 15.115.962 |
| **C7.5 tỷ giá** | 🟡 **bắn** — 25 dòng USD chạm 331/112, `413` = 0 |
| Kết luận đầu trang | "CHƯA SẴN SÀNG — còn 2 việc" (2 đỏ), so_vang 9 → 10 (thêm C7.5) |

Đúng thiết kế: sổ làm đủ thì các check im (xanh), chỉ tỷ giá — thứ thật sự bị bỏ
sót — sáng đèn.

## Sửa phát sinh trong lúc làm

- **C7.5 thu hẹp phạm vi:** chỉ nhắc khi ngoại tệ chạm **TK tiền tệ** (111/112/131/
  331…). Ngoại tệ trên TK vật tư (152/153/156) ghi theo tỷ giá lúc phát sinh, không
  đánh giá lại — nhắc ở đó là dương tính giả. File thật có USD trên cả hai loại.
- **Dòng đếm Tab A** bỏ sót `tu_xac_nhan` (14 + 0 + 1 < 16). Đã đưa vào và chỉ hiện
  mục có số > 0.
- **Tiêu đề "11 bước"** ghi cứng trong HTML → làm động theo `trang_thai.length`.

## Bản .bat

`Kiem_tra_khoa_so.bat` viết lại: tự tìm Python (`py`→`python`), tự `pip install` lần
đầu nếu thiếu thư viện, báo lỗi tiếng Việt kèm `pause`. Double-click là chạy.
