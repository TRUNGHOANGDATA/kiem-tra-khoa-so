# Nâng cấp: Sẵn sàng cho Báo cáo quản trị (Nhóm 8) + nhận chi nhánh đa cột — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Các bước dùng checkbox (`- [ ]`).

**Goal:** Từ cơ chế file "BC QUẢN TRỊ" của kế toán tổng hợp, bổ sung (A) nhận diện chi nhánh đa cột và (B) Nhóm 8 kiểm tra dữ liệu Bravo đã **sẵn sàng để dựng báo cáo quản trị theo khoản mục chi phí (KMCP) & bộ phận** — bắt đúng nguyên nhân gốc của "chênh lệch" mà kế toán phải dò tay trong sheet CHECK.

**Architecture:** Sửa `loader.py` (chi nhánh đa cột + đọc thêm `ExpenseCatgCode`), thêm `app/checks/g8_bao_cao_quan_tri.py` theo khuôn mẫu G1–G7. **Không** đụng Tab A (16 bước khóa sổ giữ nguyên) — Nhóm 8 là chất lượng dữ liệu cho báo cáo, khác trục với các bước khóa sổ. Không thêm nguồn dữ liệu, không thêm dependency.

**Tech Stack:** Python 3.14, pandas 3.0, pytest (`-W error`).

**Spec:** cập nhật `docs/spec/2026-09-15-tool-kiem-tra-khoa-so-design.md` (thêm §Nhóm 8, §nguồn dữ liệu: cột chi nhánh & khoản mục).

**Tiền đề:** plan này nối tiếp nhánh `nhom-7-but-toan-cuoi-ky` (Nhóm 7 đã xong, 245 test xanh).

---

## Cơ chế file BC quản trị (đã mổ xẻ ngày 16/09)

File `VXHN_2607_BC QUAN TRI_KMCP_OK.xlsx` là **sản phẩm hạ nguồn** của kế toán tổng hợp, 5 sheet:
- **BKCT** — bảng kê chứng từ Bravo thô (87.623 dòng, 80 cột) — chính là loại file tool đang đọc.
- **BCQT / BC. Theo bộ phận** — báo cáo quản trị: phân loại lại chi phí theo **khoản mục (KMCP)** và **bộ phận**, cột là chi nhánh.
- **CHECK** — đối chiếu từng TK × chi nhánh: **Bravo vs Tổng hợp → Chênh lệch phải = 0**. Đang đầy `#REF!` (công thức liên sheet gãy), có chênh 0,36đ ở 622.

**Ba dữ kiện đo được (không phỏng đoán):**
1. Chi nhánh nằm ở cột **`Đơn vị`** (VXHN 87.008 / VXHO 615), **không có `BranchCode`**. Tính năng đa chi nhánh hiện tại key cứng vào `BranchCode` → không nhận ra file này.
2. Bravo khớp CHECK ở 621/622/627 (621 = 12.305.652.879) **nhưng lệch ở 641/642** (641: tool 2.011.546.443 vs CHECK 1.905.171.332). Cột "Tổng hợp" đã bị **tái phân loại** — **không tái tạo được** chỉ từ file Bravo. → Đối chiếu tự động đầy đủ (đọc sheet BCQT) là **spike riêng sau**, không nằm trong plan này.
3. Nguyên nhân gốc của chênh lệch **nằm ngay trong file Bravo**: dòng chi phí **thiếu mã khoản mục** hoặc **thiếu bộ phận** → rơi khỏi báo cáo. Đây là phần Nhóm 8 bắt.

**Số đo trên BKCT của file thật (để test đối chiếu):**

