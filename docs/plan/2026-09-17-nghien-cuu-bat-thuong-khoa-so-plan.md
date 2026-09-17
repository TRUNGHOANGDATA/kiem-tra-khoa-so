# Plan — Nhìn ra bất thường khi khóa sổ từ Bảng kê chứng từ + CĐPS

_2026-09-17. Trạng thái: chờ duyệt phạm vi/thứ tự trước khi code._

## 1. Nghiên cứu: kế toán thực tế soát gì trước khi khóa sổ

Tổng hợp từ hướng dẫn quy trình khóa sổ (TT200/TT24), bài soát CĐPS (Đức Minh, MISA,
Lê Ánh), nhận diện rủi ro trên CĐPS (htttdn) và tài liệu review trial balance (PICPA,
month-end close). Các nhóm kiểm tra chuẩn:

| # | Nhóm kiểm tra | Nội dung cốt lõi | Nguồn dữ liệu |
|---|---|---|---|
| A | **Toàn vẹn CĐPS** | Tổng Nợ = Có ở đầu kỳ / PS / cuối kỳ; **dư đầu + PS Nợ − PS Có = dư cuối** từng TK; TK cha = tổng con; **TK loại 5–9 dư cuối = 0** | CĐPS |
| B | **Tính chất số dư** | Loại 1–2 dư Nợ, loại 3–4 dư Có (trừ TK lưỡng tính); **quỹ 111/112 không âm**; **kho 15x không âm**; 214 không dư Nợ; 131 dư Có / 331 dư Nợ = cần rà; 1381/3381/3388 "chờ xử lý" phải về 0 | CĐPS |
| C | **Đối chiếu sổ ↔ CĐPS** | Tổng PS Nợ/Có từng TK từ bảng kê phải khớp PS trên CĐPS | Bảng kê + CĐPS |
| D | **Quan hệ đối ứng** | 211 − 214 = GTCL; có dư 211 thì phải có PS Có 214 (khấu hao); có dư 242 thì phải có phân bổ; xuất 155/156 phải có 632 tương ứng | CĐPS (+ bảng kê) |
| E | **Biến động kỳ** | Dư cuối / PS từng TK lệch lớn so với kỳ trước, không giải thích được | CĐPS nhiều kỳ |
| F | **Bút toán bất thường trong sổ** | Giao dịch lớn lệch mặt bằng, dồn ngày cuối kỳ, số tròn, cặp đối ứng hiếm, bút toán điều chỉnh sát ngày khóa | Bảng kê |
| G | **Bút toán cuối kỳ đủ chưa** | Khấu hao → phân bổ → lương/BH → trích trước → dự phòng → tập hợp CP → giá thành → giá vốn → kết chuyển → thuế → lãi/lỗ | Bảng kê |
| H | **Đối chiếu ngoài** | 111 vs sổ quỹ, 112 vs sao kê, 131/331 vs xác nhận công nợ, 133/3331 vs tờ khai GTGT | _Ngoài tầm tool_ (không có dữ liệu) |

Kết luận nghiên cứu quan trọng nhất: **hai lớp phát hiện mạnh nhất (A, B, D) đều dựa trên
số dư của CĐPS** — tool hiện có CĐPS trong kho nhưng chỉ dùng cho dư đầu 421 (C7.6).
Đây là khe hở lớn và rẻ nhất để lấp.

## 2. Đối chiếu với tool hiện có (41 check / 16 bước)

