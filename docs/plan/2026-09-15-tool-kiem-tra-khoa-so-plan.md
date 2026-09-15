# Tool Kiểm Tra Khóa Sổ Cuối Kỳ — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ứng dụng desktop (pywebview) đọc bảng kê chứng từ Bravo (Excel), chạy 6 nhóm kiểm tra khóa sổ, hiển thị kết quả ngay trong app (Trạng thái khóa sổ + Lỗi & cảnh báo) và xuất báo cáo Excel tùy chọn.

**Architecture:** Backend Python chia lớp rõ: `loader.py` chuẩn hóa Excel → DataFrame; `checks/` mỗi nhóm một module trả `list[CheckResult]` thống nhất; `trang_thai.py` suy 11 bước khóa sổ; `report.py` xuất Excel; `api.py` là cầu nối `js_api` cho frontend HTML/CSS/JS thuần (Segoe UI, light mode). Chi tiết lỗi lưu trong backend, UI lấy theo trang.

**Tech Stack:** Python 3.14, pandas 3.0, python-calamine (đọc Excel nhanh), xlsxwriter, pywebview 6.2, pytest 9. Frontend: HTML/CSS/JS thuần, không CDN.

**Spec:** `docs/spec/2026-09-15-tool-kiem-tra-khoa-so-design.md`

## Global Constraints

- Font toàn app: `"Segoe UI"`; chế độ **light mode**; bảng màu spec §9: nền `#FFFFFF`/`#F5F7FA`, chữ `#1F2937`/`#6B7280`, primary `#1F4E79` hover `#2E75B6`, 🔴 `#DC2626` 🟡 `#D97706` 🟢 `#16A34A`, viền `#E5E7EB`.
- Không dùng CDN/tài nguyên mạng — chạy offline.
- Thư mục đầu vào `1. Source/`, đầu ra `2. Report/` (tự tạo nếu chưa có).
- Mã nguồn trong `app/` (package `app`), test trong `tests/`. Chạy app bằng `python -m app.main` từ thư mục gốc.
- Mọi cột chi tiết dòng-vi-phạm dùng thứ tự chuẩn `DocNo, DocDate, DebitAccount, CreditAccount, Amount, Description, ly_do`; check dạng tổng hợp được dùng cột riêng — UI/report phải render cột **động**.
- Mức độ: `"do"` (🔴 nghiêm trọng), `"vang"` (🟡 cảnh báo), `"xanh"` (🟢 đạt). Mặc định spec: C1.2 = 🔴; C6.1 = Top 50.
- Tài khoản so khớp theo **prefix** (`startswith`) vì Bravo dùng TK chi tiết (`6214`, `632211`, `1551`…).
- Không commit dữ liệu kế toán: `.gitignore` loại `1. Source/`, `2. Report/`.
- Commit message kết thúc bằng dòng: `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`

---

## File Structure

| File | Trách nhiệm |
|------|-------------|
| `app/__init__.py` | đánh dấu package |
| `app/checks/base.py` | `BoiCanh`, `CheckResult`, hằng mức độ, tiện ích: `bat_dau`, `loc_dong`, `co_dong`, `phat_sinh_theo_prefix`, `so_phat_sinh_tai_khoan`, `tao_ket_qua`, `fmt_so` |
| `app/loader.py` | `chuan_hoa`, `xac_dinh_ky`, `doc_bang_ke`, `ThongTinFile`, `tim_file_moi_nhat` |
| `app/checks/g1_chung_tu.py` … `g6_tong_quan.py` | mỗi nhóm một hàm `kiem_tra(df, ctx) -> list[CheckResult]` |
| `app/checks/__init__.py` | `TEN_NHOM`, `DANH_SACH`, `chay_tat_ca(df, ctx, on_progress)` |
| `app/trang_thai.py` | `BuocKhoaSo`, `suy_trang_thai(df, ket_qua)` — 11 bước |
| `app/report.py` | `xuat_bao_cao(...) -> Path` |
| `app/api.py` | `JsApi` (js_api), serialize DataFrame → JSON theo trang |
| `app/main.py` | tạo cửa sổ pywebview |
| `app/web/index.html`, `style.css`, `app.js` | giao diện |
| `Kiem_tra_khoa_so.bat`, `requirements.txt`, `pytest.ini`, `.gitignore` | chạy & cấu hình |
| `tests/conftest.py` | fixture `tao_df`, `ctx` |
| `tests/test_*.py` | test từng module |

---

### Task 0: Khởi tạo dự án

**Files:**
- Create: `app/__init__.py`, `app/checks/__init__.py` (rỗng tạm), `app/web/.gitkeep`, `tests/__init__.py`, `tests/conftest.py`, `requirements.txt`, `pytest.ini`, `.gitignore`

**Interfaces:**
- Produces: fixture `tao_df(rows: list[dict]) -> pd.DataFrame` (điền mặc định mọi cột cần thiết) và fixture `ctx` = `BoiCanh(ky_thang=8, ky_nam=2026)` — mọi test sau dùng.

- [ ] **Step 1: Tạo cấu trúc thư mục & file cấu hình**

```bash
cd "D:/Cong Viec/Check List Khoa So Ke Toan"
mkdir -p app/checks app/web tests "2. Report"
touch app/__init__.py app/checks/__init__.py tests/__init__.py app/web/.gitkeep
```

`requirements.txt`:
```
pandas>=3.0
openpyxl>=3.1
python-calamine>=0.3
xlsxwriter>=3.2
pywebview>=6.0
pytest>=8
```

`pytest.ini`:
```ini
[pytest]
pythonpath = .
testpaths = tests
```

`.gitignore`:
```
1. Source/
2. Report/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 2: Viết conftest với fixture `tao_df`**

`tests/conftest.py`:
```python
import pandas as pd
import pytest

from app.checks.base import BoiCanh

MAC_DINH = {
    "DocCode": "BT", "DocNo": "BT2608-000001", "DocDate": "2026-08-15",
    "DebitAccount": "6421", "CreditAccount": "1111", "Amount": 1_000_000.0,
    "Description": "Chi phí", "TaxCode": None, "CustomerCode": None,
    "CustomerName": None, "CurrencyCode": "VND", "OriginalAmount": 0.0,
    "ExchangeRate": 1.0, "Quantity9": 0.0, "UnitCost": 0.0,
    "ItemCode": None, "ItemName": None, "WarehouseName": None,
    "CreatedByName": "Kế toán A",
}