| TK | Dòng | Thiếu khoản mục | Có bộ phận | Thiếu bộ phận | C8.2 bắt (tự suy) |
|----|------|-----------------|-----------|---------------|-------------------|
| 621 | 11.012 | 0 | 0 | 11.012 | **0** (621 không dùng bộ phận) |
| 622 | 20 | 0 | 20 | 0 | 0 |
| 627 | 413 | 0 | 413 | 0 | 0 |
| 641 | 547 | 0 | 547 | 0 | 0 |
| 642 | 480 | 0 | 480 | 0 | 0 |
| 635/811 | 67 | 0 | 67 | 0 | 0 |

Công ty điền khoản mục 12.539/12.539 dòng chi phí → C8.1 = 0. Sổ sạch thì Nhóm 8 im.

---

## Global Constraints

- **Một file Bravo, trong kỳ, cấp 1** — như G7.
- **Không cảnh báo từ sự vắng mặt của bằng chứng** ([[tool-kiem-tra-khoa-so-suc-manh-bang-chung]]): C8.1/C8.2 chỉ bật khi công ty **thật sự dùng** khoản mục/bộ phận (có dòng đã điền). "Không dùng" → không phải lỗi.
- **C8.2 tự suy theo dữ liệu, theo TỪNG nhóm TK cấp 1**: chỉ bắt dòng thiếu bộ phận nếu chính nhóm TK đó có dòng khác **đã** điền bộ phận. Cách này tự động loại 621 (toàn bộ trống → nhóm 621 không dùng bộ phận), không cần khai cứng.
- **Không đụng Tab A** — 16 bước khóa sổ giữ nguyên; Nhóm 8 chỉ ở Tab B.
- Chạy được dưới `pytest -W error`; G8 nhận `df` một `DonVi` như mọi nhóm.

---

### Task 1: loader — chi nhánh đa cột + đọc `ExpenseCatgCode`

**Files:**
- Modify: `app/loader.py`
- Test: `tests/test_loader.py`, `tests/test_nhieu_chi_nhanh.py`

**Interfaces:**
- Đổi `COT_CHI_NHANH` (str) → `COT_CHI_NHANH` (tuple ưu tiên) = `("BranchCode", "Đơn vị")`.
- Thêm `"Đơn vị"` và `"ExpenseCatgCode"` vào `COT_CHUOI`.
- `ma_chi_nhanh(df)`: trả cột chi nhánh đầu tiên **có ít nhất một giá trị khác rỗng**; không có → `CHI_NHANH_KHONG_RO`.

- [ ] **Step 1: Test**

```python
# tests/test_nhieu_chi_nhanh.py
def test_nhan_chi_nhanh_tu_cot_don_vi_khi_khong_co_branchcode():
    import pandas as pd
    from app.loader import ma_chi_nhanh
    df = pd.DataFrame({"DebitAccount": ["621", "621"], "Đơn vị": ["VXHN", "VXHO"]})
    assert list(ma_chi_nhanh(df)) == ["VXHN", "VXHO"]

def test_branchcode_uu_tien_hon_don_vi():
    import pandas as pd
    from app.loader import ma_chi_nhanh
    df = pd.DataFrame({"BranchCode": ["A01", "A01"], "Đơn vị": ["VXHN", "VXHO"]})
    assert list(ma_chi_nhanh(df)) == ["A01", "A01"]   # BranchCode có giá trị -> dùng nó

def test_cot_branchcode_rong_thi_roi_xuong_don_vi():
    import pandas as pd
    from app.loader import ma_chi_nhanh, CHI_NHANH_KHONG_RO
    df = pd.DataFrame({"BranchCode": [None, None], "Đơn vị": ["VXHN", None]})
    assert list(ma_chi_nhanh(df)) == ["VXHN", CHI_NHANH_KHONG_RO]
```

- [ ] **Step 2: FAIL** (hiện `ma_chi_nhanh` chỉ đọc `BranchCode`).

- [ ] **Step 3: Sửa loader**

