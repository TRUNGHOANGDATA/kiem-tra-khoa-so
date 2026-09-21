# Thiết kế: Nút "Kiểm tra cập nhật" trong phần mềm

Ngày: 2026-09-21 · Trạng thái: chờ duyệt

## 1. Mục tiêu

Người dùng (nhân viên kế toán rải nhiều chi nhánh, dùng qua internet) bấm một nút
trong app để biết có bản mới không; nếu có thì **tự chọn** cài hay để sau. Bấm
"Cài" thì app tải bộ cài mới về và chạy, không phải tự đi tìm link.

## 2. Quyết định nền (đã chốt: Cách B)

Phân phối qua **GitHub Releases công khai, KHÔNG token**. Đổi lại, **bộ cài không
được nhúng dữ liệu tài chính thật**:

- Bộ cài **thôi nhúng CĐPS thật** (`1. Source/BANG CAN DOI PHAT SINH/*.xlsx`).
  Lần đầu chạy, người dùng nạp CĐPS như đã nạp bảng kê hằng tháng. Đây cũng dọn
  luôn *bẫy CĐPS cũ hơn bảng kê* (bản cài mang CĐPS đóng băng gây chẩn đoán sai).
- **Tên 8 chi nhánh** chuyển từ `tao_seed.py` (tracked) sang một file local
  `chi_nhanh.json` bị `.gitignore`, đọc lúc build. Repo public không còn mẩu
  thông tin công ty nào.
- Số liệu tài chính vốn **đã** nằm ngoài git (`.gitignore` loại `1. Source/`,
  `2. Report/`, `*.xlsx`, `/build/`) — không cần xoá lịch sử.

Repo: **một repo public** chứa cả mã nguồn lẫn release (source đã sạch số liệu).
Tham số triển khai duy nhất: slug repo, đặt trong hằng `KHO_PHAT_HANH` (mục 4).

## 3. Luồng người dùng

1. App khởi động → *nền, best-effort* hỏi phiên bản mới nhất. Có bản mới thì banner
   hiện dấu "●" cạnh nút cập nhật. Lỗi mạng → im lặng, không cản gì.
2. Người dùng bấm **Kiểm tra cập nhật** (luôn có trong banner):
   - Không có mạng / chưa có release → thông báo nhẹ ("Không kết nối được" /
     "Đang dùng bản mới nhất").
   - Có bản mới → hộp thoại: "Có bản **X.Y.Z**. [Cài ngay] [Để sau]" kèm mô tả
     release (nếu có).
3. Bấm **Cài ngay** → app tải `KiemTraKhoaSo-Setup-X.Y.Z.exe` về `%TEMP%`, chạy nó,
   rồi **tự thoát** (one-folder khoá file, phải thoát để cài đè). Inno cài đè
   per-user, xong người dùng mở lại app.

## 4. Thành phần

### 4.1 `app/cap_nhat.py` (mới, thuần Python, chỉ stdlib)

Không thêm phụ thuộc — dùng `urllib.request`/`json` (ponytail: stdlib đủ).

```
KHO_PHAT_HANH = "owner/ten-repo"   # slug GitHub, điền khi tạo repo
API_LATEST = f"https://api.github.com/repos/{KHO_PHAT_HANH}/releases/latest"
TEN_ASSET = "KiemTraKhoaSo-Setup"  # tiền tố tên file cài để nhận đúng asset

def _bo(v: str) -> tuple[int, ...]:
    "1.2.3 / v1.2.3 -> (1,2,3); phần không phải số -> 0"

def moi_hon(latest: str, hien_tai: str) -> bool:
    "so tuple số; latest > hien_tai"

def lay_ban_moi_nhat(timeout=6) -> dict:
    "Gọi API_LATEST (không auth). Trả:
       {'phien_ban': 'X.Y.Z', 'url_tai': '...', 'mo_ta': '...'} hoặc
       {'loi': '<thông điệp thân thiện>'}.
     Nuốt mọi ngoại lệ mạng/HTTP/JSON -> {'loi': ...}. Bỏ 'v' ở tag_name.
     Chọn asset đầu tiên tên bắt đầu bằng TEN_ASSET và .exe."

def tai_bo_cai(url: str, tien_do=None) -> str:
    "Tải về %TEMP%/<tên asset>, trả đường dẫn. Ghi ra file .part rồi đổi tên
     (không để lại file dở nếu đứt mạng)."
```

### 4.2 `app/api.py` (thêm 2 method vào `JsApi`)