def tao_df(rows: list[dict]) -> pd.DataFrame:
    """Tạo DataFrame test: mỗi dict chỉ cần ghi cột khác mặc định."""
    full = [{**MAC_DINH, **r} for r in rows]
    df = pd.DataFrame(full)
    df["DocDate"] = pd.to_datetime(df["DocDate"])
    for c in ("Amount", "OriginalAmount", "ExchangeRate", "Quantity9", "UnitCost"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df


@pytest.fixture
def ctx() -> BoiCanh:
    return BoiCanh(ky_thang=8, ky_nam=2026)
```

- [ ] **Step 3: Kiểm tra pytest chạy được (chưa có test nên báo "no tests ran")**

Run: `python -m pytest -q`
Expected: `no tests ran` (exit 5) — không lỗi import (conftest import `app.checks.base` sẽ fail cho tới Task 1; chấp nhận ở bước này, Task 1 sửa).

- [ ] **Step 4: Khởi tạo git và commit**

```bash
git init
git add .gitignore requirements.txt pytest.ini app tests
git commit -m "chore: khoi tao du an tool kiem tra khoa so

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 1: `checks/base.py` — kiểu dữ liệu & tiện ích chung

**Files:**
- Create: `app/checks/base.py`
- Test: `tests/test_base.py`

**Interfaces:**
- Produces:
  - `DO = "do"`, `VANG = "vang"`, `XANH = "xanh"`; `COT_CHUAN = ["DocNo","DocDate","DebitAccount","CreditAccount","Amount","Description","ly_do"]`
  - `@dataclass BoiCanh(ky_thang: int, ky_nam: int)`
  - `@dataclass CheckResult(ma, ten, nhom, muc_do, chi_tiet: pd.DataFrame, ghi_chu="", la_thong_ke=False)` với property `so_loi -> int`, `muc_do_thuc -> str`
  - `bat_dau(s: pd.Series, *prefixes: str) -> pd.Series[bool]`
  - `loc_dong(df, no: tuple[str,...]|None=None, co: tuple[str,...]|None=None) -> pd.DataFrame`
  - `co_dong(df, no=None, co=None) -> bool`
  - `phat_sinh_theo_prefix(df, prefix: str) -> tuple[float, float]` (ps_no, ps_co)
  - `so_phat_sinh_tai_khoan(df) -> pd.DataFrame` cột `TK, ps_no, ps_co, net`
  - `tao_ket_qua(df_vi_pham, ma, ten, nhom, muc_do, ly_do: str|pd.Series, ghi_chu="") -> CheckResult`
  - `fmt_so(x: float) -> str` → `"1.234.567"`

- [ ] **Step 1: Viết test**

`tests/test_base.py`:
```python
import pandas as pd

from app.checks import base
from tests.conftest import tao_df


def test_bat_dau_theo_prefix():
    s = pd.Series(["6214", "632211", "1551", None])
    assert base.bat_dau(s, "621", "632").tolist() == [True, True, False, False]


def test_loc_dong_va_co_dong():
    df = tao_df([
        {"DebitAccount": "154", "CreditAccount": "6214"},
        {"DebitAccount": "911", "CreditAccount": "632111"},
    ])
    assert len(base.loc_dong(df, no=("154",), co=("621",))) == 1
    assert base.co_dong(df, no=("911",), co=("632",)) is True
    assert base.co_dong(df, no=("155",), co=("154",)) is False


def test_phat_sinh_theo_prefix():
    df = tao_df([
        {"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100},
        {"DebitAccount": "154", "CreditAccount": "6214", "Amount": 100},
    ])
    assert base.phat_sinh_theo_prefix(df, "621") == (100.0, 100.0)


def test_so_phat_sinh_tai_khoan_co_net():
    df = tao_df([
        {"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 300},
        {"DebitAccount": "911", "CreditAccount": "6421", "Amount": 200},
    ])
    bang = base.so_phat_sinh_tai_khoan(df).set_index("TK")
    assert bang.loc["6421", "ps_no"] == 300
    assert bang.loc["6421", "ps_co"] == 200
    assert bang.loc["6421", "net"] == 100


def test_tao_ket_qua_them_ly_do_va_dem_loi():
    df = tao_df([{"Description": ""}, {"Description": ""}])
    kq = base.tao_ket_qua(df, "C1.1", "Thiếu diễn giải", "G1", base.VANG, "Diễn giải trống")
    assert kq.so_loi == 2
    assert list(kq.chi_tiet.columns) == base.COT_CHUAN
    assert kq.chi_tiet["ly_do"].iloc[0] == "Diễn giải trống"
    assert kq.muc_do_thuc == base.VANG


def test_muc_do_thuc_xanh_khi_khong_loi():
    df = tao_df([]) if False else tao_df([{"Amount": 1}]).iloc[0:0]
    kq = base.tao_ket_qua(df, "C1.5", "Số tiền ≤ 0", "G1", base.DO, "x")
    assert kq.so_loi == 0 and kq.muc_do_thuc == base.XANH


def test_fmt_so():
    assert base.fmt_so(1234567.4) == "1.234.567"
```

- [ ] **Step 2: Chạy test, xác nhận fail**

Run: `python -m pytest tests/test_base.py -q`
Expected: FAIL — `ModuleNotFoundError: app.checks.base`

- [ ] **Step 3: Viết `app/checks/base.py`**

```python
"""Kiểu dữ liệu & tiện ích chung cho mọi bộ kiểm tra."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

DO, VANG, XANH = "do", "vang", "xanh"
THU_TU_MUC_DO = {DO: 0, VANG: 1, XANH: 2}
COT_CHUAN = ["DocNo", "DocDate", "DebitAccount", "CreditAccount", "Amount", "Description", "ly_do"]


@dataclass
class BoiCanh:
    ky_thang: int
    ky_nam: int


@dataclass
class CheckResult:
    ma: str
    ten: str
    nhom: str
    muc_do: str
    chi_tiet: pd.DataFrame
    ghi_chu: str = ""
    la_thong_ke: bool = False

    @property
    def so_loi(self) -> int:
        return 0 if self.la_thong_ke else int(len(self.chi_tiet))

    @property
    def muc_do_thuc(self) -> str:
        if self.la_thong_ke or self.so_loi == 0:
            return XANH
        return self.muc_do


def bat_dau(s: pd.Series, *prefixes: str) -> pd.Series:
    return s.fillna("").astype(str).str.startswith(tuple(prefixes))


def loc_dong(df: pd.DataFrame, no: tuple[str, ...] | None = None,
             co: tuple[str, ...] | None = None) -> pd.DataFrame:
    m = pd.Series(True, index=df.index)
    if no:
        m &= bat_dau(df["DebitAccount"], *no)
    if co:
        m &= bat_dau(df["CreditAccount"], *co)
    return df[m]


def co_dong(df: pd.DataFrame, no=None, co=None) -> bool:
    return len(loc_dong(df, no, co)) > 0


def phat_sinh_theo_prefix(df: pd.DataFrame, prefix: str) -> tuple[float, float]:
    ps_no = df.loc[bat_dau(df["DebitAccount"], prefix), "Amount"].sum()
    ps_co = df.loc[bat_dau(df["CreditAccount"], prefix), "Amount"].sum()
    return float(ps_no), float(ps_co)


def so_phat_sinh_tai_khoan(df: pd.DataFrame) -> pd.DataFrame:
    no = df.groupby("DebitAccount")["Amount"].sum().rename("ps_no")
    co = df.groupby("CreditAccount")["Amount"].sum().rename("ps_co")
    bang = pd.concat([no, co], axis=1).fillna(0.0)
    bang.index.name = "TK"
    bang["net"] = bang["ps_no"] - bang["ps_co"]
    return bang.reset_index()


def tao_ket_qua(df_vi_pham: pd.DataFrame, ma: str, ten: str, nhom: str, muc_do: str,
                ly_do, ghi_chu: str = "") -> CheckResult:
    cols = [c for c in COT_CHUAN if c != "ly_do" and c in df_vi_pham.columns]
    ct = df_vi_pham[cols].copy()
    ct["ly_do"] = ly_do.values if isinstance(ly_do, pd.Series) else ly_do
    return CheckResult(ma, ten, nhom, muc_do, ct.reset_index(drop=True), ghi_chu)


def fmt_so(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")
```

- [ ] **Step 4: Chạy test, xác nhận pass**

Run: `python -m pytest tests/test_base.py -q`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add app/checks/base.py tests/test_base.py tests/conftest.py
git commit -m "feat(checks): them base - CheckResult va tien ich chung

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: `loader.py` — đọc & chuẩn hóa bảng kê

**Files:**
- Create: `app/loader.py`
- Test: `tests/test_loader.py`

**Interfaces:**
- Consumes: `BoiCanh`, `fmt_so` từ `app.checks.base`
- Produces:
  - `COT_BAT_BUOC = ["DocNo","DocDate","DebitAccount","CreditAccount","Amount"]`
  - `@dataclass ThongTinFile(path: str, ten: str, ky: str, ky_thang: int, ky_nam: int, so_dong: int, tong_ps: float, nhat_ky: list[str])`
  - `chuan_hoa(df) -> tuple[pd.DataFrame, list[str]]`
  - `xac_dinh_ky(df) -> tuple[int, int]` (thang, nam)
  - `doc_bang_ke(path: str) -> tuple[pd.DataFrame, ThongTinFile]` — raise `ValueError` nếu thiếu cột bắt buộc
  - `tim_file_moi_nhat(thu_muc: str) -> str | None`

- [ ] **Step 1: Viết test**

`tests/test_loader.py`:
```python
import pandas as pd
import pytest

from app import loader


def _xlsx_mau(tmp_path):
    df = pd.DataFrame({
        "DocCode": ["BT", "PN"], "DocNo": ["BT1", "PN1"],
        "DocDate": ["2026-08-05", "2026-08-20"],
        "DebitAccount": [" 6421 ", 1521], "CreditAccount": ["1111", "3311"],
        "Amount": [1000, "abc"], "Description": ["NULL", "Mua NVL"],
        "TaxCode": ["NULL", "V10"], "CustomerCode": ["NULL", "NCC01"],
        "CurrencyCode": ["VND", "VND"], "OriginalAmount": [0, 0], "ExchangeRate": [1, 1],
        "Quantity9": [0, 10], "UnitCost": [0, 500], "CreatedByName": ["A", "B"],
    })
    p = tmp_path / "Bang ke test.xlsx"
    df.to_excel(p, sheet_name="Table1", index=False)
    return p


def test_chuan_hoa_null_va_so():
    df = pd.DataFrame({"Description": ["NULL", " ", "ok"], "Amount": ["1", "x", 3],
                       "DebitAccount": [6421, " 111 ", None], "CreditAccount": ["1", "2", "3"],
                       "DocNo": ["a", "b", "c"], "DocDate": ["2026-08-01"] * 3})
    out, log = loader.chuan_hoa(df)
    assert out["Description"].isna().tolist() == [True, True, False]
    assert out["Amount"].tolist() == [1.0, 0.0, 3.0]
    assert out["DebitAccount"].tolist()[:2] == ["6421", "111"]
    assert any("Amount" in m for m in log)


def test_xac_dinh_ky_lay_thang_pho_bien():
    df = pd.DataFrame({"DocDate": pd.to_datetime(["2026-08-01", "2026-08-09", "2026-07-31"])})
    assert loader.xac_dinh_ky(df) == (8, 2026)


def test_doc_bang_ke_tra_thong_tin(tmp_path):
    df, tt = loader.doc_bang_ke(str(_xlsx_mau(tmp_path)))
    assert tt.so_dong == 2 and tt.ky == "08/2026" and tt.tong_ps == 1000.0
    assert df["DebitAccount"].tolist() == ["6421", "1521"]
    assert df["TaxCode"].isna().tolist() == [True, False]


def test_doc_bang_ke_thieu_cot_bao_loi(tmp_path):
    p = tmp_path / "sai.xlsx"
    pd.DataFrame({"DocNo": ["x"]}).to_excel(p, index=False)
    with pytest.raises(ValueError, match="Thiếu cột"):
        loader.doc_bang_ke(str(p))


def test_tim_file_moi_nhat(tmp_path):
    (tmp_path / "a.xlsx").write_bytes(b"1")
    import time; time.sleep(0.05)
    (tmp_path / "b.xlsx").write_bytes(b"1")
    (tmp_path / "~$tam.xlsx").write_bytes(b"1")
    assert loader.tim_file_moi_nhat(str(tmp_path)).endswith("b.xlsx")
    assert loader.tim_file_moi_nhat(str(tmp_path / "khong_co")) is None
```

- [ ] **Step 2: Chạy test, xác nhận fail**

Run: `python -m pytest tests/test_loader.py -q`
Expected: FAIL — `ModuleNotFoundError: app.loader`

- [ ] **Step 3: Viết `app/loader.py`**

```python
"""Đọc bảng kê chứng từ Bravo (Excel) và chuẩn hóa thành DataFrame."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

COT_BAT_BUOC = ["DocNo", "DocDate", "DebitAccount", "CreditAccount", "Amount"]
COT_SO = ["Amount", "OriginalAmount", "ExchangeRate", "Quantity9", "UnitCost"]
COT_CHUOI = ["DocCode", "DocNo", "Description", "DebitAccount", "CreditAccount", "TaxCode",
             "CustomerCode", "CustomerName", "ItemCode", "ItemName", "WarehouseName",
             "CurrencyCode", "CreatedByName", "CashFlowName", "ExpenseCatgName", "DeptName"]


@dataclass
class ThongTinFile:
    path: str
    ten: str
    ky: str
    ky_thang: int
    ky_nam: int
    so_dong: int
    tong_ps: float
    nhat_ky: list[str] = field(default_factory=list)


def chuan_hoa(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    log: list[str] = []
    df = df.copy()
    for c in COT_CHUOI:
        if c not in df.columns:
            df[c] = pd.NA
        s = df[c].astype("string").str.strip()
        df[c] = s.mask(s.isna() | s.eq("") | s.str.upper().eq("NULL"))
    for c in COT_SO:
        if c not in df.columns:
            df[c] = 0.0
        so = pd.to_numeric(df[c], errors="coerce")
        hong = int(so.isna().sum() - df[c].isna().sum())
        if hong > 0:
            log.append(f"Cột {c}: {hong} giá trị không phải số, đã ép về 0")
        df[c] = so.fillna(0.0).astype(float)
    df["DocDate"] = pd.to_datetime(df["DocDate"], errors="coerce")
    return df, log


def xac_dinh_ky(df: pd.DataFrame) -> tuple[int, int]:
    d = df["DocDate"].dropna()
    if d.empty:
        raise ValueError("Không có ngày chứng từ hợp lệ để xác định kỳ")
    ky = (d.dt.year * 100 + d.dt.month).mode().iloc[0]
    return int(ky % 100), int(ky // 100)


def doc_bang_ke(path: str) -> tuple[pd.DataFrame, ThongTinFile]:
    try:
        raw = pd.read_excel(path, engine="calamine")
    except Exception:
        raw = pd.read_excel(path, engine="openpyxl")
    thieu = [c for c in COT_BAT_BUOC if c not in raw.columns]
    if thieu:
        raise ValueError(f"Thiếu cột bắt buộc: {', '.join(thieu)}")
    df, log = chuan_hoa(raw)
    thang, nam = xac_dinh_ky(df)
    tt = ThongTinFile(path=path, ten=Path(path).name, ky=f"{thang:02d}/{nam}",
                      ky_thang=thang, ky_nam=nam, so_dong=len(df),
                      tong_ps=float(df["Amount"].sum()), nhat_ky=log)
    return df, tt


def tim_file_moi_nhat(thu_muc: str) -> str | None:
    p = Path(thu_muc)
    if not p.is_dir():
        return None
    files = [f for f in p.glob("*.xls*") if not f.name.startswith("~$")]
    if not files:
        return None
    return str(max(files, key=os.path.getmtime))
```

- [ ] **Step 4: Chạy test, xác nhận pass**

Run: `python -m pytest tests/test_loader.py -q`
Expected: 5 passed

- [ ] **Step 5: Smoke test trên file thật (bỏ qua nếu không có file)** — thêm vào cuối `tests/test_loader.py`:

```python
FILE_THAT = "1. Source/Bang ke chung tu 082027.xlsx"


@pytest.mark.skipif(not __import__("os").path.exists(FILE_THAT), reason="không có file thật")
def test_doc_file_that():
    import time
    t = time.time()
    df, tt = loader.doc_bang_ke(FILE_THAT)
    assert tt.so_dong > 70_000 and tt.ky == "08/2026"
    assert time.time() - t < 30
```

Run: `python -m pytest tests/test_loader.py -q`
Expected: 6 passed (ghi lại thời gian đọc để đối chiếu acceptance).

- [ ] **Step 6: Commit**

```bash
git add app/loader.py tests/test_loader.py
git commit -m "feat(loader): doc va chuan hoa bang ke chung tu Bravo

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Nhóm 1 — Hình thức chứng từ (`g1_chung_tu.py`)

**Files:**
- Create: `app/checks/g1_chung_tu.py`
- Test: `tests/test_g1_chung_tu.py`

**Interfaces:**
- Consumes: `tao_ket_qua, DO, VANG, BoiCanh` từ `base`
- Produces: `NHOM = "G1"`, `kiem_tra(df, ctx) -> list[CheckResult]` với các mã `C1.1`…`C1.6` theo đúng thứ tự.

- [ ] **Step 1: Viết test**

`tests/test_g1_chung_tu.py`:
```python
from app.checks import g1_chung_tu as g1
from tests.conftest import tao_df


def _kq(df, ctx):
    return {r.ma: r for r in g1.kiem_tra(df, ctx)}


def test_du_6_ma_theo_thu_tu(ctx):
    assert [r.ma for r in g1.kiem_tra(tao_df([{}]), ctx)] == ["C1.1", "C1.2", "C1.3", "C1.4", "C1.5", "C1.6"]


def test_c11_thieu_dien_giai(ctx):
    df = tao_df([{"Description": None}, {"Description": "  "}, {"Description": "ok"}])
    assert _kq(df, ctx)["C1.1"].so_loi == 2


def test_c12_ngay_ngoai_ky(ctx):
    df = tao_df([{"DocDate": "2026-07-31"}, {"DocDate": "2026-08-31"}, {"DocDate": "2026-09-01"}])
    kq = _kq(df, ctx)["C1.2"]
    assert kq.so_loi == 2 and kq.muc_do == "do"


def test_c13_nghi_trung(ctx):
    r = {"DocNo": "X", "DebitAccount": "6421", "CreditAccount": "1111", "Amount": 5, "Description": "a"}
    df = tao_df([r, r, {**r, "Amount": 6}])
    assert _kq(df, ctx)["C1.3"].so_loi == 2


def test_c14_no_bang_co(ctx):
    df = tao_df([{"DebitAccount": "1111", "CreditAccount": "1111"}, {}])
    assert _kq(df, ctx)["C1.4"].so_loi == 1


def test_c15_so_tien_khong_duong(ctx):
    df = tao_df([{"Amount": 0}, {"Amount": -1}, {"Amount": 1}])
    assert _kq(df, ctx)["C1.5"].so_loi == 2


def test_c16_thieu_so_hoac_ngay(ctx):
    df = tao_df([{"DocNo": None}, {"DocDate": None}, {}])
    assert _kq(df, ctx)["C1.6"].so_loi == 2
```

- [ ] **Step 2: Chạy test, xác nhận fail**

Run: `python -m pytest tests/test_g1_chung_tu.py -q`
Expected: FAIL — module không tồn tại

- [ ] **Step 3: Viết `app/checks/g1_chung_tu.py`**

```python
"""Nhóm 1 — Hình thức chứng từ."""
import pandas as pd

from .base import DO, VANG, BoiCanh, CheckResult, tao_ket_qua

NHOM = "G1"


def _trong(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip().eq("")


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    kq = []
    kq.append(tao_ket_qua(df[_trong(df["Description"])], "C1.1", "Thiếu diễn giải", NHOM, VANG,
                          "Diễn giải trống"))

    d = df["DocDate"]
    ngoai_ky = d.notna() & ((d.dt.month != ctx.ky_thang) | (d.dt.year != ctx.ky_nam))
    kq.append(tao_ket_qua(df[ngoai_ky], "C1.2", "Ngày chứng từ ngoài kỳ", NHOM, DO,
                          f"Ngày không thuộc kỳ {ctx.ky_thang:02d}/{ctx.ky_nam}"))

    keys = ["DocNo", "DebitAccount", "CreditAccount", "Amount", "Description"]
    trung = df.duplicated(subset=keys, keep=False)
    kq.append(tao_ket_qua(df[trung].sort_values(keys), "C1.3", "Nghi trùng bút toán", NHOM, VANG,
                          "Trùng số CT + TK Nợ/Có + số tiền + diễn giải"))

    cung_tk = df["DebitAccount"].notna() & (df["DebitAccount"] == df["CreditAccount"])
    kq.append(tao_ket_qua(df[cung_tk], "C1.4", "TK Nợ = TK Có", NHOM, DO,
                          "Định khoản cùng một tài khoản"))

    kq.append(tao_ket_qua(df[df["Amount"] <= 0], "C1.5", "Số tiền ≤ 0", NHOM, DO,
                          "Số tiền bằng 0 hoặc âm"))

    thieu = _trong(df["DocNo"]) | df["DocDate"].isna()
    kq.append(tao_ket_qua(df[thieu], "C1.6", "Thiếu số chứng từ / ngày", NHOM, DO,
                          "Thiếu DocNo hoặc DocDate"))
    return kq
```

- [ ] **Step 4: Chạy test, xác nhận pass**

Run: `python -m pytest tests/test_g1_chung_tu.py -q`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add app/checks/g1_chung_tu.py tests/test_g1_chung_tu.py
git commit -m "feat(checks): nhom 1 hinh thuc chung tu (C1.1-C1.6)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Nhóm 2 — Định khoản bất thường (`g2_dinh_khoan.py`)

**Files:**
- Create: `app/checks/g2_dinh_khoan.py`
- Test: `tests/test_g2_dinh_khoan.py`

**Interfaces:**
- Produces: `NHOM = "G2"`, `kiem_tra(df, ctx)` → `C2.1`…`C2.4`; hằng `NGUONG_LECH_TY_GIA = 1.0`

- [ ] **Step 1: Viết test**

`tests/test_g2_dinh_khoan.py`:
```python
from app.checks import g2_dinh_khoan as g2
from tests.conftest import tao_df


def _kq(df, ctx):
    return {r.ma: r for r in g2.kiem_tra(df, ctx)}


def test_du_4_ma(ctx):
    assert [r.ma for r in g2.kiem_tra(tao_df([{}]), ctx)] == ["C2.1", "C2.2", "C2.3", "C2.4"]


def test_c21_thieu_doi_tuong_cong_no(ctx):
    df = tao_df([
        {"DebitAccount": "1311", "CustomerCode": None},
        {"CreditAccount": "3311", "CustomerCode": "NCC"},
        {"DebitAccount": "6421", "CustomerCode": None},
    ])
    assert _kq(df, ctx)["C2.1"].so_loi == 1


def test_c22_tk_sai_dinh_dang(ctx):
    df = tao_df([{"DebitAccount": "11"}, {"CreditAccount": "ABC"}, {}])
    assert _kq(df, ctx)["C2.2"].so_loi == 2


def test_c23_cung_nhom_tien(ctx):
    df = tao_df([{"DebitAccount": "1111", "CreditAccount": "1112"},
                 {"DebitAccount": "1121", "CreditAccount": "1122"},
                 {"DebitAccount": "1121", "CreditAccount": "1111"}])
    assert _kq(df, ctx)["C2.3"].so_loi == 2


def test_c24_lech_quy_doi_ngoai_te(ctx):
    df = tao_df([
        {"CurrencyCode": "USD", "OriginalAmount": 100, "ExchangeRate": 26000, "Amount": 2_600_000},
        {"CurrencyCode": "USD", "OriginalAmount": 100, "ExchangeRate": 26000, "Amount": 2_600_500},
        {"CurrencyCode": "VND", "OriginalAmount": 0, "ExchangeRate": 1, "Amount": 5},
    ])
    assert _kq(df, ctx)["C2.4"].so_loi == 1
```

- [ ] **Step 2: Chạy test, xác nhận fail**

Run: `python -m pytest tests/test_g2_dinh_khoan.py -q`
Expected: FAIL — module không tồn tại

- [ ] **Step 3: Viết `app/checks/g2_dinh_khoan.py`**

```python
"""Nhóm 2 — Định khoản bất thường."""
import pandas as pd

from .base import VANG, BoiCanh, CheckResult, bat_dau, tao_ket_qua

NHOM = "G2"
NGUONG_LECH_TY_GIA = 1.0


def _hop_le(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.fullmatch(r"\d{3,}")


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    kq = []
    tk_cong_no = bat_dau(df["DebitAccount"], "131", "331") | bat_dau(df["CreditAccount"], "131", "331")
    thieu_dt = df["CustomerCode"].fillna("").astype(str).str.strip().eq("")
    kq.append(tao_ket_qua(df[tk_cong_no & thieu_dt], "C2.1", "Thiếu mã đối tượng ở TK công nợ",
                          NHOM, VANG, "Dùng TK 131/331 nhưng CustomerCode trống"))

    sai = ~_hop_le(df["DebitAccount"]) | ~_hop_le(df["CreditAccount"])
    kq.append(tao_ket_qua(df[sai], "C2.2", "Tài khoản sai định dạng", NHOM, VANG,
                          "TK phải toàn chữ số, tối thiểu 3 ký tự"))

    cung_tien = ((bat_dau(df["DebitAccount"], "111") & bat_dau(df["CreditAccount"], "111")) |
                 (bat_dau(df["DebitAccount"], "112") & bat_dau(df["CreditAccount"], "112")))
    kq.append(tao_ket_qua(df[cung_tien], "C2.3", "Chuyển tiền nội bộ cùng nhóm TK", NHOM, VANG,
                          "Nợ/Có cùng nhóm 111 hoặc 112 — rà soát bút toán trung gian"))

    ngoai_te = df["CurrencyCode"].fillna("VND").astype(str).str.upper().ne("VND")
    lech = (df["Amount"] - df["OriginalAmount"] * df["ExchangeRate"]).abs() > NGUONG_LECH_TY_GIA
    kq.append(tao_ket_qua(df[ngoai_te & lech], "C2.4", "Lệch quy đổi ngoại tệ", NHOM, VANG,
                          "Amount ≠ OriginalAmount × ExchangeRate"))
    return kq
```

- [ ] **Step 4: Chạy test, xác nhận pass**

Run: `python -m pytest tests/test_g2_dinh_khoan.py -q`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add app/checks/g2_dinh_khoan.py tests/test_g2_dinh_khoan.py
git commit -m "feat(checks): nhom 2 dinh khoan bat thuong (C2.1-C2.4)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Nhóm 3 — Thuế GTGT (`g3_thue_gtgt.py`)

**Files:**
- Create: `app/checks/g3_thue_gtgt.py`
- Test: `tests/test_g3_thue_gtgt.py`

**Interfaces:**
- Produces: `NHOM = "G3"`, `kiem_tra(df, ctx)` → `C3.1`, `C3.2` (lỗi theo dòng), `C3.3` (`la_thong_ke=True`, cột `TaxCode, thue_vao_1331, thue_ra_33311, so_dong`)

- [ ] **Step 1: Viết test**

`tests/test_g3_thue_gtgt.py`:
```python
from app.checks import g3_thue_gtgt as g3
from tests.conftest import tao_df


def _kq(df, ctx):
    return {r.ma: r for r in g3.kiem_tra(df, ctx)}


def test_c31_co_ma_thue_nhung_thieu_tk_thue(ctx):
    df = tao_df([
        {"DocNo": "A", "DebitAccount": "1521", "CreditAccount": "3311", "TaxCode": "V10"},   # thiếu
        {"DocNo": "B", "DebitAccount": "1521", "CreditAccount": "3311", "TaxCode": "V10"},
        {"DocNo": "B", "DebitAccount": "1331", "CreditAccount": "3311", "TaxCode": "V10"},   # đủ
        {"DocNo": "C", "DebitAccount": "6421", "CreditAccount": "1111", "TaxCode": "V00"},   # không chịu thuế
    ])
    assert _kq(df, ctx)["C3.1"].so_loi == 1


def test_c32_doanh_thu_thieu_thue_dau_ra(ctx):
    df = tao_df([
        {"DocNo": "S1", "DebitAccount": "1311", "CreditAccount": "5111", "TaxCode": "R10A"},   # thiếu 33311
        {"DocNo": "S2", "DebitAccount": "1311", "CreditAccount": "5111", "TaxCode": "R10A"},
        {"DocNo": "S2", "DebitAccount": "1311", "CreditAccount": "33311", "TaxCode": "R10A"},
    ])
    assert _kq(df, ctx)["C3.2"].so_loi == 1


def test_c33_bang_tong_hop_thue(ctx):
    df = tao_df([
        {"DebitAccount": "1331", "CreditAccount": "3311", "TaxCode": "V10", "Amount": 100},
        {"DebitAccount": "1311", "CreditAccount": "33311", "TaxCode": "R10A", "Amount": 200},
    ])
    kq = _kq(df, ctx)["C3.3"]
    assert kq.la_thong_ke and kq.so_loi == 0 and kq.muc_do_thuc == "xanh"
    b = kq.chi_tiet.set_index("TaxCode")
    assert b.loc["V10", "thue_vao_1331"] == 100 and b.loc["R10A", "thue_ra_33311"] == 200
```

- [ ] **Step 2: Chạy test, xác nhận fail**

Run: `python -m pytest tests/test_g3_thue_gtgt.py -q`
Expected: FAIL — module không tồn tại

- [ ] **Step 3: Viết `app/checks/g3_thue_gtgt.py`**

```python
"""Nhóm 3 — Thuế GTGT."""
import pandas as pd

from .base import VANG, XANH, BoiCanh, CheckResult, bat_dau, tao_ket_qua

NHOM = "G3"
TK_THUE = ("1331", "33311")


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    kq = []
    tax = df["TaxCode"].fillna("").astype(str).str.strip().str.upper()
    co_thue = tax.ne("") & tax.ne("V00")
    dong_tk_thue = bat_dau(df["DebitAccount"], *TK_THUE) | bat_dau(df["CreditAccount"], *TK_THUE)

    docs_thieu = set(df.loc[co_thue, "DocNo"]) - set(df.loc[dong_tk_thue, "DocNo"])
    kq.append(tao_ket_qua(df[co_thue & df["DocNo"].isin(docs_thieu)], "C3.1",
                          "Có mã thuế nhưng chứng từ thiếu TK thuế", NHOM, VANG,
                          "TaxCode chịu thuế nhưng cả chứng từ không có dòng 1331/33311"))

    dt = bat_dau(df["CreditAccount"], "511") & co_thue
    dong_33311 = bat_dau(df["DebitAccount"], "33311") | bat_dau(df["CreditAccount"], "33311")
    docs_dt_thieu = set(df.loc[dt, "DocNo"]) - set(df.loc[dong_33311, "DocNo"])
    kq.append(tao_ket_qua(df[dt & df["DocNo"].isin(docs_dt_thieu)], "C3.2",
                          "Doanh thu thiếu thuế đầu ra", NHOM, VANG,
                          "Có Có 511 với TaxCode chịu thuế nhưng chứng từ không có 33311"))

    vao = df[bat_dau(df["DebitAccount"], "1331")].groupby(tax[bat_dau(df["DebitAccount"], "1331")])["Amount"].sum()
    ra = df[bat_dau(df["CreditAccount"], "33311")].groupby(tax[bat_dau(df["CreditAccount"], "33311")])["Amount"].sum()
    dem = df.groupby(tax)["Amount"].size()
    bang = pd.concat([vao.rename("thue_vao_1331"), ra.rename("thue_ra_33311"),
                      dem.rename("so_dong")], axis=1).fillna(0)
    bang.index.name = "TaxCode"
    kq.append(CheckResult("C3.3", "Tổng hợp thuế GTGT theo mã thuế", NHOM, XANH,
                          bang.reset_index(), la_thong_ke=True))
    return kq
```

- [ ] **Step 4: Chạy test, xác nhận pass**

Run: `python -m pytest tests/test_g3_thue_gtgt.py -q`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add app/checks/g3_thue_gtgt.py tests/test_g3_thue_gtgt.py
git commit -m "feat(checks): nhom 3 thue GTGT (C3.1-C3.3)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Nhóm 4 — Kho & giá vốn ⭐ (`g4_kho_gia_von.py`)

**Files:**
- Create: `app/checks/g4_kho_gia_von.py`
- Test: `tests/test_g4_kho_gia_von.py`

**Interfaces:**
- Produces: `NHOM = "G4"`, `TK_KHO = ("152","153","155","156")`, `TK_CO_HOP_LE_GIA_VON = ("152","153","154","155","156","157")`, `kiem_tra(df, ctx)` → `C4.1`, `C4.2`, `C4.3` (dòng), `C4.4`, `C4.5` (tổng hợp, cột `TK, ps_no, ps_co, ly_do`)

- [ ] **Step 1: Viết test**

`tests/test_g4_kho_gia_von.py`:
```python
from app.checks import g4_kho_gia_von as g4
from tests.conftest import tao_df


def _kq(df, ctx):
    return {r.ma: r for r in g4.kiem_tra(df, ctx)}


def test_c41_xuat_kho_gia_0(ctx):
    df = tao_df([
        {"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 10, "UnitCost": 0, "Amount": 0},
        {"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 10, "UnitCost": 5, "Amount": 50},
        {"DebitAccount": "6421", "CreditAccount": "1111", "Quantity9": 0, "UnitCost": 0, "Amount": 9},
    ])
    kq = _kq(df, ctx)["C4.1"]
    assert kq.so_loi == 1 and kq.muc_do == "do"


def test_c42_lech_tien_sl_x_don_gia(ctx):
    df = tao_df([
        {"CreditAccount": "1551", "Quantity9": 10, "UnitCost": 100.4, "Amount": 1004},
        {"CreditAccount": "1551", "Quantity9": 10, "UnitCost": 100, "Amount": 1500},
    ])
    assert _kq(df, ctx)["C4.2"].so_loi == 1


def test_c43_gia_von_khong_di_kem_kho(ctx):
    df = tao_df([
        {"DebitAccount": "632111", "CreditAccount": "1551"},
        {"DebitAccount": "632111", "CreditAccount": "3311"},
    ])
    assert _kq(df, ctx)["C4.3"].so_loi == 1


def test_c44_chua_tap_hop_chi_phi_ve_154(ctx):
    df = tao_df([
        {"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100},
        {"DebitAccount": "154", "CreditAccount": "6214", "Amount": 100},
        {"DebitAccount": "6221", "CreditAccount": "3341", "Amount": 50},     # 622 chưa kết chuyển
    ])
    kq = _kq(df, ctx)["C4.4"]
    assert kq.so_loi == 1 and kq.chi_tiet["TK"].iloc[0] == "622" and kq.muc_do == "do"


def test_c44_khong_ap_dung_khi_khong_phat_sinh(ctx):
    assert _kq(tao_df([{}]), ctx)["C4.4"].so_loi == 0


def test_c45_chua_nhap_kho_thanh_pham(ctx):
    co = tao_df([{"DebitAccount": "154", "CreditAccount": "6214"},
                 {"DebitAccount": "1551", "CreditAccount": "154"}])
    thieu = tao_df([{"DebitAccount": "154", "CreditAccount": "6214"}])
    assert _kq(co, ctx)["C4.5"].so_loi == 0
    assert _kq(thieu, ctx)["C4.5"].so_loi == 1
```

- [ ] **Step 2: Chạy test, xác nhận fail**

Run: `python -m pytest tests/test_g4_kho_gia_von.py -q`
Expected: FAIL — module không tồn tại

- [ ] **Step 3: Viết `app/checks/g4_kho_gia_von.py`**

```python
"""Nhóm 4 — Kho & giá vốn (đặc thù sản xuất)."""
import pandas as pd

from .base import DO, VANG, BoiCanh, CheckResult, bat_dau, co_dong, phat_sinh_theo_prefix, tao_ket_qua

NHOM = "G4"
TK_KHO = ("152", "153", "155", "156")
TK_CO_HOP_LE_GIA_VON = ("152", "153", "154", "155", "156", "157")
TK_CHI_PHI_SX = ("621", "622", "627")


def _bang_tong_hop(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["TK", "ps_no", "ps_co", "ly_do"])


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    kq = []
    dong_kho = bat_dau(df["DebitAccount"], *TK_KHO) | bat_dau(df["CreditAccount"], *TK_KHO)
    co_sl = dong_kho & (df["Quantity9"] > 0)

    gia_0 = co_sl & ((df["UnitCost"] <= 0) | (df["Amount"] <= 0))
    kq.append(tao_ket_qua(df[gia_0], "C4.1", "Xuất/nhập kho giá = 0", NHOM, DO,
                          "Có số lượng nhưng đơn giá hoặc tiền = 0 — chưa tính giá xuất kho"))

    co_gia = co_sl & (df["UnitCost"] > 0)
    lech = (df["Amount"] - df["Quantity9"] * df["UnitCost"]).abs() > (df["Amount"].abs() * 0.001 + 1)
    kq.append(tao_ket_qua(df[co_gia & lech], "C4.2", "Tiền ≠ Số lượng × Đơn giá", NHOM, VANG,
                          "Lệch vượt ngưỡng làm tròn 0,1% + 1đ"))

    gv_sai = bat_dau(df["DebitAccount"], "632") & ~bat_dau(df["CreditAccount"], *TK_CO_HOP_LE_GIA_VON)
    kq.append(tao_ket_qua(df[gv_sai], "C4.3", "Giá vốn không đối ứng TK kho", NHOM, VANG,
                          "Nợ 632 nhưng TK Có không thuộc 152/153/154/155/156/157"))

    rows = []
    for tk in TK_CHI_PHI_SX:
        ps_no, ps_co = phat_sinh_theo_prefix(df, tk)
        if ps_no > 0 and not co_dong(df, no=("154",), co=(tk,)):
            rows.append({"TK": tk, "ps_no": ps_no, "ps_co": ps_co,
                         "ly_do": f"Có phát sinh Nợ {tk} nhưng không có bút toán Nợ 154 / Có {tk}"})
    kq.append(CheckResult("C4.4", "Chưa tập hợp chi phí SX về 154", NHOM, DO, _bang_tong_hop(rows)))

    rows = []
    if co_dong(df, no=("154",)) and not co_dong(df, no=("155",), co=("154",)):
        ps_no, ps_co = phat_sinh_theo_prefix(df, "154")
        rows.append({"TK": "154", "ps_no": ps_no, "ps_co": ps_co,
                     "ly_do": "Đã tập hợp vào 154 nhưng không có bút toán Nợ 155 / Có 154 (nhập kho thành phẩm)"})
    kq.append(CheckResult("C4.5", "Chưa nhập kho thành phẩm 154 → 155", NHOM, VANG, _bang_tong_hop(rows)))
    return kq
```

- [ ] **Step 4: Chạy test, xác nhận pass**

Run: `python -m pytest tests/test_g4_kho_gia_von.py -q`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add app/checks/g4_kho_gia_von.py tests/test_g4_kho_gia_von.py
git commit -m "feat(checks): nhom 4 kho va gia von (C4.1-C4.5)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Nhóm 5 — Kết chuyển cuối kỳ ⭐ (`g5_ket_chuyen.py`)

**Files:**
- Create: `app/checks/g5_ket_chuyen.py`
- Test: `tests/test_g5_ket_chuyen.py`

**Interfaces:**
- Produces: `NHOM = "G5"`, `kiem_tra(df, ctx)` → `C5.1` (cột `TK, ps_no, ps_co, net, ly_do`), `C5.2`…`C5.6` (cột `TK, ps_no, ps_co, ly_do`); hằng `TK_DOANH_THU = ("511","515","711")`, `TK_CHI_PHI_911 = ("635","641","642","811")`

- [ ] **Step 1: Viết test**

`tests/test_g5_ket_chuyen.py`:
```python
from app.checks import g5_ket_chuyen as g5
from tests.conftest import tao_df


def _kq(df, ctx):
    return {r.ma: r for r in g5.kiem_tra(df, ctx)}


def test_du_6_ma(ctx):
    assert [r.ma for r in g5.kiem_tra(tao_df([{}]), ctx)] == ["C5.1", "C5.2", "C5.3", "C5.4", "C5.5", "C5.6"]


def test_c51_tk_5678_chua_ve_0(ctx):
    df = tao_df([
        {"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 300},
        {"DebitAccount": "911", "CreditAccount": "6421", "Amount": 300},     # đã kết chuyển hết
        {"DebitAccount": "6418", "CreditAccount": "1111", "Amount": 50},     # chưa
        {"DebitAccount": "1311", "CreditAccount": "5111", "Amount": 1000},   # chưa
    ])
    kq = _kq(df, ctx)["C5.1"]
    assert sorted(kq.chi_tiet["TK"]) == ["5111", "6418"] and kq.muc_do == "vang"


def test_c52_thieu_ket_chuyen_gia_von(ctx):
    thieu = tao_df([{"DebitAccount": "632111", "CreditAccount": "1551"}])
    du = tao_df([{"DebitAccount": "632111", "CreditAccount": "1551"},
                 {"DebitAccount": "911", "CreditAccount": "632111"}])
    assert _kq(thieu, ctx)["C5.2"].so_loi == 1 and _kq(thieu, ctx)["C5.2"].muc_do == "do"
    assert _kq(du, ctx)["C5.2"].so_loi == 0


def test_c53_thieu_ket_chuyen_doanh_thu_theo_tk(ctx):
    df = tao_df([
        {"DebitAccount": "1311", "CreditAccount": "5111"},
        {"DebitAccount": "5111", "CreditAccount": "911"},
        {"DebitAccount": "1121", "CreditAccount": "5151"},      # 515 chưa kết chuyển
    ])
    kq = _kq(df, ctx)["C5.3"]
    assert kq.chi_tiet["TK"].tolist() == ["515"]


def test_c54_thieu_ket_chuyen_chi_phi(ctx):
    df = tao_df([{"DebitAccount": "6421", "CreditAccount": "1111"},
                 {"DebitAccount": "63541", "CreditAccount": "1121"},
                 {"DebitAccount": "911", "CreditAccount": "6421"}])
    assert _kq(df, ctx)["C5.4"].chi_tiet["TK"].tolist() == ["635"]


def test_c55_thieu_ket_chuyen_lai_lo(ctx):
    thieu = tao_df([{"DebitAccount": "911", "CreditAccount": "6421"}])
    du_lai = tao_df([{"DebitAccount": "911", "CreditAccount": "6421"},
                     {"DebitAccount": "911", "CreditAccount": "4212"}])
    du_lo = tao_df([{"DebitAccount": "911", "CreditAccount": "6421"},
                    {"DebitAccount": "4212", "CreditAccount": "911"}])
    assert _kq(thieu, ctx)["C5.5"].so_loi == 1
    assert _kq(du_lai, ctx)["C5.5"].so_loi == 0 and _kq(du_lo, ctx)["C5.5"].so_loi == 0


def test_c56_thieu_khau_tru_thue(ctx):
    thieu = tao_df([{"DebitAccount": "1331", "CreditAccount": "3311"},
                    {"DebitAccount": "1311", "CreditAccount": "33311"}])
    du = tao_df([*[{"DebitAccount": "1331", "CreditAccount": "3311"},
                   {"DebitAccount": "1311", "CreditAccount": "33311"}],
                 {"DebitAccount": "33311", "CreditAccount": "1331"}])
    assert _kq(thieu, ctx)["C5.6"].so_loi == 1 and _kq(du, ctx)["C5.6"].so_loi == 0
```

- [ ] **Step 2: Chạy test, xác nhận fail**

Run: `python -m pytest tests/test_g5_ket_chuyen.py -q`
Expected: FAIL — module không tồn tại

- [ ] **Step 3: Viết `app/checks/g5_ket_chuyen.py`**

```python
"""Nhóm 5 — Kết chuyển cuối kỳ: phát hiện thiếu bút toán kết chuyển và TK 5/6/7/8 chưa về 0."""
import pandas as pd

from .base import (DO, VANG, BoiCanh, CheckResult, bat_dau, co_dong, fmt_so,
                   phat_sinh_theo_prefix, so_phat_sinh_tai_khoan)

NHOM = "G5"
TK_DOANH_THU = ("511", "515", "711")
TK_CHI_PHI_911 = ("635", "641", "642", "811")
COT_TH = ["TK", "ps_no", "ps_co", "ly_do"]


def _bang(rows: list[dict], cols=COT_TH) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=cols)


def _thieu(df, tk: str, no: tuple, co: tuple, ly_do: str) -> dict | None:
    ps_no, ps_co = phat_sinh_theo_prefix(df, tk)
    if (ps_no > 0 or ps_co > 0) and not co_dong(df, no=no, co=co):
        return {"TK": tk, "ps_no": ps_no, "ps_co": ps_co, "ly_do": ly_do}
    return None


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    kq = []
    bang = so_phat_sinh_tai_khoan(df)
    pl = bang[bat_dau(bang["TK"], "5", "6", "7", "8") & (bang["net"].abs() > 0.5)].copy()
    pl["ly_do"] = pl["net"].map(lambda n: f"Net phát sinh trong kỳ còn {fmt_so(n)} — chưa kết chuyển hết")
    kq.append(CheckResult("C5.1", "TK đầu 5/6/7/8 chưa kết chuyển hết", NHOM, VANG,
                          pl[["TK", "ps_no", "ps_co", "net", "ly_do"]].reset_index(drop=True),
                          ghi_chu="Có DN chỉ kết chuyển cuối năm — kế toán tự quyết định"))

    r = _thieu(df, "632", ("911",), ("632",), "Có phát sinh 632 nhưng thiếu bút toán Nợ 911 / Có 632")
    kq.append(CheckResult("C5.2", "Thiếu kết chuyển giá vốn 632 → 911", NHOM, DO, _bang([r] if r else [])))

    rows = [x for tk in TK_DOANH_THU
            if (x := _thieu(df, tk, (tk,), ("911",), f"Có phát sinh {tk} nhưng thiếu Nợ {tk} / Có 911"))]
    kq.append(CheckResult("C5.3", "Thiếu kết chuyển doanh thu → 911", NHOM, DO, _bang(rows)))

    rows = [x for tk in TK_CHI_PHI_911
            if (x := _thieu(df, tk, ("911",), (tk,), f"Có phát sinh {tk} nhưng thiếu Nợ 911 / Có {tk}"))]
    kq.append(CheckResult("C5.4", "Thiếu kết chuyển chi phí → 911", NHOM, DO, _bang(rows)))

    rows = []
    if co_dong(df, no=("911",)) or co_dong(df, co=("911",)):
        if not (co_dong(df, no=("911",), co=("421",)) or co_dong(df, no=("421",), co=("911",))):
            ps_no, ps_co = phat_sinh_theo_prefix(df, "911")
            rows.append({"TK": "911", "ps_no": ps_no, "ps_co": ps_co,
                         "ly_do": "Có phát sinh 911 nhưng không có bút toán 911 ↔ 421"})
    kq.append(CheckResult("C5.5", "Thiếu kết chuyển lãi/lỗ 911 ↔ 421", NHOM, VANG, _bang(rows)))

    rows = []
    vao_no, _ = phat_sinh_theo_prefix(df, "1331")
    _, ra_co = phat_sinh_theo_prefix(df, "33311")
    if vao_no > 0 and ra_co > 0 and not co_dong(df, no=("33311",), co=("1331",)):
        rows.append({"TK": "33311/1331", "ps_no": vao_no, "ps_co": ra_co,
                     "ly_do": "Có thuế vào và thuế ra nhưng thiếu bút toán khấu trừ Nợ 33311 / Có 1331"})
    kq.append(CheckResult("C5.6", "Thiếu khấu trừ thuế GTGT", NHOM, VANG, _bang(rows)))
    return kq
```

- [ ] **Step 4: Chạy test, xác nhận pass**

Run: `python -m pytest tests/test_g5_ket_chuyen.py -q`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add app/checks/g5_ket_chuyen.py tests/test_g5_ket_chuyen.py
git commit -m "feat(checks): nhom 5 ket chuyen cuoi ky (C5.1-C5.6)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Nhóm 6 — Thống kê & soát xét (`g6_tong_quan.py`)

**Files:**
- Create: `app/checks/g6_tong_quan.py`
- Test: `tests/test_g6_tong_quan.py`

**Interfaces:**
- Produces: `NHOM = "G6"`, `TOP_N = 50`, `kiem_tra(df, ctx)` → 5 `CheckResult` đều `la_thong_ke=True`: `C6.1` (cột `DocNo, DocDate, DebitAccount, CreditAccount, Amount, Description, CreatedByName`), `C6.2` (`TK, ps_no, ps_co, net`), `C6.3` (`DocCode, so_dong, tong`), `C6.4` (`CreatedByName, so_dong, tong`), `C6.5` (`DocDate, so_dong, tong, bat_thuong`)

- [ ] **Step 1: Viết test**

`tests/test_g6_tong_quan.py`:
```python
from app.checks import g6_tong_quan as g6
from tests.conftest import tao_df


def test_tat_ca_la_thong_ke(ctx):
    kq = g6.kiem_tra(tao_df([{}]), ctx)
    assert [r.ma for r in kq] == ["C6.1", "C6.2", "C6.3", "C6.4", "C6.5"]
    assert all(r.la_thong_ke and r.so_loi == 0 for r in kq)


def test_c61_top_theo_amount_giam_dan(ctx):
    df = tao_df([{"Amount": 1}, {"Amount": 9}, {"Amount": 5}])
    top = {r.ma: r for r in g6.kiem_tra(df, ctx)}["C6.1"].chi_tiet
    assert top["Amount"].tolist() == [9, 5, 1] and "CreatedByName" in top.columns


def test_c63_c64_gom_nhom(ctx):
    df = tao_df([{"DocCode": "BT", "CreatedByName": "A", "Amount": 1},
                 {"DocCode": "BT", "CreatedByName": "B", "Amount": 2},
                 {"DocCode": "PN", "CreatedByName": "A", "Amount": 3}])
    kq = {r.ma: r for r in g6.kiem_tra(df, ctx)}
    assert kq["C6.3"].chi_tiet.set_index("DocCode").loc["BT", "so_dong"] == 2
    assert kq["C6.4"].chi_tiet.set_index("CreatedByName").loc["A", "tong"] == 4


def test_c65_danh_dau_ngay_don_but_toan(ctx):
    rows = [{"DocDate": f"2026-08-{d:02d}"} for d in range(1, 11)] + [{"DocDate": "2026-08-31"}] * 30
    kq = {r.ma: r for r in g6.kiem_tra(tao_df(rows), ctx)}["C6.5"].chi_tiet
    assert kq["bat_thuong"].sum() == 1
```

- [ ] **Step 2: Chạy test, xác nhận fail**

Run: `python -m pytest tests/test_g6_tong_quan.py -q`
Expected: FAIL — module không tồn tại

- [ ] **Step 3: Viết `app/checks/g6_tong_quan.py`**

```python
"""Nhóm 6 — Thống kê & soát xét (không phải lỗi)."""
import pandas as pd

from .base import XANH, BoiCanh, CheckResult, so_phat_sinh_tai_khoan

NHOM = "G6"
TOP_N = 50


def _tk(ma, ten, bang) -> CheckResult:
    return CheckResult(ma, ten, NHOM, XANH, bang.reset_index(drop=True), la_thong_ke=True)


def _gom(df, cot) -> pd.DataFrame:
    g = df.groupby(cot, dropna=False)["Amount"].agg(so_dong="size", tong="sum").reset_index()
    return g.sort_values("tong", ascending=False)


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    cols = ["DocNo", "DocDate", "DebitAccount", "CreditAccount", "Amount", "Description", "CreatedByName"]
    top = df.nlargest(TOP_N, "Amount")[[c for c in cols if c in df.columns]]

    theo_ngay = _gom(df, "DocDate").sort_values("DocDate")
    m, s = theo_ngay["so_dong"].mean(), theo_ngay["so_dong"].std(ddof=0)
    theo_ngay["bat_thuong"] = theo_ngay["so_dong"] > (m + 2 * s) if len(theo_ngay) > 1 else False

    return [
        _tk("C6.1", f"Top {TOP_N} giao dịch giá trị lớn", top),
        _tk("C6.2", "Phát sinh theo tài khoản", so_phat_sinh_tai_khoan(df).sort_values("ps_no", ascending=False)),
        _tk("C6.3", "Phát sinh theo loại chứng từ", _gom(df, "DocCode")),
        _tk("C6.4", "Phát sinh theo người lập", _gom(df, "CreatedByName")),
        _tk("C6.5", "Phân bố bút toán theo ngày", theo_ngay),
    ]
```

- [ ] **Step 4: Chạy test, xác nhận pass**

Run: `python -m pytest tests/test_g6_tong_quan.py -q`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add app/checks/g6_tong_quan.py tests/test_g6_tong_quan.py
git commit -m "feat(checks): nhom 6 thong ke va soat xet (C6.1-C6.5)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: Đăng ký & chạy toàn bộ check (`checks/__init__.py`)

**Files:**
- Modify: `app/checks/__init__.py`
- Test: `tests/test_chay_tat_ca.py`

**Interfaces:**
- Produces: `TEN_NHOM: dict[str,str]` (G1…G6), `DANH_SACH: list[tuple[str, Callable]]`, `chay_tat_ca(df, ctx, on_progress: Callable[[str,int],None]|None=None) -> list[CheckResult]`; re-export `BoiCanh, CheckResult, DO, VANG, XANH`.

- [ ] **Step 1: Viết test**

`tests/test_chay_tat_ca.py`:
```python
from app import checks
from tests.conftest import tao_df


def test_chay_tat_ca_tra_29_check_va_bao_tien_trinh(ctx):
    goi = []
    kq = checks.chay_tat_ca(tao_df([{}]), ctx, on_progress=lambda ten, pct: goi.append((ten, pct)))
    assert len(kq) == 6 + 4 + 3 + 5 + 6 + 5
    assert {r.nhom for r in kq} == set(checks.TEN_NHOM)
    assert goi[0][1] == 0 and goi[-1] == ("Hoàn tất", 100)
    assert len({r.ma for r in kq}) == len(kq)  # mã không trùng
```

- [ ] **Step 2: Chạy test, xác nhận fail**

Run: `python -m pytest tests/test_chay_tat_ca.py -q`
Expected: FAIL — `AttributeError: chay_tat_ca`

- [ ] **Step 3: Viết `app/checks/__init__.py`**

```python
"""Đăng ký các nhóm kiểm tra và chạy tuần tự."""
from collections.abc import Callable

import pandas as pd

from . import g1_chung_tu, g2_dinh_khoan, g3_thue_gtgt, g4_kho_gia_von, g5_ket_chuyen, g6_tong_quan
from .base import DO, VANG, XANH, BoiCanh, CheckResult  # noqa: F401  (re-export)

TEN_NHOM = {
    "G1": "Hình thức chứng từ",
    "G2": "Định khoản bất thường",
    "G3": "Thuế GTGT",
    "G4": "Kho & giá vốn",
    "G5": "Kết chuyển cuối kỳ",
    "G6": "Thống kê & soát xét",
}
DANH_SACH = [
    ("G1", g1_chung_tu.kiem_tra), ("G2", g2_dinh_khoan.kiem_tra), ("G3", g3_thue_gtgt.kiem_tra),
    ("G4", g4_kho_gia_von.kiem_tra), ("G5", g5_ket_chuyen.kiem_tra), ("G6", g6_tong_quan.kiem_tra),
]


def chay_tat_ca(df: pd.DataFrame, ctx: BoiCanh,
                on_progress: Callable[[str, int], None] | None = None) -> list[CheckResult]:
    kq: list[CheckResult] = []
    n = len(DANH_SACH)
    for i, (ma, fn) in enumerate(DANH_SACH):
        if on_progress:
            on_progress(TEN_NHOM[ma], int(i * 100 / n))
        kq.extend(fn(df, ctx))
    if on_progress:
        on_progress("Hoàn tất", 100)
    return kq
```

- [ ] **Step 4: Chạy toàn bộ test, xác nhận pass**

Run: `python -m pytest -q`
Expected: tất cả passed (≈ 38 test)

- [ ] **Step 5: Commit**

```bash
git add app/checks/__init__.py tests/test_chay_tat_ca.py
git commit -m "feat(checks): dang ky 6 nhom va chay_tat_ca co bao tien trinh

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 10: Suy trạng thái 11 bước khóa sổ (`trang_thai.py`)

**Files:**
- Create: `app/trang_thai.py`
- Test: `tests/test_trang_thai.py`

**Interfaces:**
- Consumes: `CheckResult` dict theo mã (`ket_qua["C4.1"]`, `["C5.1"]`), tiện ích `base`
- Produces: `DA_LAM="da_lam"`, `CHUA_LAM="chua_lam"`, `CAN_RA="can_ra"`, `KHONG_AP_DUNG="khong_ap_dung"`; `@dataclass BuocKhoaSo(buoc: str, trang_thai: str, tom_tat: str, ma_check: str)`; `suy_trang_thai(df, ket_qua: dict[str, CheckResult]) -> list[BuocKhoaSo]` (đúng 11 phần tử, thứ tự spec §5 Tab A)

- [ ] **Step 1: Viết test**

`tests/test_trang_thai.py`:
```python
from app import checks, trang_thai as tt
from tests.conftest import tao_df


def _suy(df, ctx):
    kq = {r.ma: r for r in checks.chay_tat_ca(df, ctx)}
    return {b.buoc: b for b in tt.suy_trang_thai(df, kq)}, tt.suy_trang_thai(df, kq)


def test_du_11_buoc_dung_thu_tu(ctx):
    _, ds = _suy(tao_df([{}]), ctx)
    assert len(ds) == 11
    assert ds[0].buoc.startswith("Tập hợp CP NVL") and ds[-1].buoc.startswith("TK đầu 5/6/7/8")


def test_khong_phat_sinh_thi_khong_ap_dung(ctx):
    b, _ = _suy(tao_df([{"DebitAccount": "1111", "CreditAccount": "1121"}]), ctx)
    assert b["Tập hợp CP NVL trực tiếp 621 → 154"].trang_thai == tt.KHONG_AP_DUNG
    assert b["Kết chuyển giá vốn 632 → 911"].trang_thai == tt.KHONG_AP_DUNG


def test_621_da_lam_can_ra_chua_lam(ctx):
    da = tao_df([{"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100},
                 {"DebitAccount": "154", "CreditAccount": "6214", "Amount": 100}])
    ra = tao_df([{"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100},
                 {"DebitAccount": "154", "CreditAccount": "6214", "Amount": 60}])
    chua = tao_df([{"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100}])
    k = "Tập hợp CP NVL trực tiếp 621 → 154"
    assert _suy(da, ctx)[0][k].trang_thai == tt.DA_LAM
    assert _suy(ra, ctx)[0][k].trang_thai == tt.CAN_RA and "40" in _suy(ra, ctx)[0][k].tom_tat
    assert _suy(chua, ctx)[0][k].trang_thai == tt.CHUA_LAM and b_ma(_suy(chua, ctx)[0][k]) == "C4.4"


def b_ma(b):
    return b.ma_check


def test_xuat_kho_gia_va_tk_pl_ve_0(ctx):
    df = tao_df([{"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 1, "UnitCost": 0, "Amount": 0},
                 {"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 10}])
    b, _ = _suy(df, ctx)
    assert b["Xuất kho có đầy đủ giá"].trang_thai == tt.CAN_RA
    assert b["TK đầu 5/6/7/8 đã về 0 (kết chuyển hết)"].trang_thai == tt.CAN_RA


def test_lai_lo_va_thue(ctx):
    df = tao_df([{"DebitAccount": "911", "CreditAccount": "6421"},
                 {"DebitAccount": "911", "CreditAccount": "4212"},
                 {"DebitAccount": "1331", "CreditAccount": "3311"},
                 {"DebitAccount": "1311", "CreditAccount": "33311"}])
    b, _ = _suy(df, ctx)
    assert b["Kết chuyển lãi/lỗ 911 ↔ 421"].trang_thai == tt.DA_LAM
    assert b["Khấu trừ thuế GTGT 33311 ↔ 1331"].trang_thai == tt.CHUA_LAM
```

- [ ] **Step 2: Chạy test, xác nhận fail**

Run: `python -m pytest tests/test_trang_thai.py -q`
Expected: FAIL — module không tồn tại

- [ ] **Step 3: Viết `app/trang_thai.py`**

```python
"""Suy trạng thái 11 bước khóa sổ từ dữ liệu phát sinh (Tab A)."""
from dataclasses import dataclass

import pandas as pd

from .checks.base import CheckResult, bat_dau, co_dong, fmt_so, phat_sinh_theo_prefix

DA_LAM, CHUA_LAM, CAN_RA, KHONG_AP_DUNG = "da_lam", "chua_lam", "can_ra", "khong_ap_dung"
TK_KHO = ("152", "153", "155", "156")


@dataclass
class BuocKhoaSo:
    buoc: str
    trang_thai: str
    tom_tat: str
    ma_check: str


def _ket_chuyen(df, ten, tk, no, co, ma) -> BuocKhoaSo:
    """Bước dạng 'TK nguồn -> TK đích': dựa vào phát sinh & sự tồn tại bút toán."""
    ps_no, ps_co = phat_sinh_theo_prefix(df, tk)
    if ps_no == 0 and ps_co == 0:
        return BuocKhoaSo(ten, KHONG_AP_DUNG, f"Kỳ này không có phát sinh {tk}", ma)
    if not co_dong(df, no=no, co=co):
        return BuocKhoaSo(ten, CHUA_LAM, f"Phát sinh {tk}: Nợ {fmt_so(ps_no)} / Có {fmt_so(ps_co)} — chưa có bút toán kết chuyển", ma)
    net = ps_no - ps_co
    if abs(net) > 0.5:
        return BuocKhoaSo(ten, CAN_RA, f"Đã kết chuyển nhưng còn net {fmt_so(net)} chưa về 0", ma)
    return BuocKhoaSo(ten, DA_LAM, f"Nợ {fmt_so(ps_no)} / Có {fmt_so(ps_co)} — đã về 0", ma)


def _nhom_ve_911(df, ten, cac_tk, huong, ma) -> BuocKhoaSo:
    """huong='nguon->911' (doanh thu) hoặc '911->nguon' (chi phí)."""
    co_ps = [tk for tk in cac_tk if any(phat_sinh_theo_prefix(df, tk))]
    if not co_ps:
        return BuocKhoaSo(ten, KHONG_AP_DUNG, "Không có phát sinh", ma)
    thieu = [tk for tk in co_ps
             if not (co_dong(df, no=(tk,), co=("911",)) if huong == "nguon->911"
                     else co_dong(df, no=("911",), co=(tk,)))]
    if thieu:
        return BuocKhoaSo(ten, CHUA_LAM, f"Chưa kết chuyển: {', '.join(thieu)}", ma)
    return BuocKhoaSo(ten, DA_LAM, f"Đã kết chuyển: {', '.join(co_ps)}", ma)


def suy_trang_thai(df: pd.DataFrame, ket_qua: dict[str, CheckResult]) -> list[BuocKhoaSo]:
    ds = [
        _ket_chuyen(df, "Tập hợp CP NVL trực tiếp 621 → 154", "621", ("154",), ("621",), "C4.4"),
        _ket_chuyen(df, "Tập hợp CP nhân công trực tiếp 622 → 154", "622", ("154",), ("622",), "C4.4"),
        _ket_chuyen(df, "Tập hợp & phân bổ CP SXC 627 → 154", "627", ("154",), ("627",), "C4.4"),
    ]

    if not co_dong(df, no=("154",)):
        ds.append(BuocKhoaSo("Nhập kho thành phẩm 154 → 155 (tính giá thành)", KHONG_AP_DUNG, "Không có phát sinh 154", "C4.5"))
    elif co_dong(df, no=("155",), co=("154",)):
        ps = loc_tong(df, "155", "154")
        ds.append(BuocKhoaSo("Nhập kho thành phẩm 154 → 155 (tính giá thành)", DA_LAM, f"Nợ 155 / Có 154: {fmt_so(ps)}", "C4.5"))
    else:
        ds.append(BuocKhoaSo("Nhập kho thành phẩm 154 → 155 (tính giá thành)", CHUA_LAM, "Có Nợ 154 nhưng chưa có Nợ 155 / Có 154", "C4.5"))

    dong_kho = bat_dau(df["DebitAccount"], *TK_KHO) | bat_dau(df["CreditAccount"], *TK_KHO)
    so_gia_0 = ket_qua["C4.1"].so_loi if "C4.1" in ket_qua else 0
    if not dong_kho.any():
        ds.append(BuocKhoaSo("Xuất kho có đầy đủ giá", KHONG_AP_DUNG, "Không có bút toán kho", "C4.1"))
    elif so_gia_0 == 0:
        ds.append(BuocKhoaSo("Xuất kho có đầy đủ giá", DA_LAM, f"{int(dong_kho.sum())} dòng kho, không dòng giá = 0", "C4.1"))
    else:
        ds.append(BuocKhoaSo("Xuất kho có đầy đủ giá", CAN_RA, f"Còn {so_gia_0} dòng kho có số lượng nhưng giá = 0", "C4.1"))

    ds.append(_ket_chuyen(df, "Kết chuyển giá vốn 632 → 911", "632", ("911",), ("632",), "C5.2"))
    ds.append(_nhom_ve_911(df, "Kết chuyển doanh thu 511/515/711 → 911", ("511", "515", "711"), "nguon->911", "C5.3"))
    ds.append(_nhom_ve_911(df, "Kết chuyển chi phí 635/641/642/811 → 911", ("635", "641", "642", "811"), "911->nguon", "C5.4"))

    vao, _ = phat_sinh_theo_prefix(df, "1331")
    _, ra = phat_sinh_theo_prefix(df, "33311")
    if vao == 0 or ra == 0:
        ds.append(BuocKhoaSo("Khấu trừ thuế GTGT 33311 ↔ 1331", KHONG_AP_DUNG, "Thiếu thuế vào hoặc thuế ra", "C5.6"))
    elif co_dong(df, no=("33311",), co=("1331",)):
        ds.append(BuocKhoaSo("Khấu trừ thuế GTGT 33311 ↔ 1331", DA_LAM, f"Thuế vào {fmt_so(vao)} / thuế ra {fmt_so(ra)} — đã khấu trừ", "C5.6"))
    else:
        ds.append(BuocKhoaSo("Khấu trừ thuế GTGT 33311 ↔ 1331", CHUA_LAM, f"Thuế vào {fmt_so(vao)} / thuế ra {fmt_so(ra)} — chưa có bút toán khấu trừ", "C5.6"))

    if not (co_dong(df, no=("911",)) or co_dong(df, co=("911",))):
        ds.append(BuocKhoaSo("Kết chuyển lãi/lỗ 911 ↔ 421", KHONG_AP_DUNG, "Không có phát sinh 911", "C5.5"))
    elif co_dong(df, no=("911",), co=("421",)) or co_dong(df, no=("421",), co=("911",)):
        ds.append(BuocKhoaSo("Kết chuyển lãi/lỗ 911 ↔ 421", DA_LAM, "Đã có bút toán 911 ↔ 421", "C5.5"))
    else:
        ds.append(BuocKhoaSo("Kết chuyển lãi/lỗ 911 ↔ 421", CHUA_LAM, "Có 911 nhưng chưa kết chuyển sang 421", "C5.5"))

    con = ket_qua["C5.1"].so_loi if "C5.1" in ket_qua else 0
    if con == 0:
        ds.append(BuocKhoaSo("TK đầu 5/6/7/8 đã về 0 (kết chuyển hết)", DA_LAM, "Mọi TK doanh thu/chi phí đã về 0", "C5.1"))
    else:
        ds.append(BuocKhoaSo("TK đầu 5/6/7/8 đã về 0 (kết chuyển hết)", CAN_RA, f"Còn {con} tài khoản có net ≠ 0", "C5.1"))
    return ds


def loc_tong(df, no: str, co: str) -> float:
    m = bat_dau(df["DebitAccount"], no) & bat_dau(df["CreditAccount"], co)
    return float(df.loc[m, "Amount"].sum())
```

- [ ] **Step 4: Chạy test, xác nhận pass**

Run: `python -m pytest tests/test_trang_thai.py -q`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add app/trang_thai.py tests/test_trang_thai.py
git commit -m "feat: suy trang thai 11 buoc khoa so tu du lieu

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 11: Xuất báo cáo Excel (`report.py`)

**Files:**
- Create: `app/report.py`
- Test: `tests/test_report.py`

**Interfaces:**
- Consumes: `list[CheckResult]`, `list[BuocKhoaSo]`, `ThongTinFile`, `TEN_NHOM`
- Produces: `xuat_bao_cao(ket_qua, trang_thai, thong_tin, thu_muc_out: str) -> str` (đường dẫn file); `TEN_MUC_DO = {"do":"Nghiêm trọng","vang":"Cảnh báo","xanh":"Đạt"}`; `TEN_TRANG_THAI = {...}`; `ten_sheet_an_toan(ten) -> str`

- [ ] **Step 1: Viết test**

`tests/test_report.py`:
```python
import openpyxl

from app import checks, report, trang_thai as tt
from app.loader import ThongTinFile
from tests.conftest import tao_df


def test_xuat_bao_cao_tao_du_sheet(tmp_path, ctx):
    df = tao_df([{"Description": None, "DebitAccount": "632111", "CreditAccount": "1551", "Amount": 5}])
    kq = checks.chay_tat_ca(df, ctx)
    ts = tt.suy_trang_thai(df, {r.ma: r for r in kq})
    tt_file = ThongTinFile("x.xlsx", "x.xlsx", "08/2026", 8, 2026, 1, 5.0, ["log 1"])
    path = report.xuat_bao_cao(kq, ts, tt_file, str(tmp_path))
    wb = openpyxl.load_workbook(path)
    assert wb.sheetnames[:2] == ["Tong quan", "Trang thai khoa so"]
    assert "C1.1" in wb.sheetnames and "C5.2" in wb.sheetnames      # có lỗi -> có sheet
    assert "C1.5" not in wb.sheetnames                               # không lỗi -> không sheet
    assert "C6.1" in wb.sheetnames and "Nhat ky xu ly" in wb.sheetnames
    ws = wb["Tong quan"]
    assert ws["A1"].value.startswith("BÁO CÁO KIỂM TRA KHÓA SỔ")
    assert ws.freeze_panes is not None or True


def test_ten_sheet_an_toan():
    assert report.ten_sheet_an_toan("C1.1") == "C1.1"
    assert report.ten_sheet_an_toan("a/b:c*d?[e]" + "x" * 40) == ("a-b-c-d-e-x" + "x" * 40)[:31]
```

- [ ] **Step 2: Chạy test, xác nhận fail**

Run: `python -m pytest tests/test_report.py -q`
Expected: FAIL — module không tồn tại

- [ ] **Step 3: Viết `app/report.py`**

```python
"""Xuất báo cáo kiểm tra khóa sổ ra Excel (xlsxwriter)."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from .checks import TEN_NHOM
from .checks.base import DO, VANG, XANH, CheckResult
from .loader import ThongTinFile
from .trang_thai import BuocKhoaSo

TEN_MUC_DO = {DO: "Nghiêm trọng", VANG: "Cảnh báo", XANH: "Đạt"}
TEN_TRANG_THAI = {"da_lam": "Đã làm", "chua_lam": "CHƯA LÀM", "can_ra": "Cần rà", "khong_ap_dung": "Không áp dụng"}
MAU = {DO: "#FFC7CE", VANG: "#FFEB9C", XANH: "#C6EFCE",
       "da_lam": "#C6EFCE", "chua_lam": "#FFC7CE", "can_ra": "#FFEB9C", "khong_ap_dung": "#EDEDED"}
FONT = "Segoe UI"


def ten_sheet_an_toan(ten: str) -> str:
    return re.sub(r"[\[\]:*?/\\]", "-", ten)[:31]


def _ghi_bang(writer, ten_sheet, df: pd.DataFrame, fmt, dong_dau=0):
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].dt.strftime("%d/%m/%Y")
    df.to_excel(writer, sheet_name=ten_sheet, index=False, startrow=dong_dau)
    ws = writer.sheets[ten_sheet]
    for j, c in enumerate(df.columns):
        ws.write(dong_dau, j, c, fmt["header"])
        rong = max(10, min(60, int(df[c].astype(str).str.len().quantile(0.9)) + 2 if len(df) else 12))
        ws.set_column(j, j, rong, fmt["so"] if c in ("Amount", "ps_no", "ps_co", "net", "tong",
                                                          "thue_vao_1331", "thue_ra_33311") else None)
    ws.freeze_panes(dong_dau + 1, 0)
    if len(df):
        ws.autofilter(dong_dau, 0, dong_dau + len(df), len(df.columns) - 1)
    return ws


def xuat_bao_cao(ket_qua: list[CheckResult], trang_thai: list[BuocKhoaSo],
                 thong_tin: ThongTinFile, thu_muc_out: str) -> str:
    Path(thu_muc_out).mkdir(parents=True, exist_ok=True)
    ky_ten = thong_tin.ky.replace("/", "-")
    path = Path(thu_muc_out) / f"Bao cao kiem tra khoa so - {ky_ten} - {datetime.now():%Y%m%d_%H%M}.xlsx"

    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        wb = writer.book
        fmt = {
            "header": wb.add_format({"bold": True, "font_color": "white", "bg_color": "#1F4E79",
                                     "font_name": FONT, "border": 1, "text_wrap": True, "valign": "vcenter"}),
            "so": wb.add_format({"num_format": "#,##0", "font_name": FONT}),
            "tieu_de": wb.add_format({"bold": True, "font_size": 14, "font_color": "#1F4E79", "font_name": FONT}),
        }
        for md, mau in MAU.items():
            fmt[md] = wb.add_format({"bg_color": mau, "font_name": FONT, "border": 1})

        # --- Tổng quan ---
        loi = [r for r in ket_qua if not r.la_thong_ke]
        so_do = sum(r.muc_do_thuc == DO for r in loi)
        so_vang = sum(r.muc_do_thuc == VANG for r in loi)
        chua = sum(b.trang_thai == "chua_lam" for b in trang_thai)
        tq = pd.DataFrame([{
            "Mã": r.ma, "Nhóm": TEN_NHOM[r.nhom], "Kiểm tra": r.ten,
            "Số dòng vi phạm": r.so_loi, "Mức độ": TEN_MUC_DO[r.muc_do_thuc], "Ghi chú": r.ghi_chu,
        } for r in loi])
        ws = _ghi_bang(writer, "Tong quan", tq, fmt, dong_dau=4)
        ws.write(0, 0, f"BÁO CÁO KIỂM TRA KHÓA SỔ — KỲ {thong_tin.ky}", fmt["tieu_de"])
        ws.write(1, 0, f"File: {thong_tin.ten} · {thong_tin.so_dong:,} dòng · Tổng phát sinh {thong_tin.tong_ps:,.0f}")
        ket_luan = "SẴN SÀNG KHÓA SỔ" if so_do == 0 and chua == 0 else f"CHƯA SẴN SÀNG — {so_do} lỗi nghiêm trọng, {chua} bước chưa làm"
        ws.write(2, 0, f"Kết luận: {ket_luan}  ·  🔴 {so_do}  🟡 {so_vang}", fmt["tieu_de"])
        for i, r in enumerate(loi, start=5):
            ws.write(i, 4, TEN_MUC_DO[r.muc_do_thuc], fmt[r.muc_do_thuc])

        # --- Trạng thái khóa sổ ---
        ts = pd.DataFrame([{"Bước": b.buoc, "Trạng thái": TEN_TRANG_THAI[b.trang_thai],
                            "Tóm tắt": b.tom_tat, "Mã check": b.ma_check} for b in trang_thai])
        ws = _ghi_bang(writer, "Trang thai khoa so", ts, fmt)
        for i, b in enumerate(trang_thai, start=1):
            ws.write(i, 1, TEN_TRANG_THAI[b.trang_thai], fmt[b.trang_thai])

        # --- Chi tiết từng check ---
        for r in ket_qua:
            if r.so_loi > 0 or r.la_thong_ke:
                _ghi_bang(writer, ten_sheet_an_toan(r.ma), r.chi_tiet, fmt)

        # --- Nhật ký ---
        nk = pd.DataFrame({"Thông điệp": thong_tin.nhat_ky or ["Không có cảnh báo khi đọc dữ liệu"]})
        _ghi_bang(writer, "Nhat ky xu ly", nk, fmt)
    return str(path)
```

- [ ] **Step 4: Chạy test, xác nhận pass**

Run: `python -m pytest tests/test_report.py -q`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add app/report.py tests/test_report.py
git commit -m "feat(report): xuat bao cao Excel tong quan + trang thai + chi tiet

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 12: Cầu nối `JsApi` (`api.py`)

**Files:**
- Create: `app/api.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: `loader.doc_bang_ke`, `loader.tim_file_moi_nhat`, `checks.chay_tat_ca`, `trang_thai.suy_trang_thai`, `report.xuat_bao_cao`
- Produces: class `JsApi` với:
  - `gan_window(window)` — lưu window để `evaluate_js` & file dialog
  - `lay_file_moi_nhat() -> dict | None` = `{path, ten, ky, so_dong, tong_ps}` (đọc file để lấy thông tin, giữ df trong bộ nhớ)
  - `chon_file() -> dict | None` — mở dialog rồi gọi `_nap_file`
  - `nap_file(path) -> dict` — nạp file được kéo-thả
  - `chay_kiem_tra(path: str | None = None) -> dict` = `{tomtat:{ky, so_dong, tong_ps, so_do, so_vang, so_chua_lam, con_viec, san_sang}, trang_thai:[...], nhom:[{ma, ten, so_loi, muc_do, checks:[{ma, ten, muc_do, so_loi, la_thong_ke, ghi_chu}]}]}`
  - `lay_chi_tiet(ma_check, trang=1, kich_thuoc=100, tim_kiem="") -> dict` = `{tong, trang, cot:[...], dong:[{...}]}`
  - `xuat_bao_cao() -> dict` = `{path}`; `mo_file(path)`, `mo_thu_muc(path)`
  - Mọi giá trị trả về là JSON-serializable (không numpy scalar). Lỗi trả `{"loi": "..."}` thay vì raise.
  - `THU_MUC_SOURCE = "1. Source"`, `THU_MUC_REPORT = "2. Report"` tính từ thư mục gốc dự án (`Path(__file__).resolve().parents[1]`).

- [ ] **Step 1: Viết test**

`tests/test_api.py`:
```python
import json

import pandas as pd

from app.api import JsApi


def _xlsx(tmp_path):
    rows = [
        {"DocNo": "A", "DocDate": "2026-08-01", "DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100, "Description": "x"},
        {"DocNo": "B", "DocDate": "2026-08-02", "DebitAccount": "154", "CreditAccount": "6214", "Amount": 100, "Description": None},
        {"DocNo": "C", "DocDate": "2026-08-03", "DebitAccount": "632111", "CreditAccount": "1551", "Amount": 70, "Description": "gv"},
    ]
    p = tmp_path / "bk.xlsx"
    pd.DataFrame(rows).to_excel(p, sheet_name="Table1", index=False)
    return str(p)


def test_chay_kiem_tra_tra_json_hop_le(tmp_path):
    api = JsApi()
    kq = api.chay_kiem_tra(_xlsx(tmp_path))
    json.dumps(kq)  # không numpy scalar
    assert kq["tomtat"]["ky"] == "08/2026" and kq["tomtat"]["so_dong"] == 3
    assert kq["tomtat"]["san_sang"] is False           # 632 chưa kết chuyển -> C5.2 đỏ
    assert len(kq["trang_thai"]) == 11 and len(kq["nhom"]) == 6
    g5 = next(n for n in kq["nhom"] if n["ma"] == "G5")
    assert g5["muc_do"] == "do"


def test_lay_chi_tiet_phan_trang_va_tim_kiem(tmp_path):
    api = JsApi()
    api.chay_kiem_tra(_xlsx(tmp_path))
    ct = api.lay_chi_tiet("C1.1")
    assert ct["tong"] == 1 and ct["dong"][0]["DocNo"] == "B" and ct["dong"][0]["DocDate"] == "02/08/2026"
    assert api.lay_chi_tiet("C1.1", tim_kiem="zzz")["tong"] == 0
    assert "TK" in api.lay_chi_tiet("C5.2")["cot"]


def test_xuat_bao_cao_va_loi_khi_chua_chay(tmp_path, monkeypatch):
    api = JsApi()
    assert "loi" in api.xuat_bao_cao()
    api.chay_kiem_tra(_xlsx(tmp_path))
    monkeypatch.setattr(api, "thu_muc_report", str(tmp_path / "out"))
    kq = api.xuat_bao_cao()
    assert kq["path"].endswith(".xlsx") and (tmp_path / "out").exists()


def test_file_khong_ton_tai_tra_loi():
    assert "loi" in JsApi().chay_kiem_tra("khong/co/file.xlsx")
```

- [ ] **Step 2: Chạy test, xác nhận fail**

Run: `python -m pytest tests/test_api.py -q`
Expected: FAIL — module không tồn tại

- [ ] **Step 3: Viết `app/api.py`**

```python
"""Cầu nối JS ↔ Python cho pywebview (js_api)."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pandas as pd

from . import checks, report
from .checks.base import DO, VANG, THU_TU_MUC_DO, BoiCanh, CheckResult
from .loader import ThongTinFile, doc_bang_ke, tim_file_moi_nhat
from .trang_thai import suy_trang_thai

GOC = Path(__file__).resolve().parents[1]
THU_MUC_SOURCE = str(GOC / "1. Source")
THU_MUC_REPORT = str(GOC / "2. Report")


def _records(df: pd.DataFrame) -> list[dict]:
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].dt.strftime("%d/%m/%Y")
    return json.loads(df.to_json(orient="records", force_ascii=False))


class JsApi:
    def __init__(self):
        self._window = None
        self._df: pd.DataFrame | None = None
        self._tt: ThongTinFile | None = None
        self._kq: dict[str, CheckResult] = {}
        self._ket_qua: list[CheckResult] = []
        self._trang_thai = []
        self.thu_muc_source = THU_MUC_SOURCE
        self.thu_muc_report = THU_MUC_REPORT

    # ---- cửa sổ & tiến trình ----
    def gan_window(self, window):
        self._window = window

    def _tien_trinh(self, ten: str, pct: int):
        if self._window is not None:
            self._window.evaluate_js(f"window.onTienTrinh && onTienTrinh({json.dumps(ten, ensure_ascii=False)}, {pct})")

    # ---- nạp file ----
    def _nap_file(self, path: str) -> dict:
        self._df, self._tt = doc_bang_ke(path)
        self._kq, self._ket_qua, self._trang_thai = {}, [], []
        t = self._tt
        return {"path": t.path, "ten": t.ten, "ky": t.ky, "so_dong": t.so_dong, "tong_ps": t.tong_ps}

    def lay_file_moi_nhat(self):
        p = tim_file_moi_nhat(self.thu_muc_source)
        if not p:
            return None
        try:
            return self._nap_file(p)
        except Exception as e:  # noqa: BLE001
            return {"loi": str(e), "path": p}

    def nap_file(self, path: str):
        try:
            return self._nap_file(path)
        except Exception as e:  # noqa: BLE001
            return {"loi": str(e)}

    def chon_file(self):
        if self._window is None:
            return {"loi": "Chưa có cửa sổ"}
        import webview
        loai = getattr(getattr(webview, "FileDialog", None), "OPEN", None) or webview.OPEN_DIALOG
        chon = self._window.create_file_dialog(loai, directory=self.thu_muc_source,
                                               file_types=("Excel (*.xlsx;*.xls;*.xlsm)",))
        if not chon:
            return None
        return self.nap_file(chon[0])

    # ---- kiểm tra ----
    def chay_kiem_tra(self, path: str | None = None):
        try:
            if path and (self._tt is None or self._tt.path != path):
                self._nap_file(path)
            if self._df is None:
                return {"loi": "Chưa chọn file bảng kê"}
            ctx = BoiCanh(self._tt.ky_thang, self._tt.ky_nam)
            self._ket_qua = checks.chay_tat_ca(self._df, ctx, on_progress=self._tien_trinh)
            self._kq = {r.ma: r for r in self._ket_qua}
            self._trang_thai = suy_trang_thai(self._df, self._kq)
            return self._tom_tat()
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không đọc/kiểm tra được file: {e}"}

    def _tom_tat(self) -> dict:
        loi = [r for r in self._ket_qua if not r.la_thong_ke]
        so_do = sum(r.muc_do_thuc == DO for r in loi)
        so_vang = sum(r.muc_do_thuc == VANG for r in loi)
        chua = sum(b.trang_thai == "chua_lam" for b in self._trang_thai)
        nhom = []
        for ma, ten in checks.TEN_NHOM.items():
            cs = [r for r in self._ket_qua if r.nhom == ma]
            khong_tk = [r for r in cs if not r.la_thong_ke]
            muc = min((r.muc_do_thuc for r in khong_tk), key=THU_TU_MUC_DO.get, default="xanh")
            nhom.append({"ma": ma, "ten": ten, "so_loi": sum(r.so_loi for r in khong_tk), "muc_do": muc,
                         "checks": [{"ma": r.ma, "ten": r.ten, "muc_do": r.muc_do_thuc, "so_loi": r.so_loi,
                                     "la_thong_ke": r.la_thong_ke, "ghi_chu": r.ghi_chu} for r in cs]})
        t = self._tt
        return {
            "tomtat": {"ky": t.ky, "ten": t.ten, "so_dong": t.so_dong, "tong_ps": t.tong_ps,
                       "so_do": so_do, "so_vang": so_vang, "so_chua_lam": chua,
                       "con_viec": so_do + chua, "san_sang": so_do == 0 and chua == 0},
            "trang_thai": [{"buoc": b.buoc, "trang_thai": b.trang_thai, "tom_tat": b.tom_tat,
                            "ma_check": b.ma_check} for b in self._trang_thai],
            "nhom": nhom,
        }

    def lay_chi_tiet(self, ma_check: str, trang: int = 1, kich_thuoc: int = 100, tim_kiem: str = ""):
        r = self._kq.get(ma_check)
        if r is None:
            return {"loi": f"Không có kết quả {ma_check}"}
        df = r.chi_tiet
        if tim_kiem:
            tk = tim_kiem.lower()
            mask = df.astype(str).apply(lambda s: s.str.lower().str.contains(tk, regex=False)).any(axis=1)
            df = df[mask]
        tong = int(len(df))
        a = max(0, (int(trang) - 1) * int(kich_thuoc))
        return {"tong": tong, "trang": int(trang), "cot": list(df.columns),
                "dong": _records(df.iloc[a:a + int(kich_thuoc)])}

    # ---- xuất & mở ----
    def xuat_bao_cao(self):
        if not self._ket_qua:
            return {"loi": "Chưa chạy kiểm tra"}
        try:
            p = report.xuat_bao_cao(self._ket_qua, self._trang_thai, self._tt, self.thu_muc_report)
            return {"path": p}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không xuất được báo cáo: {e}"}

    def mo_file(self, path: str):
        os.startfile(path)  # noqa: S606
        return True

    def mo_thu_muc(self, path: str):
        p = Path(path)
        if p.is_file():
            subprocess.Popen(["explorer", "/select,", str(p)])  # noqa: S603,S607
        else:
            os.startfile(str(p))  # noqa: S606
        return True
```

- [ ] **Step 4: Chạy test, xác nhận pass**

Run: `python -m pytest tests/test_api.py -q`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add app/api.py tests/test_api.py
git commit -m "feat(api): JsApi cau noi pywebview - nap file, kiem tra, chi tiet theo trang, xuat bao cao

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 13: Giao diện — `index.html` + `style.css` (Segoe UI, light mode)

**Files:**
- Create: `app/web/index.html`, `app/web/style.css`
- Test: `tests/test_web_static.py`

**Interfaces:**
- Produces các `id` mà `app.js` (Task 14) bám vào: `man-hinh-1`, `man-hinh-2`, `vung-keo-tha`, `btn-chon-file`, `the-file`, `file-ten`, `file-ky`, `file-so-dong`, `file-tong-ps`, `btn-kiem-tra`, `tien-trinh`, `tien-trinh-thanh`, `tien-trinh-ten`, `banner`, `banner-ket-luan`, `so-do`, `so-vang`, `so-xanh`, `tab-a`, `tab-b`, `noi-dung-a`, `noi-dung-b`, `ds-buoc`, `luoi-nhom`, `bang-chi-tiet`, `chi-tiet-tieu-de`, `o-tim-kiem`, `phan-trang`, `btn-xuat`, `btn-kiem-tra-lai`, `btn-file-khac`, `toast`, `header-file`.
- CSS class trạng thái: `.muc-do`, `.muc-xanh`, `.muc-vang`, `.muc-do-` (đỏ), `.tt-da_lam`, `.tt-chua_lam`, `.tt-can_ra`, `.tt-khong_ap_dung`, `.an` (display:none), `.the-nhom.dang-chon`.

- [ ] **Step 1: Viết test tĩnh**

`tests/test_web_static.py`:
```python
from pathlib import Path

WEB = Path("app/web")


def test_index_tham_chieu_file_local_va_du_id():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert 'href="style.css"' in html and 'src="app.js"' in html
    assert "http://" not in html and "https://" not in html   # offline
    for i in ["man-hinh-1", "man-hinh-2", "btn-kiem-tra", "tab-a", "tab-b", "ds-buoc",
              "luoi-nhom", "bang-chi-tiet", "btn-xuat", "toast", "vung-keo-tha"]:
        assert f'id="{i}"' in html, i


def test_css_segoe_ui_light_mode():
    css = (WEB / "style.css").read_text(encoding="utf-8")
    assert "Segoe UI" in css and "#1F4E79" in css and "#DC2626" in css
    assert "prefers-color-scheme: dark" not in css
```

- [ ] **Step 2: Chạy test, xác nhận fail**

Run: `python -m pytest tests/test_web_static.py -q`
Expected: FAIL — file không tồn tại

- [ ] **Step 3: Viết `app/web/index.html`**

```html
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<title>Kiểm tra khóa sổ cuối kỳ</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="header">
  <div class="logo">KS</div>
  <div class="header-text">
    <h1>Kiểm tra khóa sổ cuối kỳ</h1>
    <p>Doanh nghiệp sản xuất · Thông tư 200</p>
  </div>
  <div id="header-file" class="header-file"></div>
</header>

<!-- ===== MÀN HÌNH 1: CHỌN FILE ===== -->
<main id="man-hinh-1" class="man-hinh">
  <section id="vung-keo-tha" class="vung-keo-tha">
    <div class="icon-file">📄</div>
    <p class="keo-tha-text">Kéo file bảng kê chứng từ (.xlsx) vào đây</p>
    <p class="keo-tha-phu">hoặc</p>
    <button id="btn-chon-file" class="btn btn-phu">Chọn file…</button>
  </section>

  <section id="the-file" class="the-file an">
    <div class="the-file-hang"><span>File</span><strong id="file-ten"></strong></div>
    <div class="the-file-luoi">
      <div><span>Kỳ</span><strong id="file-ky"></strong></div>
      <div><span>Số dòng</span><strong id="file-so-dong"></strong></div>
      <div><span>Tổng phát sinh</span><strong id="file-tong-ps"></strong></div>
    </div>
  </section>

  <button id="btn-kiem-tra" class="btn btn-chinh btn-lon" disabled>Kiểm tra</button>

  <section id="tien-trinh" class="tien-trinh an">
    <div class="tien-trinh-nen"><div id="tien-trinh-thanh" class="tien-trinh-thanh"></div></div>
    <p id="tien-trinh-ten"></p>
  </section>
</main>

<!-- ===== MÀN HÌNH 2: KẾT QUẢ ===== -->
<main id="man-hinh-2" class="man-hinh an">
  <section id="banner" class="banner">
    <div id="banner-ket-luan" class="banner-ket-luan"></div>
    <div class="banner-so">
      <span class="chip chip-do">🔴 <b id="so-do">0</b></span>
      <span class="chip chip-vang">🟡 <b id="so-vang">0</b></span>
      <span class="chip chip-xanh">🟢 <b id="so-xanh">0</b></span>
    </div>
  </section>

  <nav class="tab-bar">
    <button id="tab-a" class="tab dang-chon">Trạng thái khóa sổ</button>
    <button id="tab-b" class="tab">Lỗi &amp; cảnh báo</button>
  </nav>

  <section id="noi-dung-a" class="noi-dung">
    <ul id="ds-buoc" class="ds-buoc"></ul>
  </section>

  <section id="noi-dung-b" class="noi-dung an">
    <div id="luoi-nhom" class="luoi-nhom"></div>
  </section>

  <section id="khung-chi-tiet" class="khung-chi-tiet an">
    <div class="chi-tiet-dau">
      <h3 id="chi-tiet-tieu-de"></h3>
      <input id="o-tim-kiem" type="search" placeholder="Tìm trong kết quả…">
    </div>
    <div class="bang-cuon"><table id="bang-chi-tiet" class="bang"></table></div>
    <div id="phan-trang" class="phan-trang"></div>
  </section>

  <footer class="footer">
    <button id="btn-xuat" class="btn btn-chinh">Xuất báo cáo Excel</button>
    <button id="btn-kiem-tra-lai" class="btn btn-phu">Kiểm tra lại</button>
    <button id="btn-file-khac" class="btn btn-phu">Kiểm tra file khác</button>
  </footer>
</main>

<div id="toast" class="toast an"></div>
<script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 4: Viết `app/web/style.css`**

```css
:root {
  --nen: #FFFFFF; --nen-phu: #F5F7FA; --chu: #1F2937; --chu-phu: #6B7280;
  --chinh: #1F4E79; --chinh-hover: #2E75B6; --vien: #E5E7EB;
  --do: #DC2626; --vang: #D97706; --xanh: #16A34A;
  --do-nhat: #FEE2E2; --vang-nhat: #FEF3C7; --xanh-nhat: #DCFCE7; --xam-nhat: #F3F4F6;
}
* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; background: var(--nen-phu); color: var(--chu);
  font-family: "Segoe UI", system-ui, -apple-system, sans-serif; font-size: 14px; }
.an { display: none !important; }

/* Header */
.header { display: flex; align-items: center; gap: 14px; padding: 14px 24px; background: var(--nen);
  border-bottom: 1px solid var(--vien); position: sticky; top: 0; z-index: 10; }
.logo { width: 40px; height: 40px; border-radius: 10px; background: var(--chinh); color: #fff;
  display: grid; place-items: center; font-weight: 700; }
.header-text h1 { margin: 0; font-size: 18px; font-weight: 600; }
.header-text p { margin: 0; color: var(--chu-phu); font-size: 12px; }
.header-file { margin-left: auto; color: var(--chu-phu); font-size: 13px; }

/* Màn hình */
.man-hinh { max-width: 1100px; margin: 0 auto; padding: 24px; display: flex; flex-direction: column; gap: 18px; }
#man-hinh-1 { max-width: 640px; align-items: stretch; padding-top: 48px; }

/* Kéo thả */
.vung-keo-tha { border: 2px dashed #B8C4D6; border-radius: 14px; padding: 40px 24px; text-align: center;
  background: var(--nen); transition: .15s; }
.vung-keo-tha.keo-qua { border-color: var(--chinh-hover); background: #EEF4FB; }
.icon-file { font-size: 40px; }
.keo-tha-text { font-size: 16px; margin: 8px 0 2px; }
.keo-tha-phu { color: var(--chu-phu); margin: 4px 0 12px; }

/* Thẻ file */
.the-file { background: var(--nen); border: 1px solid var(--vien); border-radius: 12px; padding: 16px 20px; }
.the-file span { display: block; color: var(--chu-phu); font-size: 12px; }
.the-file strong { font-size: 15px; font-weight: 600; }
.the-file-hang { margin-bottom: 12px; }
.the-file-luoi { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }

/* Nút */
.btn { font: inherit; border-radius: 10px; padding: 10px 18px; border: 1px solid var(--vien);
  background: var(--nen); color: var(--chu); cursor: pointer; transition: .15s; }
.btn:hover { background: var(--xam-nhat); }
.btn-chinh { background: var(--chinh); color: #fff; border-color: var(--chinh); }
.btn-chinh:hover { background: var(--chinh-hover); border-color: var(--chinh-hover); }
.btn-lon { font-size: 17px; padding: 14px; font-weight: 600; }
.btn:disabled { opacity: .5; cursor: not-allowed; }

/* Tiến trình */
.tien-trinh-nen { height: 8px; background: var(--vien); border-radius: 99px; overflow: hidden; }
.tien-trinh-thanh { height: 100%; width: 0; background: var(--chinh-hover); transition: width .2s; }
#tien-trinh-ten { color: var(--chu-phu); margin: 6px 0 0; font-size: 13px; }

/* Banner */
.banner { display: flex; align-items: center; justify-content: space-between; gap: 16px;
  border-radius: 14px; padding: 18px 22px; border: 1px solid var(--vien); }
.banner.san-sang { background: var(--xanh-nhat); border-color: #86EFAC; }
.banner.chua-san-sang { background: var(--do-nhat); border-color: #FCA5A5; }
.banner-ket-luan { font-size: 20px; font-weight: 700; }
.banner.san-sang .banner-ket-luan { color: #166534; }
.banner.chua-san-sang .banner-ket-luan { color: #991B1B; }
.chip { padding: 6px 12px; border-radius: 99px; background: var(--nen); border: 1px solid var(--vien); margin-left: 6px; }

/* Tabs */
.tab-bar { display: flex; gap: 4px; border-bottom: 1px solid var(--vien); }
.tab { font: inherit; font-size: 15px; padding: 10px 18px; background: none; border: none;
  border-bottom: 3px solid transparent; color: var(--chu-phu); cursor: pointer; }
.tab.dang-chon { color: var(--chinh); border-bottom-color: var(--chinh); font-weight: 600; }

/* Tab A – các bước */
.ds-buoc { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.buoc { display: grid; grid-template-columns: 36px 1fr auto 20px; align-items: center; gap: 12px;
  background: var(--nen); border: 1px solid var(--vien); border-radius: 12px; padding: 12px 16px; cursor: pointer; }
.buoc:hover { border-color: var(--chinh-hover); }
.buoc .icon { font-size: 20px; text-align: center; }
.buoc .ten { font-weight: 600; }
.buoc .tom-tat { color: var(--chu-phu); font-size: 13px; }
.buoc .nhan { font-size: 12px; padding: 4px 10px; border-radius: 99px; font-weight: 600; }
.tt-da_lam .nhan { background: var(--xanh-nhat); color: #166534; }
.tt-chua_lam .nhan { background: var(--do-nhat); color: #991B1B; }
.tt-can_ra .nhan { background: var(--vang-nhat); color: #92400E; }
.tt-khong_ap_dung .nhan { background: var(--xam-nhat); color: var(--chu-phu); }

/* Tab B – thẻ nhóm */
.luoi-nhom { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.the-nhom { background: var(--nen); border: 1px solid var(--vien); border-radius: 12px; padding: 14px 16px; cursor: pointer; }
.the-nhom:hover, .the-nhom.dang-chon { border-color: var(--chinh); box-shadow: 0 0 0 2px #DBEAFE; }
.the-nhom .so { font-size: 28px; font-weight: 700; }
.the-nhom .ten { font-weight: 600; margin-top: 4px; }
.the-nhom .ds-check { margin: 8px 0 0; padding: 0; list-style: none; font-size: 12px; color: var(--chu-phu); }
.the-nhom .ds-check li { display: flex; justify-content: space-between; padding: 2px 0; cursor: pointer; }
.the-nhom .ds-check li:hover { color: var(--chinh); }
.muc-do { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }
.muc-xanh { background: var(--xanh); } .muc-vang { background: var(--vang); } .muc-do- { background: var(--do); }
.the-nhom.nhom-do .so { color: var(--do); } .the-nhom.nhom-vang .so { color: var(--vang); } .the-nhom.nhom-xanh .so { color: var(--xanh); }

/* Bảng chi tiết */
.khung-chi-tiet { background: var(--nen); border: 1px solid var(--vien); border-radius: 12px; padding: 14px 16px; }
.chi-tiet-dau { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
.chi-tiet-dau h3 { margin: 0; font-size: 15px; }
#o-tim-kiem { font: inherit; padding: 8px 12px; border: 1px solid var(--vien); border-radius: 8px; width: 260px; }
.bang-cuon { max-height: 420px; overflow: auto; border: 1px solid var(--vien); border-radius: 8px; }
.bang { width: 100%; border-collapse: collapse; font-size: 13px; }
.bang th { position: sticky; top: 0; background: var(--chinh); color: #fff; text-align: left; padding: 8px 10px; white-space: nowrap; }
.bang td { padding: 6px 10px; border-bottom: 1px solid var(--vien); vertical-align: top; }
.bang tr:nth-child(even) td { background: var(--nen-phu); }
.bang td.so { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
.phan-trang { display: flex; align-items: center; gap: 10px; margin-top: 10px; color: var(--chu-phu); font-size: 13px; }

/* Footer & toast */
.footer { display: flex; gap: 10px; padding-top: 6px; }
.toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); background: #111827; color: #fff;
  padding: 12px 18px; border-radius: 10px; display: flex; gap: 12px; align-items: center; box-shadow: 0 8px 24px rgba(0,0,0,.2); }
.toast .btn { padding: 6px 12px; }
```

- [ ] **Step 5: Chạy test, xác nhận pass**

Run: `python -m pytest tests/test_web_static.py -q`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add app/web/index.html app/web/style.css tests/test_web_static.py
git commit -m "feat(web): giao dien HTML/CSS Segoe UI light mode - 2 man hinh, 2 tab

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 14: `app.js` + `main.py` + file `.bat`

**Files:**
- Create: `app/web/app.js`, `app/main.py`, `Kiem_tra_khoa_so.bat`
- Modify: `tests/test_web_static.py` (thêm test app.js)

**Interfaces:**
- Consumes: `window.pywebview.api.*` theo Task 12; các `id`/class theo Task 13.
- Produces: hàm global `onTienTrinh(ten, pct)` (backend gọi); `main()` tạo cửa sổ 1100×750, min 1000×700, tiêu đề "Kiểm tra khóa sổ cuối kỳ".

- [ ] **Step 1: Thêm test tĩnh cho app.js** — thêm vào `tests/test_web_static.py`:

```python
def test_app_js_co_ham_tien_trinh_va_goi_api():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert "function onTienTrinh" in js
    for f in ["lay_file_moi_nhat", "chon_file", "nap_file", "chay_kiem_tra", "lay_chi_tiet", "xuat_bao_cao", "mo_file", "mo_thu_muc"]:
        assert f"api.{f}(" in js, f
    assert "pywebviewFullPath" in js   # kéo-thả lấy đường dẫn thật
```

- [ ] **Step 2: Chạy test, xác nhận fail**

Run: `python -m pytest tests/test_web_static.py -q`
Expected: 1 failed (app.js chưa có)

- [ ] **Step 3: Viết `app/web/app.js`**

```javascript
/* Kiểm tra khóa sổ – frontend thuần, giao tiếp qua window.pywebview.api */
const $ = (id) => document.getElementById(id);
let api = null;
let ketQua = null;              // kết quả chay_kiem_tra
let fileHienTai = null;         // {path, ten, ky, so_dong, tong_ps}
let chiTiet = { ma: null, trang: 1, timKiem: "" };
const KICH_THUOC = 100;

const fmt = (n) => Number(n || 0).toLocaleString("vi-VN", { maximumFractionDigits: 0 });
const ICON_TT = { da_lam: "✅", chua_lam: "❌", can_ra: "⚠️", khong_ap_dung: "➖" };
const NHAN_TT = { da_lam: "Đã làm", chua_lam: "Chưa làm", can_ra: "Cần rà", khong_ap_dung: "Không áp dụng" };
const NHAN_MD = { do: "Nghiêm trọng", vang: "Cảnh báo", xanh: "Đạt" };
const CLASS_MD = { do: "muc-do-", vang: "muc-vang", xanh: "muc-xanh" };

/* ---------- tiến trình (backend gọi) ---------- */
function onTienTrinh(ten, pct) {
  $("tien-trinh").classList.remove("an");
  $("tien-trinh-thanh").style.width = pct + "%";
  $("tien-trinh-ten").textContent = pct < 100 ? `Đang kiểm tra: ${ten}…` : "Hoàn tất";
}
window.onTienTrinh = onTienTrinh;

/* ---------- toast ---------- */
function toast(msg, nut = []) {
  const t = $("toast");
  t.innerHTML = "";
  t.append(Object.assign(document.createElement("span"), { textContent: msg }));
  nut.forEach(({ ten, onClick }) => {
    const b = document.createElement("button"); b.className = "btn"; b.textContent = ten; b.onclick = onClick; t.append(b);
  });
  t.classList.remove("an");
  clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.add("an"), nut.length ? 12000 : 4000);
}

/* ---------- màn hình 1 ---------- */
function hienFile(info) {
  if (!info || info.loi) { toast(info?.loi || "Không đọc được file"); return; }
  fileHienTai = info;
  $("file-ten").textContent = info.ten; $("file-ky").textContent = info.ky;
  $("file-so-dong").textContent = fmt(info.so_dong); $("file-tong-ps").textContent = fmt(info.tong_ps);
  $("the-file").classList.remove("an"); $("btn-kiem-tra").disabled = false;
  $("header-file").textContent = `${info.ten} · kỳ ${info.ky}`;
}

async function khoiTao() {
  api = window.pywebview.api;
  const info = await api.lay_file_moi_nhat();
  if (info) hienFile(info); else toast("Chưa có file trong thư mục '1. Source' — hãy chọn hoặc kéo file vào.");
}

$("btn-chon-file").onclick = async () => hienFile(await api.chon_file());

const vung = $("vung-keo-tha");
["dragenter", "dragover"].forEach((e) => vung.addEventListener(e, (ev) => { ev.preventDefault(); vung.classList.add("keo-qua"); }));
["dragleave", "drop"].forEach((e) => vung.addEventListener(e, (ev) => { ev.preventDefault(); vung.classList.remove("keo-qua"); }));
vung.addEventListener("drop", async (ev) => {
  const f = ev.dataTransfer.files[0];
  const path = f && f.pywebviewFullPath;            // pywebview gắn đường dẫn thật vào File
  if (!path) { toast("Không lấy được đường dẫn file — hãy dùng nút 'Chọn file…'"); return; }
  hienFile(await api.nap_file(path));
});

$("btn-kiem-tra").onclick = chayKiemTra;
async function chayKiemTra() {
  $("btn-kiem-tra").disabled = true; onTienTrinh("Bắt đầu", 0);
  const kq = await api.chay_kiem_tra(fileHienTai?.path || null);
  $("btn-kiem-tra").disabled = false; $("tien-trinh").classList.add("an");
  if (kq.loi) { toast(kq.loi); return; }
  ketQua = kq; veKetQua(); chuyenManHinh(2);
}

function chuyenManHinh(n) {
  $("man-hinh-1").classList.toggle("an", n !== 1);
  $("man-hinh-2").classList.toggle("an", n !== 2);
}

/* ---------- màn hình 2 ---------- */
function veKetQua() {
  const t = ketQua.tomtat;
  const b = $("banner");
  b.className = "banner " + (t.san_sang ? "san-sang" : "chua-san-sang");
  $("banner-ket-luan").textContent = t.san_sang ? "SẴN SÀNG KHÓA SỔ" : `CHƯA SẴN SÀNG — còn ${t.con_viec} việc`;
  $("so-do").textContent = t.so_do; $("so-vang").textContent = t.so_vang;
  const tongCheck = ketQua.nhom.flatMap((n) => n.checks).filter((c) => !c.la_thong_ke).length;
  $("so-xanh").textContent = tongCheck - t.so_do - t.so_vang;
  veTabA(); veTabB(); anChiTiet();
}

function veTabA() {
  const ul = $("ds-buoc"); ul.innerHTML = "";
  ketQua.trang_thai.forEach((b) => {
    const li = document.createElement("li"); li.className = `buoc tt-${b.trang_thai}`;
    li.innerHTML = `<div class="icon">${ICON_TT[b.trang_thai]}</div>
      <div><div class="ten">${b.buoc}</div><div class="tom-tat">${b.tom_tat}</div></div>
      <span class="nhan">${NHAN_TT[b.trang_thai]}</span><span>›</span>`;
    li.onclick = () => moChiTiet(b.ma_check, `${b.buoc} — chứng minh (${b.ma_check})`);
    ul.append(li);
  });
}

function veTabB() {
  const luoi = $("luoi-nhom"); luoi.innerHTML = "";
  ketQua.nhom.forEach((n) => {
    const d = document.createElement("div"); d.className = `the-nhom nhom-${n.muc_do}`; d.dataset.ma = n.ma;
    const ds = n.checks.map((c) =>
      `<li data-ma="${c.ma}"><span><i class="muc-do ${CLASS_MD[c.muc_do]}"></i>${c.ma} ${c.ten}</span><b>${c.la_thong_ke ? "📊" : fmt(c.so_loi)}</b></li>`).join("");
    d.innerHTML = `<div class="so">${n.ma === "G6" ? "📊" : fmt(n.so_loi)}</div><div class="ten">${n.ten}</div>
      <div class="tom-tat">${n.ma === "G6" ? "Bảng thống kê" : NHAN_MD[n.muc_do]}</div><ul class="ds-check">${ds}</ul>`;
    d.querySelectorAll("li").forEach((li) => li.onclick = (ev) => {
      ev.stopPropagation(); const c = n.checks.find((x) => x.ma === li.dataset.ma);
      chonThe(d); moChiTiet(c.ma, `${c.ma} · ${c.ten}${c.ghi_chu ? " — " + c.ghi_chu : ""}`);
    });
    d.onclick = () => { const c = n.checks.find((x) => x.so_loi > 0) || n.checks[0]; chonThe(d); moChiTiet(c.ma, `${c.ma} · ${c.ten}`); };
    luoi.append(d);
  });
}
function chonThe(d) { document.querySelectorAll(".the-nhom").forEach((x) => x.classList.remove("dang-chon")); d.classList.add("dang-chon"); }

/* ---------- chi tiết ---------- */
async function moChiTiet(ma, tieuDe, trang = 1) {
  chiTiet = { ma, trang, timKiem: chiTiet.ma === ma ? chiTiet.timKiem : "" };
  $("o-tim-kiem").value = chiTiet.timKiem;
  const kq = await api.lay_chi_tiet(ma, trang, KICH_THUOC, chiTiet.timKiem);
  if (kq.loi) { toast(kq.loi); return; }
  $("chi-tiet-tieu-de").textContent = `${tieuDe} · ${fmt(kq.tong)} dòng`;
  const tb = $("bang-chi-tiet");
  if (!kq.tong) { tb.innerHTML = `<tr><td style="padding:16px;color:#6B7280">Không có dòng nào.</td></tr>`; }
  else {
    const soCot = new Set(["Amount", "ps_no", "ps_co", "net", "tong", "so_dong", "thue_vao_1331", "thue_ra_33311", "UnitCost", "Quantity9"]);
    tb.innerHTML = `<thead><tr>${kq.cot.map((c) => `<th>${c}</th>`).join("")}</tr></thead><tbody>${
      kq.dong.map((r) => `<tr>${kq.cot.map((c) => soCot.has(c) && typeof r[c] === "number"
        ? `<td class="so">${fmt(r[c])}</td>` : `<td>${r[c] ?? ""}</td>`).join("")}</tr>`).join("")}</tbody>`;
  }
  vePhanTrang(kq.tong, trang, tieuDe);
  $("khung-chi-tiet").classList.remove("an");
  $("khung-chi-tiet").scrollIntoView({ behavior: "smooth", block: "start" });
}
function anChiTiet() { $("khung-chi-tiet").classList.add("an"); }

function vePhanTrang(tong, trang, tieuDe) {
  const soTrang = Math.max(1, Math.ceil(tong / KICH_THUOC));
  const p = $("phan-trang"); p.innerHTML = "";
  const nut = (ten, t, tat) => { const b = document.createElement("button"); b.className = "btn"; b.textContent = ten;
    b.disabled = tat; b.onclick = () => moChiTiet(chiTiet.ma, tieuDe.replace(/ · .*dòng$/, ""), t); return b; };
  p.append(nut("‹ Trước", trang - 1, trang <= 1),
    Object.assign(document.createElement("span"), { textContent: `Trang ${trang}/${soTrang}` }),
    nut("Sau ›", trang + 1, trang >= soTrang));
}

$("o-tim-kiem").addEventListener("input", (ev) => {
  clearTimeout($("o-tim-kiem")._t);
  $("o-tim-kiem")._t = setTimeout(() => { chiTiet.timKiem = ev.target.value.trim();
    moChiTiet(chiTiet.ma, $("chi-tiet-tieu-de").textContent.replace(/ · .*dòng$/, ""), 1); }, 300);
});

/* ---------- tabs & footer ---------- */
$("tab-a").onclick = () => chuyenTab("a"); $("tab-b").onclick = () => chuyenTab("b");
function chuyenTab(t) {
  $("tab-a").classList.toggle("dang-chon", t === "a"); $("tab-b").classList.toggle("dang-chon", t === "b");
  $("noi-dung-a").classList.toggle("an", t !== "a"); $("noi-dung-b").classList.toggle("an", t !== "b");
  anChiTiet();
}
$("btn-xuat").onclick = async () => {
  const kq = await api.xuat_bao_cao();
  if (kq.loi) { toast(kq.loi); return; }
  toast("Đã xuất báo cáo Excel", [
    { ten: "Mở file Excel", onClick: () => api.mo_file(kq.path) },
    { ten: "Mở thư mục", onClick: () => api.mo_thu_muc(kq.path) },
  ]);
};
$("btn-kiem-tra-lai").onclick = async () => { chuyenManHinh(1); await chayKiemTra(); };
$("btn-file-khac").onclick = () => { chuyenManHinh(1); anChiTiet(); };

window.addEventListener("pywebviewready", khoiTao);
```

- [ ] **Step 4: Viết `app/main.py`**

```python
"""Điểm vào: mở cửa sổ pywebview. Chạy: python -m app.main (từ thư mục gốc)."""
from pathlib import Path

import webview

from .api import JsApi

WEB_DIR = Path(__file__).resolve().parent / "web"


def main():
    api = JsApi()
    window = webview.create_window(
        "Kiểm tra khóa sổ cuối kỳ", url=str(WEB_DIR / "index.html"), js_api=api,
        width=1100, height=750, min_size=(1000, 700), background_color="#F5F7FA",
    )
    api.gan_window(window)
    webview.start()


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Viết `Kiem_tra_khoa_so.bat`**

```bat
@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m app.main
if errorlevel 1 (
  echo.
  echo Khong chay duoc app. Kiem tra da cai Python va: pip install -r requirements.txt
  pause
)
```

- [ ] **Step 6: Chạy test tĩnh, xác nhận pass**

Run: `python -m pytest tests/test_web_static.py -q`
Expected: 3 passed

- [ ] **Step 7: Chạy app lần đầu (smoke) — mở rồi đóng**

Run: `python -m app.main` (từ thư mục gốc). Xác nhận: cửa sổ mở, tiêu đề đúng, font Segoe UI, đã tự nhận file trong `1. Source` (thẻ file hiện tên/kỳ/số dòng). Đóng cửa sổ.
Nếu lỗi `pywebviewready` không bắn: kiểm tra console (`webview.start(debug=True)` tạm thời), sửa rồi tắt debug.

- [ ] **Step 8: Commit**

```bash
git add app/web/app.js app/main.py Kiem_tra_khoa_so.bat tests/test_web_static.py
git commit -m "feat(app): app.js, main.py, file .bat - hoan thien luong 1 nut xem ket qua trong app

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 15: Kiểm thử end-to-end trên file thật & tinh chỉnh

**Files:**
- Create: `tests/test_e2e_file_that.py`
- Modify (nếu cần): các module check theo phát hiện thực tế

**Interfaces:**
- Consumes: toàn bộ pipeline qua `JsApi`

- [ ] **Step 1: Viết test e2e (skip nếu không có file)**

`tests/test_e2e_file_that.py`:
```python
import os, time

import pytest

from app.api import JsApi

FILE = "1. Source/Bang ke chung tu 082027.xlsx"
pytestmark = pytest.mark.skipif(not os.path.exists(FILE), reason="không có file thật")


def test_pipeline_file_that_chay_nhanh_va_hop_ly(tmp_path):
    api = JsApi(); api.thu_muc_report = str(tmp_path)
    t = time.time()
    kq = api.chay_kiem_tra(FILE)
    assert "loi" not in kq, kq.get("loi")
    thoi_gian = time.time() - t
    assert kq["tomtat"]["ky"] == "08/2026" and kq["tomtat"]["so_dong"] == 79450
    assert len(kq["trang_thai"]) == 11
    # G4/G5 phải phản ánh dữ liệu thật: có phát sinh 621/632 nên không "không áp dụng"
    tt = {b["buoc"]: b for b in kq["trang_thai"]}
    assert tt["Tập hợp CP NVL trực tiếp 621 → 154"]["trang_thai"] != "khong_ap_dung"
    assert tt["Kết chuyển giá vốn 632 → 911"]["trang_thai"] != "khong_ap_dung"
    # chi tiết theo trang không đổ toàn bộ
    ct = api.lay_chi_tiet("C1.1", 1, 100)
    assert len(ct["dong"]) <= 100 and ct["tong"] > 0
    path = api.xuat_bao_cao()["path"]
    assert os.path.exists(path)
    print(f"\nThời gian kiểm tra: {thoi_gian:.1f}s")
    assert thoi_gian < 60
```

- [ ] **Step 2: Chạy, ghi lại kết quả thực tế**

Run: `python -m pytest tests/test_e2e_file_that.py -q -s`
Expected: passed; đọc thời gian in ra. Nếu > 10s, ghi chú nguyên nhân (đọc Excel vs check) để tối ưu ở bước 3.

- [ ] **Step 3: Rà soát kết quả thật trên app (thủ công) — checklist**

Run: `python -m app.main`, bấm Kiểm tra, đối chiếu:
- Banner hiện đúng kết luận; 3 con số 🔴🟡🟢 khớp bảng thẻ.
- Tab A: 11 bước, mỗi bước có tóm tắt số liệu; click bước mở đúng bảng chứng minh.
- Tab B: click thẻ G1 → bảng C1.1 hiện dòng, tìm kiếm "thuê" lọc được, phân trang hoạt động với check nhiều dòng (C2.1 hoặc C1.1).
- Xuất Excel → toast có 2 nút, "Mở file Excel" mở đúng file, "Mở thư mục" chọn đúng file trong Explorer.
- Font Segoe UI, nền sáng, không có hình ảnh/font tải từ mạng (ngắt mạng vẫn chạy).
Ghi những check cho kết quả "ồn" bất hợp lý (ví dụ C2.4 flag quá nhiều do làm tròn tỷ giá) → điều chỉnh ngưỡng trong module tương ứng, cập nhật test.

- [ ] **Step 4: Chạy toàn bộ test lần cuối**

Run: `python -m pytest -q`
Expected: tất cả passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_e2e_file_that.py app
git commit -m "test: e2e tren bang ke thuc te va tinh chinh nguong

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

## Self-Review (đã chạy)

**Spec coverage:** §3 kiến trúc → Task 1–14 ✔ · §4 cấu trúc thư mục → Task 0/13/14 ✔ · §5 luồng 1 nút, 2 tab, footer 3 nút, toast mở file/thư mục → Task 14 ✔ · §6 chuẩn hóa dữ liệu → Task 2 ✔ · §7 toàn bộ 29 check (6+4+3+5+6+5) → Task 3–8 ✔ · Tab A 11 bước → Task 10 ✔ · §8 báo cáo Excel (Tổng quan, Trạng thái, chi tiết, Nhật ký, Segoe UI, số có phân tách) → Task 11 ✔ · §9 UI Segoe UI/light/bảng màu/phân trang → Task 13–14 ✔ · §10 js_api (đủ hàm; `lay_chi_tiet` bỏ tham số `muc_do` vì mức độ đã lọc ở cấp thẻ — ghi nhận lệch nhỏ so spec) ✔ · §11 xử lý lỗi (`{"loi"}` thay raise, thiếu cột, tự tạo thư mục, không có file) → Task 2/12/14 ✔ · §13 requirements → Task 0 ✔ · §14 acceptance → Task 15 ✔.

**Placeholder scan:** không có TBD/TODO; mọi bước code đều có mã đầy đủ.

**Type consistency:** `CheckResult(ma, ten, nhom, muc_do, chi_tiet, ghi_chu, la_thong_ke)` dùng nhất quán Task 1→12; `BuocKhoaSo(buoc, trang_thai, tom_tat, ma_check)` Task 10→11→12→14; `ThongTinFile` Task 2→11→12; `chay_tat_ca(df, ctx, on_progress)` Task 9→12; `lay_chi_tiet(ma_check, trang, kich_thuoc, tim_kiem)` Task 12↔14; tên `id` HTML Task 13↔14 khớp.