```python
COT_CHI_NHANH = ("BranchCode", "Đơn vị")   # thứ tự ưu tiên
CHI_NHANH_KHONG_RO = "(không có mã chi nhánh)"

def ma_chi_nhanh(df: pd.DataFrame) -> pd.Series:
    """Cột chi nhánh đã điền chỗ trống. Thử lần lượt các cột trong COT_CHI_NHANH,
    dùng cột ĐẦU TIÊN có ít nhất một giá trị khác rỗng — Bravo xuất chi nhánh khi
    thì ở 'BranchCode' (A01), khi thì ở cột tiếng Việt 'Đơn vị' (VXHN/VXHO)."""
    for cot in COT_CHI_NHANH:
        if cot not in df.columns:
            continue
        s = df[cot].astype("string").str.strip()
        s = s.mask(s.isna() | s.eq("") | s.str.upper().eq("NULL"))
        if s.notna().any():
            return s.fillna(CHI_NHANH_KHONG_RO).astype("object")
    return pd.Series(CHI_NHANH_KHONG_RO, index=df.index, dtype="object")
```

Thêm `"Đơn vị"`, `"ExpenseCatgCode"` vào `COT_CHUOI`. (chuan_hoa tự thêm cột rỗng nếu file thiếu → 082027 không có `Đơn vị` vẫn chạy.)

- [ ] **Step 4: PASS.** Chạy `tests/test_loader.py tests/test_nhieu_chi_nhanh.py -W error` — xanh (082027 vẫn tách theo BranchCode). Commit `feat(loader): nhan chi nhanh da cot (BranchCode/Don vi) + doc ExpenseCatgCode`.

---

### Task 2: G8 khung + C8.1 thiếu mã khoản mục

**Files:**
- Create: `app/checks/g8_bao_cao_quan_tri.py`
- Modify: `app/checks/__init__.py`, `app/checks/base.py` (TEN_COT)
- Test: `tests/test_g8_bao_cao_quan_tri.py`

**Interfaces:**
- `NHOM = "G8"`, `TK_BCQT = ("621","622","627","635","641","642","515","711","811")` (đúng phạm vi sheet CHECK), `kiem_tra(df, ctx) -> list[CheckResult]`.

- [ ] **Step 1: Test**

```python
# tests/test_g8_bao_cao_quan_tri.py
from app.checks import g8_bao_cao_quan_tri as g8
from tests.conftest import tao_df

def _kq(df, ctx): return {r.ma: r for r in g8.kiem_tra(df, ctx)}

def test_c81_bat_dong_chi_phi_thieu_khoan_muc(ctx):
    df = tao_df([
        {"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 100, "ExpenseCatgCode": "2001"},
        {"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 50,  "ExpenseCatgCode": None, "DocNo": "X"},
    ])
    r = _kq(df, ctx)["C8.1"]
    assert r.so_loi == 1 and r.muc_do_thuc == "vang"
    assert r.chi_tiet.iloc[0]["DocNo"] == "X"

def test_c81_khong_bat_khi_cong_ty_khong_dung_khoan_muc(ctx):
    """Absence-of-evidence: cả kỳ không dòng chi phí nào có khoản mục -> không kết luận."""
    df = tao_df([{"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 100, "ExpenseCatgCode": None}])
    assert _kq(df, ctx)["C8.1"].so_loi == 0

def test_c81_bo_qua_dong_khong_phai_chi_phi(ctx):
    df = tao_df([{"DebitAccount": "1111", "CreditAccount": "1121", "Amount": 100, "ExpenseCatgCode": None},
                 {"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 100, "ExpenseCatgCode": "2001"}])
    assert _kq(df, ctx)["C8.1"].so_loi == 0
```

- [ ] **Step 2: FAIL** (`ModuleNotFoundError`).

- [ ] **Step 3: Viết module**

