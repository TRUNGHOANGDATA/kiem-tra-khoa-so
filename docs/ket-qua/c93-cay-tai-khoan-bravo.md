# C9.3 theo cây tài khoản Bravo (Id/ParentId) — kho v6

Ngày: 2026-11-17

## Vấn đề

CĐPS tháng 10/2026 được xuất sâu hơn tháng trước (tới cấp 2). Từ đó C9.3 "Tài khoản cha ≠ tổng tài
khoản con" báo ✕ ĐỎ ở **12/14 khay**, ví dụ dòng 6277.

- **Nguyên nhân:** danh mục Bravo khai **62781/62782 ("chi phí bằng tiền khác") làm con của 6277**.
  Dòng 6277 trên CĐPS vì thế đã gồm cả 62781/62782. Tool lại nhận TK con theo **đầu số** ("6277…"),
  nên chỉ cộng 62771 + 62772 rồi kết luận lệch.
- **Số liệu không sai:** tổng 627 trên CĐPS khớp bảng kê từng đồng.
- Tháng 07–09 xuất tới cấp 1, chưa hiện 62781/62782, nên không gặp.

## Sửa

| Phần | File |
|---|---|
| `tk_cha()`: số hiệu TK cha theo cột `Id`/`ParentId` của Bravo; file thiếu hai cột này thì để trống | `app/cdps.py` |
| Kho **schema v6**: thêm cột `cdps.cha`, có migrate `ALTER TABLE` khi mở kho v5 | `app/kho/schema.py`, `ket_noi.py`, `luu_tru.py` |
| C9.3: có cây thì con = các dòng nhận nó làm cha **trực tiếp**; chưa có cây (CĐPS nạp trước v6) thì lùi về so theo đầu số như cũ | `app/checks/g9_toan_ven_cdps.py` |
| Nạp lại CĐPS có số liệu y hệt bản trong kho mà kho chưa có cột cha → tự ghi lại để bổ sung cây, không cần tick ghi đè | `app/api.py` |

**Kho v6 không mở được bằng bản app ≤ 1.5.0.** Bản cũ sẽ báo "Kho phiên bản 6 > tool 5 — hãy cập nhật tool".

## Kiểm

- 5 test mới: đọc cây, C9.3 theo cây, C9.3 vẫn bắt cha lệch thật, migrate v5 → v6, nạp lại bổ sung
  cột cha. **566 test xanh.**
- 38 file CĐPS thật (07–10/2026): 12 file trước báo giả nay về 0; 26 file vẫn 0.

## Ghi chú cho kế toán

Danh mục Bravo đang để 62781/62782 dưới 6277. Mọi báo cáo Bravo gom theo 6277/6278 sẽ dồn "chi phí
bằng tiền khác" vào "dịch vụ mua ngoài". Đây là cài đặt danh mục, không ảnh hưởng khóa sổ.
