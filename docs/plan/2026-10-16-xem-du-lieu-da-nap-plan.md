# Xem dữ liệu đã nạp (Sổ bán hàng · Bảng kê · CĐPS) + nhận sổ bán hàng gộp A00

Ngày: 2026-10-16 · Cập nhật 2026-11-17 (file gộp C00 / T00, §2.1; sửa theo red-team) · Trạng thái: **ĐÃ CODE**
(kết quả: `docs/ket-qua/file-gop-va-du-lieu-da-nap.md`) · Đích: **1.3.1** (một đợt, không chia phase)

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

**Cách làm (sửa sau red-team 17/11): TÁCH NGAY LÚC NẠP, kho không giữ file gộp.**

Bản trước định giữ nguyên file gộp trong kho rồi lọc theo Id mỗi lần kiểm. Red-team chỉ ra lối
đó hỏng ở 3 chỗ:
- Chốt sổ không đóng băng được phần sổ của khay, vì sổ chỉ được chép theo đúng mã khay.
- Mỗi lần mở danh sách phải giải nén cả chục bảng kê.
- Sổ 1.3.0 đã nạp (không có `Id`) rơi về ✓ giả.

Tách lúc nạp thì mọi thứ phía sau **giữ nguyên như 1.3.0**: kho vẫn lưu sổ theo từng khay × kỳ.

- **Thứ tự nạp:** sổ gộp cần bảng kê của kỳ đó **đã có trong kho**. Chưa có thì từ chối kèm câu
  "Nạp bảng kê kỳ MM/YYYY trước". Sổ riêng (mã khay trong tên file) nạp như 1.3.0.
- **`Id` ép cùng kiểu** (`Int64`) ở cả `loader.chuan_hoa` và `so_ban_hang.chuan_hoa`. Đo thật:
  sổ đọc bằng `dtype=str`, bảng kê đọc ra số, nên `isin` khớp **0/165** dòng.
- **Tách:** mỗi dòng sổ gán về khay có `Id` đó trong bảng kê cùng kỳ. Lưu từng phần bằng
  `luu_nguon(SO_BAN_HANG, khay, …)`, kèm tên file gộp.
- **Dòng không khớp khay nào** thì **đếm và báo** trong kết quả nạp (số dòng, số Id). Không được
  mặc định là "toàn hàng tặng": đo kỳ 10 có Id bán thu tiền ngay không nằm trong bảng kê nào.
- **Ghi đè có kiểm độ tươi:** khay × kỳ đã có sổ thì:
  - nội dung giống hệt → "giống", bỏ qua;
  - khác → chỉ ghi đè khi file mới có `mtime` **mới hơn**; ngược lại báo "file cũ hơn bản trong
    kho, bỏ qua".
  - Sửa luôn lỗi có sẵn: `tim_file_excel` trả file mới trước rồi file sau ghi đè, nên hiện **file
    cũ nhất thắng**.
- **Độ phủ:** khi kiểm, so tập Id bán hàng/trả lại (Nợ131/Có511, Nợ5213/Có131) của bảng kê với
  sổ. Thiếu Id thì C3.2/C3.4 ghi **thống kê "sổ không phủ đủ N chứng từ"**. Không ✓ khi sổ rỗng
  hoặc không phủ đủ.
- **Sổ trong kho không có `Id`** (nạp từ 1.3.0) vẫn dùng như cũ, vì đó là sổ riêng theo tên file.
  Chỉ sổ gộp mới cần `Id`.
- Bảng kê không có cột `Id` thì sổ gộp bị từ chối, sổ riêng vẫn nhận.

## 2.1 Từ kỳ 10/2026: file gộp A00 · C00 · T00

Bravo thêm khay C (C01–C06) từ kỳ 10/2026. Ngoài file gộp **A00**, người dùng còn xuất được
**C00** (gộp các khay C) và **T00** (gộp **cả A lẫn C**, nên T00 chứa lại toàn bộ A00 và C00).

**Nguyên tắc: tool chỉ soát sai lệch trên từng khay (`BranchCode`). File gộp chỉ là cái túi
đựng nhiều khay.** Tool không làm hợp nhất và không phân biệt pháp nhân A/C. C01 được kiểm y như A01.

**Đã đo 17/11 trên file 10/2026 thật** (sổ chưa chốt, chỉ đọc, kho không bị đụng tới):
- Khay C có cột **giống hệt** khay A, có `Id`. `BranchCode` ghi đúng mã khay.
- Khay A04–A08 kỳ 10 vẫn còn vài trăm dòng và được kiểm như mọi khay.
- **Loader không cần sửa** để nhận khay C.

**Mã gộp** = tên file mang mã thuộc danh sách cố định `{A00, C00, T00}`. Chỉ áp lên **tên file**,
không áp lên `BranchCode`, vì test hiện có dùng BranchCode "A00" như một khay thật.