```python
# app/checks/g8_bao_cao_quan_tri.py
"""Nhóm 8 — Sẵn sàng cho Báo cáo quản trị (khoản mục chi phí & bộ phận).

Báo cáo quản trị phân loại lại chi phí theo KHOẢN MỤC và BỘ PHẬN. Dòng chi phí
thiếu hai trục này sẽ rơi khỏi báo cáo -> chính là "chênh lệch" mà kế toán dò tay
trong sheet CHECK. Nhóm này bắt nguyên nhân đó ngay trên file Bravo.

Đúng luật "đừng cảnh báo từ sự vắng mặt": chỉ bật khi công ty THẬT SỰ dùng khoản
mục/bộ phận (có dòng đã điền). Công ty không dùng -> không phải lỗi.
"""
import pandas as pd

from .base import VANG, BoiCanh, CheckResult, bat_dau, tao_ket_qua

NHOM = "G8"
TK_BCQT = ("621", "622", "627", "635", "641", "642", "515", "711", "811")


def _trong(s: pd.Series) -> pd.Series:
    t = s.astype("string").str.strip()
    return t.isna() | t.eq("") | t.str.upper().eq("NULL")


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    kq = []
    la_cp = bat_dau(df["DebitAccount"], *TK_BCQT)
    thieu_km = la_cp & _trong(df["ExpenseCatgCode"])
    co_dung_km = bool((la_cp & ~_trong(df["ExpenseCatgCode"])).any())
    ct = df[thieu_km] if co_dung_km else df.iloc[0:0]
    kq.append(tao_ket_qua(ct, "C8.1", "Chi phí thiếu mã khoản mục (KMCP)", NHOM, VANG,
                          "Dòng chi phí không có mã khoản mục — sẽ rơi khỏi báo cáo quản trị theo khoản mục",
                          ghi_chu="" if co_dung_km else "Kỳ này không dùng khoản mục chi phí — không áp dụng"))
    return kq
```

- [ ] **Step 4: Đăng ký** `__init__.py`: import `g8_bao_cao_quan_tri`, `"G8": "Sẵn sàng báo cáo quản trị"` vào `TEN_NHOM`, `("G8", g8_bao_cao_quan_tri.kiem_tra)` vào `DANH_SACH`. `base.py`: thêm `"ExpenseCatgCode": "Mã khoản mục", "ExpenseCatgName": "Tên khoản mục"` vào `TEN_COT`.

- [ ] **Step 5: PASS. Commit** `feat(checks): G8 khung + C8.1 thieu khoan muc`.

---

### Task 3: C8.2 thiếu bộ phận (tự suy theo nhóm TK)

**Files:** Modify `g8_bao_cao_quan_tri.py`; Test tương ứng.

- [ ] **Step 1: Test**

```python
def test_c82_tu_suy_bo_phan_theo_nhom_tk(ctx):
    df = tao_df([
        # nhóm 642 CÓ dùng bộ phận -> dòng trống bộ phận của 642 bị bắt
        {"DebitAccount": "6421", "CreditAccount": "1111", "DeptName": "P.Kế toán", "Amount": 10},
        {"DebitAccount": "6422", "CreditAccount": "1111", "DeptName": None, "Amount": 20, "DocNo": "Y"},
        # nhóm 621 KHÔNG dùng bộ phận (toàn trống) -> không bắt (NVL trực tiếp)
        {"DebitAccount": "621", "CreditAccount": "1521", "DeptName": None, "Amount": 30},
        {"DebitAccount": "621", "CreditAccount": "1521", "DeptName": None, "Amount": 40},
    ])
    r = _kq(df, ctx)["C8.2"]
    assert r.so_loi == 1 and r.chi_tiet.iloc[0]["DocNo"] == "Y"

def test_c82_khong_bat_khi_ca_ky_khong_dung_bo_phan(ctx):
    df = tao_df([{"DebitAccount": "6421", "CreditAccount": "1111", "DeptName": None, "Amount": 10}])
    assert _kq(df, ctx)["C8.2"].so_loi == 0
```

- [ ] **Step 2: FAIL** (KeyError C8.2).

- [ ] **Step 3: Thêm vào `kiem_tra`** (trước `return`)