| Nhóm | Hiện có | Khe hở |
|---|---|---|
| A Toàn vẹn CĐPS | **Không có** | Toàn bộ |
| B Tính chất số dư | **Không có** (mọi check hiện tại chỉ nhìn phát sinh) | Toàn bộ |
| C Sổ ↔ CĐPS | Đã ghi trong spec CĐPS (để sau) | Chưa làm |
| D Quan hệ đối ứng | C4.4/C4.5 (621/622/627→154→155), C4.3 (632 đối ứng kho) | Thiếu 211↔214, 242↔phân bổ, 155/156↔632 |
| E Biến động kỳ | Chỉ có drift dữ liệu đã chốt (băm dòng) | Chưa so số dư/PS theo TK |
| F Bút toán bất thường | G6 chỉ **thống kê** (top 50, theo ngày, người lập) — không gắn cờ | Chưa có ngưỡng/cảnh báo |
| G Bút toán cuối kỳ | G5 + G7 + 16 bước — **khá đủ**; C7.1–C7.4 chỉ là checklist vì thiếu bằng chứng | Nâng cấp bằng CĐPS (xem D) |
| H Đối chiếu ngoài | — | Ngoài phạm vi; ghi rõ trong UI là "tự đối chiếu" |

Trình tự 16 bước hiện có **khớp** trình tự khóa sổ chuẩn. Bước còn thiếu so với quy trình
chuẩn: *kiểm kê quỹ/kho & xử lý chênh lệch* (1381/3381 về 0) và *CĐPS cân* — có thể thêm
như bước 17–18 (quyết định ở mục 5).

## 3. Đề xuất check mới (rule cụ thể, mức độ, nguồn)

Nguyên tắc (rút từ audit hôm nay): **chỉ ĐỎ khi bằng chứng trực tiếp**; nghi vấn → VÀNG;
suy luận mềm → THỐNG KÊ. Mọi check mới phải **hiệu chỉnh trên file 8 chi nhánh thật**
trước khi coi là xong (tránh lặp lại C1.5/C1.3).

### Nhóm G9 — Toàn vẹn CĐPS (nguồn: CĐPS đã nạp; chỉ chạy khi có CĐPS)
| Mã | Rule | Mức |
|---|---|---|
| C9.1 | Σ dư đầu Nợ ≠ Σ dư đầu Có, hoặc Σ PS Nợ ≠ Σ PS Có, hoặc Σ dư cuối Nợ ≠ Σ dư cuối Có (dòng lá) | ĐỎ |
| C9.2 | Từng TK lá: dư đầu(Nợ−Có) + PS Nợ − PS Có ≠ dư cuối(Nợ−Có) (ngưỡng làm tròn 1đ) | ĐỎ |
| C9.3 | TK cha ≠ Σ TK con (từng cột) | ĐỎ |
| C9.4 | TK loại 5/6/7/8/9 có dư cuối ≠ 0 (chưa kết chuyển hết — bằng chứng trực tiếp, mạnh hơn C5.1) | ĐỎ |

### Nhóm G10 — Tính chất số dư (nguồn: CĐPS dư cuối)
| Mã | Rule | Mức |
|---|---|---|
| C10.1 | 111/112 dư Có (quỹ/ngân hàng âm) | ĐỎ |
| C10.2 | 152/153/155/156/157 dư Có (âm kho) | ĐỎ |
| C10.3 | 214 dư Nợ; 211/213 dư Có | ĐỎ |
| C10.4 | Loại 1–2 dư Có hoặc loại 3–4 dư Nợ **ngoài danh sách lưỡng tính** (131, 138, 141, 331, 333, 334, 338, 341?, 412, 413, 421) | VÀNG |
| C10.5 | 131 dư Có / 331 dư Nợ (ứng trước — rà doanh thu/hóa đơn chưa ghi) | VÀNG |
| C10.6 | 1381/3381 (thiếu/thừa chờ xử lý) còn dư cuối kỳ | VÀNG |
| C10.7 | 3388/1388 dư lớn (> ngưỡng % tổng nguồn vốn) — nội dung không rõ | THỐNG KÊ |