**(a) Bảng kê chồng nhau.** Gom theo **(khay × kỳ)**, không theo khay. Hiện `1. Source` lẫn nhiều
tháng nên khay A01 của 3 tháng bị gộp làm một; lỗi này có sẵn, sửa luôn. Một (khay × kỳ) có ở
≥2 file mà trùng Id thì:
- Hai phần **giống hệt** (vân tay theo luật mới ở (d)) → giữ một, báo "A01 có ở A00 và T00,
  giống nhau, dùng A00".
- **Khác nhau** (xuất lệch giờ, xuất lại có thêm chứng từ) → **DỪNG nạp khay đó**, nêu tên hai
  file và số dòng mỗi bên. Không đoán file nào đúng. Luật cũ "giữ file ít dòng hơn" có thể giữ
  nhầm bản cũ: `1. Source` đang có 2 bản A00 kỳ 08.
- Không trùng Id (tách tay theo ngày) → cộng như cũ.
- **Dựng lại `nguon` (tên file, mtime) SAU khi chọn.** Nếu không, cảnh báo "CĐPS cũ hơn bảng kê"
  và màn xem sẽ ghi sai file.
- Thông báo trùng/dừng phải hiện **trên màn hình**, không chỉ nằm trong nhật ký Excel.

**(b) Sổ BH gộp:** tách lúc nạp như §2. Nạp cả A00 lẫn T00 thì phần A01 đi qua cùng một luật:
giống hệt thì bỏ qua, khác thì chỉ nhận file mới hơn. Không bao giờ có hai bản cùng khay × kỳ.

**(c) CĐPS gộp:** **bỏ qua khi nạp** và báo "CĐPS gộp, app cần CĐPS từng khay". Đã kiểm: không có
luồng nào dùng CĐPS gộp.

**(d) Vân tay chốt sổ không được phụ thuộc file chứa.**
- Đo tháng 07: A01 trong file riêng và A01 tách từ A00 khớp 87.623 dòng, cùng Id, PS lệch 0, mà
  vân tay vẫn KHÁC.
- Lý do: `WarehouseId` là int ở file riêng nhưng float ở file gộp, ra `"5"` khác `"5.0000"`.
- Hậu quả: đổi file chứa là bản đã chốt báo **LỆCH giả kèm diff toàn bộ**.
- Sửa `chot_so.chuoi_dong`: số có giá trị nguyên, dù int hay float, ra cùng một chuỗi.
- Bản chốt cũ lưu hash theo luật cũ, nên `doi_chieu` so hash đã lưu trước. Lệch thì **băm lại
  blob đã chốt bằng luật mới** rồi mới kết luận, để kỳ không đổi vẫn KHỚP.

**(e) Khay A99, T99: BỎ QUA** (người dùng chốt 17/11). Đây là đơn vị trung gian / điều chỉnh của
Bravo, không phải khay cần khóa sổ.
- Hằng `KHAY_BO_QUA = ("A99", "T99")` ở `loader.py`. Dòng mang các mã này bị loại **trước khi
  tách khay**: không thành đơn vị, không vào kho, không đòi CĐPS, không chặn nút Kiểm tra.
- Kết quả nạp ghi rõ "bỏ qua N dòng của A99/T99" để người dùng biết.
- Sổ BH: dòng có Id thuộc A99/T99 rơi vào nhóm "không khớp khay nào" (§2), vẫn được đếm.
- Dòng **không có** BranchCode giữ nguyên hành vi cũ (`CHI_NHANH_KHONG_RO`).

**Xuất file cho tool từ kỳ 10:** bảng kê + sổ BH chỉ cần **một file T00**, nạp bảng kê trước.
CĐPS xuất **từng khay** (A01–A08, C01–C06).

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

- **Sổ tách từ file gộp:** dòng nhãn ghi rõ "tách từ file gộp So chi tiet ban hang A00 …".
- **Phân trang phía Python**, 100 dòng/trang, giống `lay_chi_tiet`. Bảng kê A01 có 79k dòng
  × 80 cột, đẩy hết sang giao diện là treo.
- **Cột hiển thị bảng kê**: chỉ ~14 cột đọc được (Loại CT, Số CT, Ngày, Diễn giải, TK Nợ, TK
  Có, Số tiền, Khách hàng, Mã/Tên hàng, SL, Mã thuế, Loại GD, Người lập). Xuất Excel thì ra
  đủ cột.
- **Nhớ tạm khung đang xem**: giải nén một bảng kê mất ~2,7 s. Giữ 1 khung gần nhất trong bộ
  nhớ để lật trang, đổi lọc mà không giải nén lại. Khóa nhớ tạm gồm cả **thời điểm nạp**, để nạp
  lại xong thì không hiện khung cũ.
- Thuế = 0 hiện nhãn chữ trung tính **"thuế 0"**, không dùng ✕. ✕ nghĩa là lỗi, còn thuế 0 có
  thể là hàng tặng hoặc giao dịch chi nhánh. Không chỉ tô màu (người dùng mù màu).
- Nút header "Cân đối phát sinh" đổi thành **"Dữ liệu đã nạp"**.