```
def kiem_tra_cap_nhat(self, pb_hien_tai: str) -> dict:
    r = cap_nhat.lay_ban_moi_nhat()
    if "loi" in r: return r
    r["co_moi"] = cap_nhat.moi_hon(r["phien_ban"], pb_hien_tai)
    return r        # {co_moi, phien_ban, url_tai, mo_ta}

def tai_va_cai(self, url: str) -> dict:
    "Tải bộ cài (đẩy tiến độ qua evaluate_js như on_progress hiện có),
     os.startfile(path), rồi đóng cửa sổ (self._window.destroy()).
     Lỗi -> {'loi': ...}, KHÔNG đóng app."
```

Phiên bản đang chạy lấy từ UI (`__PHIEN_BAN__`) truyền vào — giữ nguyên
"MỘT nguồn VERSION", không cần bundle VERSION cho Python.

### 4.3 UI React (banner)

- Nút **Kiểm tra cập nhật** trong banner (cạnh mấy chip thống kê). Gọi
  `window.pywebview.api.kiem_tra_cap_nhat(__PHIEN_BAN__)`.
- Startup: `useEffect` gọi 1 lần best-effort để đặt badge "●" nếu `co_moi`.
- Có bản mới: hộp thoại nhỏ (dùng mẫu dialog sẵn có) với [Cài ngay]/[Để sau];
  [Cài ngay] gọi `tai_va_cai(url_tai)`, hiện tiến độ tải rồi app tự thoát.
- Mù màu: trạng thái phân biệt bằng chữ + ký hiệu (● / "Đã mới nhất" / "Không
  kết nối"), không chỉ bằng màu.

### 4.4 Đóng gói (`tools/tao_seed.py`, `tools/installer.iss`)

- `tao_seed.py`: **bỏ** vòng nạp CĐPS và bỏ copy CĐPS gốc. `QUY_DOI` đọc từ
  `chi_nhanh.json` (local, gitignore) thay vì hằng trong file. Seed còn: khung
  thư mục + `cau-hinh.json` + bảng quy đổi tên chi nhánh + 2 file ĐỌC TRƯỚC.
- `.gitignore`: thêm `chi_nhanh.json`.
- `installer.iss`: giữ nguyên (vẫn bundle `_seed`, nay không còn CĐPS).
- Quy trình phát hành mới (ghi vào `tools/DONG_GOI.md`): sửa `VERSION` → build →
  `gh release create vX.Y.Z build/Output/KiemTraKhoaSo-Setup-X.Y.Z.exe`.

## 5. Xử lý lỗi

| Tình huống | Hành vi |
|---|---|
| Không mạng / timeout / rate-limit | `{'loi': ...}`; startup im lặng; bấm tay hiện thông báo nhẹ |
| Chưa có release nào (404) | Coi như "đã mới nhất", không báo lỗi đỏ |
| Không tìm thấy asset .exe | `{'loi': 'Bản phát hành thiếu file cài'}` |
| Đứt mạng khi tải | Xoá file `.part`, `{'loi': ...}`, KHÔNG đóng app |
| `startfile` thất bại | `{'loi': ...}`, KHÔNG đóng app |

Nguyên tắc: cập nhật là tính năng phụ, **không bao giờ được làm app treo/chết**;
mọi lỗi nuốt gọn thành thông điệp.

## 6. Kiểm thử

- `tests/test_cap_nhat.py`:
  - `moi_hon`: 1.1.4>1.1.3, 1.2.0>1.1.9, bằng nhau→False, có 'v', đuôi lẻ.
  - `lay_ban_moi_nhat`: monkeypatch `urllib` trả JSON mẫu → parse đúng
    phiên_bản/url/mô_tả; ném lỗi mạng → `{'loi': ...}`; 404 → nhánh "đã mới nhất".
  - `tai_bo_cai`: ghi `.part` rồi đổi tên; đứt giữa chừng không để lại file đích.
  - **Không chạm mạng thật, không chạm kho thật** (ép tmp_path như quy ước test).
- `test_chay_tat_ca`: không đổi (updater tách khỏi pipeline check).

## 7. Ngoài phạm vi (YAGNI)

- Không cài nền im lặng (`/SILENT`) — chạy Inno bình thường, người dùng thấy rõ.
- Không delta/patch — tải trọn bộ cài, đơn giản và chắc.
- Không tự tải nền trước khi hỏi — chỉ tải khi bấm "Cài ngay".
- Không kênh beta/rollback — chỉ "mới nhất".
- Chưa đụng: chuyển repo private↔public là thao tác tay của người dùng khi tạo repo.