### Nâng cấp G7 bằng CĐPS (từ checklist → cảnh báo có bằng chứng)
| Mã | Rule mới khi có CĐPS | Mức |
|---|---|---|
| C7.1 | dư 211/213 > 0 **và** PS Có 214 = 0 → có TSCĐ mà không khấu hao | VÀNG (thay TK) |
| C7.2 | dư đầu 242 > 0 **và** PS Có 242 = 0 → chưa phân bổ | VÀNG |
| C7.3 | có PS Có 334 **và** không có PS 338(2/3/4) → chưa trích BH/KPCĐ | VÀNG |
| C7.4/C7.7 | giữ THỐNG KÊ (không có bằng chứng phải trích) | TK |
Chưa nạp CĐPS → giữ hành vi checklist hiện tại (không đoán).

### Nhóm D bổ sung (quan hệ đối ứng)
| Mã | Rule | Mức |
|---|---|---|
| C4.7 | Có PS Có 155/156 (xuất bán) mà PS Nợ 632 = 0 hoặc < 50% giá trị xuất | VÀNG |

### Nhóm C — Đối chiếu bảng kê ↔ CĐPS (đã lên spec, nay ưu tiên hơn)
| Mã | Rule | Mức |
|---|---|---|
| C9.5 | Từng TK lá: Σ Amount Nợ / Có từ bảng kê ≠ PS Nợ / Có trên CĐPS (ngưỡng 1đ) | ĐỎ (một trong hai nguồn thiếu chứng từ) |

### Nhóm E — Biến động kỳ (cần ≥ 2 kỳ CĐPS trong kho)
| Mã | Rule | Mức |
|---|---|---|
| C11.1 | Dư cuối / PS từng TK lệch > X% **và** > Y đ so với kỳ trước (X=30%, Y theo % tổng tài sản; hiệu chỉnh trên dữ liệu) | THỐNG KÊ → VÀNG sau hiệu chỉnh |
| C11.2 | Biên lợi nhuận gộp (511 − 632)/511 đổi > Z điểm % so với kỳ trước | VÀNG |

### Nhóm F — Bút toán bất thường trong sổ (bảng kê; bắt đầu ở mức THỐNG KÊ)
| Mã | Rule | Mức |
|---|---|---|
| C6.6 | Tỷ trọng bút toán/giá trị ghi ngày cuối kỳ vượt ngưỡng (vd > 40% số dòng của kỳ) | **BỎ** |
| C6.7 | ~~Giao dịch > k × trung vị theo TK~~ → **Q3 + 30·IQR của chính TK** | THỐNG KÊ ✅ |
| C6.8 | Cặp đối ứng Nợ/Có hiếm (≤ 2 lần trong kỳ, gộp ở TK cấp 1) | THỐNG KÊ ✅ |

#### Kết quả hiệu chỉnh Đợt 3 trên file 8 chi nhánh 08/2026
- **C4.7 “xuất 155/156 không về 632” — BỎ.** 421–2.281 dòng/chi nhánh và toàn bộ hợp lệ:
  xuất NVL cho sản xuất (Nợ 621), điều chuyển kho (152/155/156), thiếu hụt (338), 627, 641.
  Chiều ngược lại đã có **C4.3** (Nợ 632 phải đối ứng TK kho hợp lệ) — đó mới là chiều có nghĩa.
- **C6.6 “dồn ngày cuối kỳ” — BỎ.** Sau khi loại kết chuyển, ngày cuối chiếm **4–9% số dòng**
  (trung bình một ngày trong tháng ≈ 4%) và **8–18,5% giá trị**. Không có sức phân biệt.
  Ngưỡng 40% của spec gốc không bao giờ chạm. Chỉ có nghĩa khi so với CHÍNH chi nhánh đó ở
  kỳ trước → chuyển sang **Đợt 4**.
- **C6.7 đổi thước đo.** “Gấp ≥ 100 lần trung vị” cho ra **cả 50 dòng đều là `1331`** ở A08:
  thuế GTGT đầu vào có trung vị 19.704đ nên mọi hóa đơn lớn đều “gấp hơn 1.000 lần”. Thay
  bằng **Q3 + 30·IQR** (ngưỡng tự co giãn theo độ phân tán của chính tài khoản), loại bút
  toán kết chuyển, tối đa 5 dòng mỗi TK → **23–50 dòng/chi nhánh**, nội dung đọc được.