```python
    # Tự suy theo TỪNG nhóm TK cấp 1: chỉ nhóm nào có dòng đã điền bộ phận mới coi
    # là "công ty phân bổ bộ phận cho nhóm đó" -> dòng trống trong nhóm ấy mới là
    # thiếu sót. 621 (NVL trực tiếp) thường trống toàn bộ -> tự động không bị bắt.
    tk3 = df["DebitAccount"].astype("string").str.strip().str[:3]
    trong_dept = _trong(df["DeptName"])
    nhom_co_dept = set(tk3[la_cp & ~trong_dept].dropna())
    thieu_dept = la_cp & trong_dept & tk3.isin(nhom_co_dept)
    kq.append(tao_ket_qua(df[thieu_dept], "C8.2", "Chi phí thiếu bộ phận (theo nhóm TK có dùng)",
                          NHOM, VANG,
                          "Dòng chi phí thuộc nhóm TK có phân bổ bộ phận nhưng bỏ trống bộ phận"
                          " — sẽ rơi khỏi báo cáo theo bộ phận",
                          ghi_chu="Chỉ xét nhóm TK cấp 1 mà kỳ này có dòng đã điền bộ phận"))
```

- [ ] **Step 4: PASS. Commit** `feat(checks): C8.2 thieu bo phan (tu suy theo nhom TK)`.

---

### Task 4: C8.3 thống kê tổng hợp chi phí theo khoản mục × TK

**Files:** Modify `g8_bao_cao_quan_tri.py`; Test tương ứng.

**Interfaces:** `CheckResult(..., la_thong_ke=True)`; bảng cột `TK, ma_khoan_muc, ten_khoan_muc, so_dong, tong` — thay cột "Bravo" đầy `#REF!` của kế toán bằng số sạch.

- [ ] **Step 1: Test**

```python
def test_c83_tong_hop_theo_khoan_muc_tk(ctx):
    df = tao_df([
        {"DebitAccount": "6421", "CreditAccount": "1111", "ExpenseCatgCode": "2001",
         "ExpenseCatgName": "Thuê mặt bằng", "Amount": 100},
        {"DebitAccount": "6421", "CreditAccount": "1111", "ExpenseCatgCode": "2001",
         "ExpenseCatgName": "Thuê mặt bằng", "Amount": 50},
        {"DebitAccount": "627", "CreditAccount": "1111", "ExpenseCatgCode": "6233",
         "ExpenseCatgName": "Vật tư", "Amount": 30},
    ])
    r = _kq(df, ctx)["C8.3"]
    assert r.la_thong_ke
    hang = {(x["TK"], x["ma_khoan_muc"]): x for x in r.chi_tiet.to_dict("records")}
    assert hang[("642", "2001")]["tong"] == 150 and hang[("642", "2001")]["so_dong"] == 2
    assert hang[("627", "6233")]["tong"] == 30
```

- [ ] **Step 2: FAIL.**

- [ ] **Step 3: Thêm hàm gộp**

```python
    sub = df[la_cp].copy()
    sub["TK"] = tk3[la_cp]
    sub["ma_khoan_muc"] = sub["ExpenseCatgCode"].astype("string").str.strip()
    sub["ten_khoan_muc"] = sub["ExpenseCatgName"].astype("string").str.strip()
    if len(sub):
        bang = (sub.groupby(["TK", "ma_khoan_muc", "ten_khoan_muc"], dropna=False)
                .agg(so_dong=("Amount", "size"), tong=("Amount", "sum")).reset_index())
    else:
        bang = pd.DataFrame(columns=["TK", "ma_khoan_muc", "ten_khoan_muc", "so_dong", "tong"])
    kq.append(CheckResult("C8.3", "Tổng hợp chi phí theo khoản mục × tài khoản", NHOM, VANG,
                          bang, la_thong_ke=True))
```

