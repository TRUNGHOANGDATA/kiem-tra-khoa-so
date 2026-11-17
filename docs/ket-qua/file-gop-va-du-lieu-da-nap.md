# File gộp A00 · C00 · T00, vân tay chốt sổ, màn "Dữ liệu đã nạp" (1.3.1)

Ngày: 2026-11-17 · Plan: `docs/plan/2026-10-16-xem-du-lieu-da-nap-plan.md` (đã sửa sau red-team)

## Bối cảnh

Từ kỳ 10/2026 Bravo có thêm khay C (C01–C06). Ngoài file gộp A00, người dùng còn xuất được C00
và T00 (T00 = A + C). Tool chỉ soát sai lệch trên **từng khay** (`BranchCode`). Tool không làm hợp
nhất và không phân biệt pháp nhân (người dùng chốt 17/11). Plan được red-team trước khi code:
10 lỗ hổng, 3 lỗ nặng nhất đã kiểm lại trong code và đều đúng.

## Đã làm

| Phần | File |
|---|---|
| `Id` chứng từ ép `Int64` ở cả bảng kê lẫn sổ bán hàng (trước: chuỗi vs số, khớp 0/165) | `app/loader.py`, `app/so_ban_hang.py` |
| `MA_GOP = (A00, C00, T00)`, `KHAY_BO_QUA = (A99, T99)`: dòng A99/T99 bị loại trước khi tách khay, có lời báo | `app/loader.py` |
| Bảng kê gom theo **(khay × kỳ)**. Cùng khay × kỳ ở 2 file trùng Id: giống hệt → giữ một; khác → **dừng khay đó**, nêu tên 2 file. Nguồn (tên file, mtime) dựng sau khi chọn. Lời báo hiện trên màn nạp | `app/loader.py`, `app/api.py`, `ui/src/ChonFile.tsx` |
| Vân tay: số int và float viết cùng một kiểu. `doi_chieu` băm lại bản đã chốt khi hash lưu theo luật cũ | `app/chot_so.py` |
| Sổ bán hàng **gộp** tách về từng khay **ngay lúc nạp** theo Id bảng kê trong kho (chưa có bảng kê thì từ chối). Dòng không khớp khay nào được đếm và báo | `app/api.py`, `app/so_ban_hang.py`, `app/kho/luu_tru.py` |
| Ghi đè sổ có kiểm độ tươi: khác nội dung mà file cũ hơn thì giữ bản trong kho (`cu_hon`). Duyệt thư mục cũ → mới (trước: file **cũ nhất** thắng) | như trên |
| C3.2/C3.4: sổ không phủ đủ chứng từ bán hàng/trả lại của bảng kê → ghi rõ số thiếu; không thấy dòng thuế 0 thì đứng ngoài kết luận (không ✓) | `app/checks/g3_thue_gtgt.py` |
| CĐPS mang mã gộp hoặc A99/T99: bỏ qua khi nạp, báo "cần CĐPS từng khay" | `app/api.py` |
| Màn **"Dữ liệu đã nạp"** (thay "Cân đối phát sinh"): 3 tab CĐPS · Sổ bán hàng · Bảng kê, lọc TK Nợ/Có, loại CT, chỉ dòng thuế 0 (nhãn chữ "thuế 0", không dùng ✕), ô tổng, phân trang phía Python, xuất Excel đủ cột đúng bộ lọc | `app/xem_nguon.py`, `app/api.py`, `ui/src/DuLieuDaNap.tsx`, `CanDoi.tsx`, `BangChiTiet.tsx` |

## Test

**537 xanh** dưới `pytest -W error` (521 cũ + 16 mới ở `tests/test_file_gop.py`). Test mới ghi
Excel thật rồi đi qua loader → kho → đọc lại. Ba test cũ chỉ sửa hàm giả để nhận tham số `bao`.

## Kiểm thật (kho tạm, không chạm kho người dùng)

**Kỳ 09/2026, bảng kê A00 + sổ A01:** 8 khay tách đúng. C3.2/C3.4 của A01 ra **31 / 6 dòng**,
**y hệt 1.3.0**. Sổ phủ đủ, không có lời báo thiếu.

**Kỳ 10/2026, file thật của các khay** (sổ chưa chốt). Chưa có file T00 thật, nên ghép một
"T00" giả lập từ bảng kê C03 + C05 + A05 (59.983 dòng):

| Phép thử | Kết quả |
|---|---|
| Vân tay C03 từ file riêng so với C03 tách từ T00 (khác dtype) | **bằng nhau** |
| Nạp T00 + C03 riêng cùng lúc | C03 không nhân đôi (37.920 dòng). Báo "giống hệt nhau, dùng T00" |
| Chốt C03 từ T00, nạp lại từ file riêng | **KHỚP** (trước sửa: LỆCH giả toàn bộ) |
| Sổ gộp C03 + C05 tách theo Id | C03 6.752 / C05 3.413 dòng. **55 dòng / 35 CT không khớp** khay nào, được báo |
| Thời gian · RAM nạp T00 giả lập + C03 | 55 s · đỉnh ~755 MB (Python) |

55 dòng không khớp là chứng từ HC (bán thu tiền ngay) và vài HD có trong sổ nhưng không có trong
bảng kê. Sổ xuất muộn hơn bảng kê khoảng 15 phút, nên đây là chênh do độ tươi dữ liệu. Không dòng
nào thuế 0 nên C3.2 không đổi. Khay C03 kỳ 10 còn lệch "thuế trả lại" giữa sổ và bảng kê; lá chắn
độ tươi sẵn có đã báo, không liên quan đợt sửa này.

## Giới hạn còn lại

- Bảng kê **không có cột `Id`** thì không phát hiện được chồng file (cộng như cũ). Mọi bảng kê
  Bravo đã đo đều có `Id`.
- Sổ gộp bỏ phần không khớp khay nào; sổ riêng thì vẫn giữ nguyên cả file như 1.3.0.
- RAM: T00 thật (~360k dòng) ước vài GB khi nạp cùng các file khác. Nếu máy yếu thì nạp T00 một
  mình.
- Chưa có file T00 thật để đo khay lạ và thời gian thật.
- UI chưa được người dùng kiểm bằng mắt.