- **C6.8 bỏ vế “không có ở kỳ đã chốt trước”** (chưa có kỳ chốt nào để so). Loại thêm cặp mà
  **cả hai vế đều là TK kết chuyển** (911/421, 154/622…) vì chúng luôn xuất hiện 1–2 lần mỗi
  kỳ → **24–66 cặp/chi nhánh**, ra đúng loại việc cần nhìn: bù trừ công nợ 2,27 tỷ, hoàn tiền
  đặt cọc 1,54 tỷ, chuyển công nợ, tách VAT.

## 4. Thứ tự làm (đề xuất)
1. **Đợt 1 — G9 + G10 + nâng C7.1/C7.2/C7.3** (dùng CĐPS sẵn có; giá trị cao nhất, rẻ nhất).
   Kèm: bước 17 "CĐPS cân & TK 5–9 về 0", bước 18 "Xử lý chênh lệch kiểm kê (1381/3381)".
2. **Đợt 2 — C9.5 đối chiếu bảng kê ↔ CĐPS + drift CĐPS** (hoàn tất spec CĐPS).
3. **Đợt 3 — C4.7 + nhóm F (thống kê có ngưỡng)**.
4. **Đợt 4 — nhóm E biến động kỳ** (khi đã có ≥ 2 kỳ CĐPS).

Mỗi đợt: TDD backend → **chạy trên file 8 chi nhánh thật, in verdict trước/sau** → người
dùng xác nhận không dương tính giả → mới build UI/commit. Cập nhật `test_api` (số nhóm 8 →
10) và memory (41 → ~55 check).

## 5. Quyết định — ĐÃ CHỐT (2026-09-17)
- **(a) Thứ tự: Đợt 1 → 2 → 3 → 4** như trên.
- **(b) TK lưỡng tính** (dư 2 chiều, KHÔNG báo ở C10.4) = danh sách TT200 **+ mở rộng**:
  `131, 138, 141, 331, 333, 334, 338, 412, 413, 421` **+ `3387, 136, 336, 244, 344`**
  (doanh thu chưa thực hiện; phải thu/phải trả nội bộ; ký cược ký quỹ — hay dư 2 chiều ở
  DN nhiều chi nhánh). Lưu thành hằng `TK_LUONG_TINH` một chỗ để sửa dễ.
- **(c) Thêm bước 17 & 18** vào trình tự khóa sổ → **18 bước**:
  - B17 "CĐPS cân & TK 5–9 đã về 0" (gắn C9.1/C9.2/C9.4)
  - B18 "Xử lý chênh lệch kiểm kê (1381/3381 về 0)" (gắn C10.6)
  - Kéo theo: sửa `test_api` (`len(trang_thai) == 16` → 18) và memory (16 → 18 bước).
- **(d) Nhóm H (đối chiếu ngoài): BỎ HẲN** — không đưa vào tool, không thêm mục tự xác
  nhận. Tool giữ nguyên tắc thuần dữ liệu có trong file.

## Nguồn tham khảo
- fast.com.vn — Khóa sổ kế toán là gì, quy trình theo quy định
- thuvienphapluat.vn — Trình tự khóa sổ kế toán từ 01/01/2025 (TT24/2024)
- taca.edu.vn — Quy trình khóa sổ và lập BCTC cuối kỳ theo tháng
- ketoanducminh.edu.vn — Cách kiểm tra chi tiết Bảng cân đối tài khoản
- amis.misa.vn — Hướng dẫn kiểm tra đối chiếu sổ sách kế toán
- ketoanleanh.edu.vn — Cách khắc phục khi CĐPS không cân
- htttdn.com — Nhận diện rủi ro trên bảng cân đối kế toán / cân đối phát sinh
- blog.picpa.org — Mastering the Trial Balance: key mistakes
- checkflow.io — Month-end close checklist (anomaly review)