Thêm nhãn `TEN_COT`: `"ma_khoan_muc": "Mã khoản mục", "ten_khoan_muc": "Tên khoản mục"`; và `"so_dong"/"tong"` đã có. Thêm `"tong"` vào `COT_SO_HIEN_THI` (đã có), `so_dong` (đã có).

- [ ] **Step 4: PASS. Commit** `feat(checks): C8.3 tong hop chi phi theo khoan muc x TK`.

---

### Task 5: Đồng bộ đếm (40 check / 8 nhóm) + nghiệm thu file thật

**Files:** `tests/test_chay_tat_ca.py`, `tests/test_du_lieu_bien.py`, `tests/test_api.py`; tạo `docs/ket-qua/them-nhom-8-bao-cao-quan-tri.md`.

- [ ] **Step 1:** `test_chay_tat_ca`: đổi tên `..._tra_40_check_...`; `len(kq) == 6+4+3+6+6+5+7+3`. `{r.nhom}` gồm `G8`.
- [ ] **Step 2:** `test_du_lieu_bien.py:14` → `== 40`. (số bước Tab A **giữ 16** — Nhóm 8 không thêm bước.)
- [ ] **Step 3:** `test_api.py` — `len(kq["nhom"]) == 8` (bước vẫn 16).
- [ ] **Step 4:** Chạy `pytest -W error` toàn bộ — xanh. `test_ket_luan` phải vẫn xanh (Nhóm 8 có C8.1/C8.2 mức VANG **thật**, nên sổ có dòng thiếu khoản mục sẽ ra "CẦN RÀ SOÁT" — đúng; nhưng kịch bản `SAN_SANG` không có TK chi phí thiếu khoản mục nên vẫn SẴN SÀNG. Xác nhận bằng chạy.)
- [ ] **Step 5:** Nghiệm thu: đọc sheet BKCT của file BC quản trị (hoặc file export thô có `Đơn vị`), xác nhận tách VXHN/VXHO; C8.1 = 0, C8.2 = 0 (khớp bảng số đo ở trên). Ghi nhật ký. Commit `test+docs: dong bo 40 check/8 nhom + nghiem thu Nhom 8`.

---

## Ngoài phạm vi (spike sau, không làm trong plan này)

- **Đối chiếu tự động Bravo ↔ Tổng hợp** (tái tạo sheet CHECK): cần đọc sheet BCQT layout riêng + logic tái phân loại 641/642 không suy được từ file Bravo. Làm spike riêng, đọc thẳng workbook nhiều sheet.
- **Đọc workbook nhiều sheet** (tự tìm sheet BKCT): tool hiện đọc sheet đầu; file BC quản trị để BKCT ở sheet thứ 3. Chỉ cần khi người dùng nạp thẳng workbook tổng hợp thay vì export thô.

## Self-Review

- **Spec coverage:** A (chi nhánh đa cột) → Task 1 ✔ · Nhóm 8 C8.1/C8.2/C8.3 → Task 2–4 ✔ · đếm 40/8 → Task 5 ✔ · nghiệm thu → Task 5 ✔.
- **Số liệu từ chạy thật** (Đơn vị VXHN/VXHO; C8.1=0; C8.2=0 nhờ tự-suy loại 621) — không phỏng đoán ✔.
- **Luật vắng-mặt-bằng-chứng:** C8.1 chỉ bật khi có dùng khoản mục; C8.2 chỉ bật cho nhóm TK có dùng bộ phận ✔.
- **Không phá Tab A / kết luận:** Nhóm 8 chỉ ở Tab B; C8.1/C8.2 là VANG thật (có bằng chứng trên dòng), C8.3 thống kê ✔.
- **Type consistency:** `tao_ket_qua` cho C8.1/C8.2 (cột chuẩn + ly_do); C8.3 bảng `{TK, ma_khoan_muc, ten_khoan_muc, so_dong, tong}` + nhãn TEN_COT ✔.