**API mới** (`app/api.py`): `xem_nguon(loai, chi_nhanh, ky_nam, ky_thang, trang, kich_thuoc,
tim, loc_no, loc_co, chi_thue_0)` → `{tong, cot, nhan, cot_so, dong, tong_hop, nguon_file}` và
`xuat_nguon(...)` (cùng tham số, ra Excel). `chi_tiet_cdps` giữ nguyên.

## 4. Các bước (một đợt)

1. `loader.py` + `so_ban_hang.py`: ép `Id` về `Int64`. Thêm `la_ma_gop(ten_file)` và
   `KHAY_BO_QUA` (A99/T99, §2.1 e).
2. `chot_so.chuoi_dong`: chuẩn hóa số nguyên. `doi_chieu`: hash đã lưu lệch thì băm lại blob
   (§2.1 d).
3. `loader.doc_nhieu_bang_ke`:
   - gom theo (khay × kỳ);
   - xử lý chồng nhau theo §2.1 (a);
   - dựng `nguon` sau khi chọn;
   - trả danh sách trùng/dừng để UI hiện.
4. `api` nạp sổ BH:
   - tách sổ gộp theo Id của bảng kê trong kho;
   - ghi đè có kiểm độ tươi (sửa luôn lỗi file cũ thắng);
   - báo dòng không khớp khay nào.

   `cdps`: bỏ qua mã gộp.
5. `g3`: kiểm độ phủ Id; không phủ đủ thì ra thống kê "sổ không phủ đủ", không ✓ khi rỗng hoặc
   không phủ.
6. `api.py`: `xem_nguon` / `xuat_nguon` + nhớ tạm 1 khung. `report.py`: xuất bảng nguồn ra Excel.
7. UI: `CanDoi.tsx` → `DuLieuDaNap.tsx` (3 tab), đổi nút header, hiện cảnh báo trùng/dừng khi
   nạp; build.
8. Test (kho ép tmp_path). **Đi đường thật: ghi Excel → loader → kho → đọc lại**, không dựng
   frame cùng kiểu trong bộ nhớ.
   - Id sổ (chuỗi) và Id bảng kê (số) đọc từ Excel thật → khớp.
   - Cùng khay đọc từ file riêng và từ file gộp (cột int so với float) → vân tay KHỚP.
   - Bản chốt mang hash luật cũ, dữ liệu không đổi → vẫn KHỚP.
   - Bảng kê A00 + T00 giống nhau → A01 không nhân đôi. Khác nhau → dừng, nêu tên 2 file.
   - Một khay nằm ở 2 file không trùng Id → cộng đủ.
   - Hai tháng khác nhau → hai đơn vị, không gộp.
   - Sổ gộp khi kho chưa có bảng kê kỳ đó → từ chối.
   - Sổ gộp 2 khay trùng DocNo khác Id → tách đúng.
   - Sổ A00 rồi T00 (giống nhau) → "giống".
   - T00 cũ hơn bản trong kho → bỏ qua, có lời báo.
   - Sổ thiếu Id bán hàng → C3.2 ra thống kê "không phủ đủ", không ✓.
   - Chốt khay có sổ tách từ file gộp → snapshot có sổ.
   - CĐPS `T00 102026 …` → bỏ qua, kho không có chi nhánh T00.
   - Bảng kê có dòng A99/T99 → không thành khay, không chặn Kiểm tra, có báo số dòng bỏ qua.
   - `xem_nguon`: phân trang, lọc TK, lọc thuế 0, tổng đầu bảng; nạp lại thì không hiện khung cũ.
9. Kiểm thật. Dùng **kho tạm** (`api._thu_muc_kho = tempfile.mkdtemp()`), không chạm kho người
   dùng.
   - Bảng kê `092026 A00` + sổ `A00 092026`: C3.2/C3.4 của A01 phải **y hệt 1.3.0** (31 dòng /
     6 dòng).
   - Lấy số C3.2/C3.4 của 7 khay còn lại cho bảng kiểm §11 plan 15/10.
   - Kỳ 10/2026: nạp T00 một mình, rồi nạp T00 + A00 + C00 cùng lúc. `van_tay` từng khay phải
     **trùng nhau**.
   - Đo thời gian nạp và RAM. Đếm số dòng A99/T99 bị bỏ qua.
10. `pytest -W error`, nâng `VERSION` lên 1.3.1, viết docs `ket-qua`, build + phát hành theo quy
    trình cũ.

## 5. Không làm

- Sửa/xóa dữ liệu trong màn xem — màn này chỉ để đọc. Muốn đổi thì nạp lại file.
- Pivot / biểu đồ — xuất Excel là đủ để soát sâu.
- Đọc `Bang ke 632 GIA VON …` (file mới xuất 15/10) — chưa có check nào dùng, chờ yêu cầu.
- Hợp nhất A + C, phân biệt pháp nhân: tool không làm (người dùng chốt 17/11). Ghi nhận để
  sau: một số dòng TransCode chi nhánh (2303/2110) có đối tượng là khay C. C3.2 đang miễn VAT
  cho các dòng này theo TransCode.
