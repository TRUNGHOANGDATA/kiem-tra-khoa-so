# Kho Chốt Sổ & Đối Chiếu Theo Kỳ — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cho phép chốt sổ từng *(chi nhánh × kỳ)* vào một kho SQLite nhúng, đối chiếu dữ liệu nguồn với bản đã chốt để phát hiện thay đổi, kèm giao diện chốt/xác nhận cập nhật và sao lưu/phục hồi/nhập kho.

**Architecture:** Thêm package `app/kho/` (lớp lưu trữ SQLite thuần IO) + module `app/chot_so.py` (logic thuần: vân tay, đối chiếu, diff). `app/api.py` nối UI ↔ hai module. Frontend mở rộng `app.js`/HTML/CSS theo hệ "Premium Light". Không đụng `app/checks` (trừ hạ cấp C7.5), `loader`, `trang_thai`, `report`.

**Tech Stack:** Python 3, pandas, `sqlite3` (stdlib — KHÔNG thêm dependency), gzip, hashlib; pywebview + HTML/CSS/JS.

**Spec:** `docs/spec/2026-09-16-kho-chot-so-va-doi-chieu-ky-design.md`

## Global Constraints

- Giữ **259 test cũ xanh** dưới `pytest -W error` (cảnh báo = lỗi).
- **Không thêm thư viện ngoài** — chỉ dùng stdlib + pandas đã có.
- Kho ở `3. Chot so/kho_chot_so.sqlite` — **git-ignored**, không commit dữ liệu kế toán.
- Toàn bộ dữ liệu trong **một file .sqlite** (sao lưu = copy 1 file).
- **Chỉ cảnh báo khi có bằng chứng:** không cảnh báo drift khi kỳ chưa có snapshot.
- Append-only: chốt lại/mở lại **không xóa** bản cũ (đặt `con_hieu_luc=0`).
- Mọi thao tác ghi kho trong **một transaction**.
- Tên hàm/biến tiếng Việt không dấu-hoặc-có-dấu theo đúng lối code hiện tại (vd `van_tay`, `doi_chieu`, `luu_snapshot`).

---

### Task 1: Hạ cấp check C7.5 (413) thành nhắc nhẹ

**Files:**
- Modify: `app/checks/g7_phan_bo_trich_lap.py:41-44` (hàm `_canh_bao`) và `:77-81` (lời gọi C7.5)
- Test: `tests/test_g7_phan_bo_trich_lap.py`

**Interfaces:**
- Produces: C7.5 vẫn là `CheckResult` mã "C7.5" nhưng `la_thong_ke=True` → `muc_do_thuc` luôn `xanh`, không vào `tinh_ket_luan`.

- [ ] **Step 1: Sửa test C7.5 để yêu cầu không kéo kết luận**

Trong `tests/test_g7_phan_bo_trich_lap.py`, tìm test C7.5 (kỳ có ngoại tệ, không có 413). Đổi kỳ vọng: kết quả C7.5 phải `la_thong_ke is True` và `muc_do_thuc == "xanh"` dù vẫn có dòng nhắc.

```python
def test_c75_ngoai_te_khong_413_chi_nhac_khong_keo_ket_luan():
    df = _df([
        # dòng ngoại tệ chạm TK tiền tệ, không có bút toán 413
        {"DebitAccount": "1121", "CreditAccount": "331", "Amount": 1000.0, "CurrencyCode": "USD"},
    ])
    kq = {r.ma: r for r in kiem_tra(df, BoiCanh(8, 2026))}
    c75 = kq["C7.5"]
    assert c75.la_thong_ke is True          # nhắc nhẹ, không phải lỗi
    assert c75.muc_do_thuc == "xanh"        # không kéo kết luận khóa sổ
    assert len(c75.chi_tiet) == 1           # vẫn giữ dòng nhắc để không bỏ sót
```

- [ ] **Step 2: Chạy test — xác nhận đỏ**

Run: `pytest tests/test_g7_phan_bo_trich_lap.py::test_c75_ngoai_te_khong_413_chi_nhac_khong_keo_ket_luan -v`
Expected: FAIL (hiện tại C7.5 trả `la_thong_ke=False`).

- [ ] **Step 3: Thêm cờ `la_thong_ke` vào `_canh_bao` và bật cho C7.5**

Sửa hàm `_canh_bao`:

```python
def _canh_bao(ma: str, ten: str, thieu: bool, ly_do: str, ghi_chu: str = "",
              la_thong_ke: bool = False) -> CheckResult:
    """Cảnh báo: chỉ bắn khi có bằng chứng đối ứng trong chính file.

    la_thong_ke=True → chỉ nhắc, KHÔNG kéo kết luận khóa sổ (dùng cho các mục
    không trọng yếu như đánh giá tỷ giá 413, hiếm khi phát sinh)."""
    ct = pd.DataFrame([{"ket_luan": ly_do}] if thieu else [], columns=["ket_luan"])
    return CheckResult(ma, ten, NHOM, VANG, ct, ghi_chu, la_thong_ke=la_thong_ke)
```

Trong lời gọi C7.5 (`:77`), thêm `la_thong_ke=True`:

```python
    kq.append(_canh_bao("C7.5", "Chưa đánh giá chênh lệch tỷ giá cuối kỳ",
                        co_du_ngoai_te and no_413 == 0 and co_413 == 0,
                        "Có phát sinh ngoại tệ trên tài khoản tiền tệ nhưng không thấy bút toán 413"
                        " — kiểm tra đánh giá lại số dư gốc ngoại tệ cuối kỳ",
                        ghi_chu="Chỉ xét dòng ngoại tệ chạm TK " + "/".join(TK_TIEN_TE),
                        la_thong_ke=True))
```

- [ ] **Step 4: Chạy lại test C7.5 + toàn bộ g7 — xác nhận xanh**

Run: `pytest tests/test_g7_phan_bo_trich_lap.py -v`
Expected: PASS toàn bộ (sửa thêm bất kỳ test C7.5 cũ nào còn kỳ vọng nó kéo kết luận).

- [ ] **Step 5: Commit**

```bash
git add app/checks/g7_phan_bo_trich_lap.py tests/test_g7_phan_bo_trich_lap.py
git commit -m "feat(checks): C7.5 (413 tỷ giá) hạ xuống nhắc nhẹ, không kéo kết luận"
```

---

### Task 2: Vân tay dữ liệu (canonical hóa)

**Files:**
- Create: `app/chot_so.py`
- Test: `tests/test_chot_so.py`

**Interfaces:**
- Produces:
  - `chuoi_dong(df: pd.DataFrame) -> pd.Series` — mỗi phần tử là chuỗi canonical của một dòng (vectorized).
  - `@dataclass VanTay { so_dong:int; tong_ps:float; ma_bam:str }`
  - `van_tay(df: pd.DataFrame) -> VanTay`

- [ ] **Step 1: Viết test vân tay ổn định & nhạy thay đổi**

```python
import pandas as pd
from app.chot_so import van_tay, chuoi_dong

def _df(rows):
    return pd.DataFrame(rows)

def test_van_tay_giong_nhau_khi_du_lieu_giong():
    df1 = _df([{"DocNo": "1", "Amount": 100.0}, {"DocNo": "2", "Amount": 200.0}])
    df2 = _df([{"DocNo": "1", "Amount": 100.0}, {"DocNo": "2", "Amount": 200.0}])
    assert van_tay(df1).ma_bam == van_tay(df2).ma_bam
    assert van_tay(df1).so_dong == 2
    assert van_tay(df1).tong_ps == 300.0

def test_van_tay_khong_doi_khi_dao_thu_tu_dong():
    df1 = _df([{"DocNo": "1", "Amount": 100.0}, {"DocNo": "2", "Amount": 200.0}])
    df2 = _df([{"DocNo": "2", "Amount": 200.0}, {"DocNo": "1", "Amount": 100.0}])
    assert van_tay(df1).ma_bam == van_tay(df2).ma_bam  # đảo dòng ≠ đổi dữ liệu

def test_van_tay_khac_khi_sua_mot_dong():
    df1 = _df([{"DocNo": "1", "Amount": 100.0}])
    df2 = _df([{"DocNo": "1", "Amount": 100.01}])
    assert van_tay(df1).ma_bam != van_tay(df2).ma_bam

def test_van_tay_on_dinh_qua_json_round_trip():
    df = _df([{"DocNo": "1", "DocDate": pd.Timestamp("2026-08-01"), "Amount": 100.0}])
    lai = pd.read_json(df.to_json(orient="records", date_format="iso"))
    assert van_tay(df).ma_bam == van_tay(lai).ma_bam
```

- [ ] **Step 2: Chạy — xác nhận đỏ**

Run: `pytest tests/test_chot_so.py -v`
Expected: FAIL ("No module named 'app.chot_so'").

- [ ] **Step 3: Viết `app/chot_so.py` phần vân tay**

```python
"""Logic chốt sổ: vân tay dữ liệu, đối chiếu bản đã chốt, sinh diff.

Thuần logic — không chạm SQLite (lớp kho ở app/kho) hay UI. Nhận DataFrame,
trả kết quả để api.py bơm ra giao diện. Dùng chung MỘT cách canonical hóa dòng
cho cả vân tay lẫn diff, nên 'giống nhau' được định nghĩa nhất quán ở một chỗ.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import reduce

import pandas as pd

NGAN = "\x01"  # ngăn cách cột trong một dòng — ký tự không xuất hiện trong dữ liệu kế toán


def chuoi_dong(df: pd.DataFrame) -> pd.Series:
    """Chuỗi canonical cho từng dòng (vectorized, chịu được 80k dòng).

    Cùng dữ liệu → cùng chuỗi, kể cả sau khi lưu/đọc lại qua JSON. Số thực làm
    tròn 4 chữ số (đủ phân biệt tiền/số lượng, tránh nhiễu số dấu phẩy động);
    ngày về 'yyyy-mm-dd'; NaN về rỗng.
    """
    if len(df) == 0:
        return pd.Series([], dtype="string")
    cols = sorted(map(str, df.columns))
    phan = []
    for c in cols:
        s = df[c]
        if pd.api.types.is_datetime64_any_dtype(s):
            gt = s.dt.strftime("%Y-%m-%d").fillna("")
        elif pd.api.types.is_float_dtype(s):
            gt = s.map(lambda x: "" if pd.isna(x) else f"{x:.4f}")
        else:
            gt = s.astype("string").fillna("")
        phan.append(c + "=" + gt.astype("string"))
    return reduce(lambda a, b: a + NGAN + b, phan)


@dataclass
class VanTay:
    so_dong: int
    tong_ps: float
    ma_bam: str


def van_tay(df: pd.DataFrame) -> VanTay:
    """Vân tay của một frame: số dòng, tổng phát sinh, mã băm sha256 độc lập thứ tự dòng."""
    dong = sorted(chuoi_dong(df).tolist())
    ma = hashlib.sha256("\n".join(dong).encode("utf-8")).hexdigest()
    tong = float(df["Amount"].sum()) if "Amount" in df.columns and len(df) else 0.0
    return VanTay(so_dong=int(len(df)), tong_ps=tong, ma_bam=ma)
```

- [ ] **Step 4: Chạy — xác nhận xanh**

Run: `pytest tests/test_chot_so.py -v`
Expected: PASS 4 test.

- [ ] **Step 5: Commit**

```bash
git add app/chot_so.py tests/test_chot_so.py
git commit -m "feat(chot-so): van tay du lieu canonical (on dinh qua luu/doc)"
```

---

### Task 3: Đối chiếu & diff thêm/bớt

**Files:**
- Modify: `app/chot_so.py`
- Test: `tests/test_chot_so.py`

**Interfaces:**
- Consumes: `chuoi_dong`, `VanTay` (Task 2).
- Produces:
  - Hằng: `KHOP = "KHOP"`, `LECH = "LECH"`, `CHUA_CHOT = "CHUA_CHOT"`.
  - `@dataclass KetQuaDoiChieu { trang_thai:str; delta_dong:int; delta_ps:float; so_ct_anh_huong:int }`
  - `doi_chieu(vt_chot: VanTay | None, df_hien_tai: pd.DataFrame, df_chot: pd.DataFrame | None = None) -> KetQuaDoiChieu`
  - `dien_diff(df_chot: pd.DataFrame, df_hien_tai: pd.DataFrame) -> dict` với khóa `them` (DataFrame), `bot` (DataFrame), `tom_tat` (dict).

- [ ] **Step 1: Viết test đối chiếu + diff**

```python
from app.chot_so import doi_chieu, dien_diff, van_tay, KHOP, LECH, CHUA_CHOT

def test_doi_chieu_chua_chot_khi_khong_co_van_tay():
    df = _df([{"DocCode": "PX", "DocNo": "1", "DebitAccount": "621", "Amount": 100.0}])
    assert doi_chieu(None, df).trang_thai == CHUA_CHOT

def test_doi_chieu_khop_khi_du_lieu_khong_doi():
    df = _df([{"DocCode": "PX", "DocNo": "1", "DebitAccount": "621", "Amount": 100.0}])
    assert doi_chieu(van_tay(df), df).trang_thai == KHOP

def test_doi_chieu_lech_va_bao_delta():
    cu = _df([{"DocCode": "PX", "DocNo": "1", "DebitAccount": "621", "Amount": 100.0}])
    moi = _df([
        {"DocCode": "PX", "DocNo": "1", "DebitAccount": "621", "Amount": 100.0},
        {"DocCode": "PX", "DocNo": "2", "DebitAccount": "621", "Amount": 50.0},
    ])
    kq = doi_chieu(van_tay(cu), moi, df_chot=cu)
    assert kq.trang_thai == LECH
    assert kq.delta_dong == 1
    assert kq.delta_ps == 50.0

def test_dien_diff_them_bot():
    cu = _df([
        {"DocCode": "PX", "DocNo": "1", "DebitAccount": "621", "Amount": 100.0},
        {"DocCode": "PX", "DocNo": "9", "DebitAccount": "621", "Amount": 10.0},
    ])
    moi = _df([
        {"DocCode": "PX", "DocNo": "1", "DebitAccount": "621", "Amount": 100.0},
        {"DocCode": "PX", "DocNo": "2", "DebitAccount": "621", "Amount": 50.0},
    ])
    d = dien_diff(cu, moi)
    assert len(d["them"]) == 1 and d["them"].iloc[0]["DocNo"] == "2"
    assert len(d["bot"]) == 1 and d["bot"].iloc[0]["DocNo"] == "9"
    assert d["tom_tat"]["so_them"] == 1 and d["tom_tat"]["so_bot"] == 1
```

- [ ] **Step 2: Chạy — xác nhận đỏ**

Run: `pytest tests/test_chot_so.py -k "doi_chieu or diff" -v`
Expected: FAIL (chưa định nghĩa).

- [ ] **Step 3: Thêm đối chiếu + diff vào `app/chot_so.py`**

```python
from collections import Counter

KHOP, LECH, CHUA_CHOT = "KHOP", "LECH", "CHUA_CHOT"


@dataclass
class KetQuaDoiChieu:
    trang_thai: str
    delta_dong: int = 0
    delta_ps: float = 0.0
    so_ct_anh_huong: int = 0


def _so_ct(df: pd.DataFrame) -> pd.Series:
    """Nhãn chứng từ để gom hiển thị: DocCode+DocNo (chấp nhận thiếu cột)."""
    dc = df["DocCode"].astype("string").fillna("") if "DocCode" in df.columns else ""
    dn = df["DocNo"].astype("string").fillna("") if "DocNo" in df.columns else ""
    return (dc.astype(str) + "·" + dn.astype(str)) if hasattr(dc, "astype") else pd.Series([], dtype="string")


def doi_chieu(vt_chot, df_hien_tai, df_chot=None) -> KetQuaDoiChieu:
    """So dữ liệu hiện tại với bản đã chốt. vt_chot=None → CHƯA_CHỐT (im lặng)."""
    if vt_chot is None:
        return KetQuaDoiChieu(CHUA_CHOT)
    vt_moi = van_tay(df_hien_tai)
    if vt_moi.ma_bam == vt_chot.ma_bam:
        return KetQuaDoiChieu(KHOP)
    delta_dong = vt_moi.so_dong - vt_chot.so_dong
    delta_ps = round(vt_moi.tong_ps - vt_chot.tong_ps, 2)
    so_ct = 0
    if df_chot is not None:
        d = dien_diff(df_chot, df_hien_tai)
        so_ct = d["tom_tat"]["so_ct_anh_huong"]
    return KetQuaDoiChieu(LECH, delta_dong, delta_ps, so_ct)


def dien_diff(df_chot: pd.DataFrame, df_hien_tai: pd.DataFrame) -> dict:
    """Dòng THÊM (có ở hiện tại, không ở bản chốt) và BỚT (ngược lại) theo hiệu đa tập.

    Băm cả dòng (không phụ thuộc khóa chứng từ — vốn có known-issue ghép không dấu
    tách), rồi gom hiển thị theo chứng từ để chỉ đúng chỗ.
    """
    key_chot = chuoi_dong(df_chot)
    key_moi = chuoi_dong(df_hien_tai)
    dem_chot, dem_moi = Counter(key_chot.tolist()), Counter(key_moi.tolist())
    du_moi = dem_moi - dem_chot   # thêm
    du_chot = dem_chot - dem_moi  # bớt

    def _lay(df, keys_series, con: Counter) -> pd.DataFrame:
        if not con:
            return df.iloc[0:0].copy()
        can = Counter(con)
        idx = []
        for i, k in enumerate(keys_series.tolist()):
            if can.get(k, 0) > 0:
                idx.append(keys_series.index[i])
                can[k] -= 1
        return df.loc[idx].reset_index(drop=True)

    them = _lay(df_hien_tai, key_moi, du_moi)
    bot = _lay(df_chot, key_chot, du_chot)
    ct = set(_so_ct(them).tolist()) | set(_so_ct(bot).tolist())
    tom_tat = {"so_them": int(len(them)), "so_bot": int(len(bot)),
               "so_ct_anh_huong": int(len([c for c in ct if c and c != "·"]))}
    return {"them": them, "bot": bot, "tom_tat": tom_tat}
```

- [ ] **Step 4: Chạy — xác nhận xanh**

Run: `pytest tests/test_chot_so.py -v`
Expected: PASS toàn bộ Task 2 + 3.

- [ ] **Step 5: Commit**

```bash
git add app/chot_so.py tests/test_chot_so.py
git commit -m "feat(chot-so): doi chieu KHOP/LECH + dien diff them/bot theo chung tu"
```

---

### Task 4: Kho SQLite — schema & kết nối/migration

**Files:**
- Create: `app/kho/__init__.py`, `app/kho/schema.py`, `app/kho/ket_noi.py`
- Test: `tests/test_kho_ket_noi.py`

**Interfaces:**
- Produces:
  - `schema.PHIEN_BAN_SCHEMA: int = 1`
  - `schema.DDL: list[str]` (câu tạo bảng)
  - `ket_noi.mo_kho(path: str) -> sqlite3.Connection` — tạo file+thư mục nếu chưa có, áp schema, migrate, đặt `row_factory=sqlite3.Row`.
  - `ket_noi.PhienBanMoiHon(Exception)` — ném khi file có `schema_version` > bản đang chạy.

- [ ] **Step 1: Viết test tạo kho & từ chối bản mới hơn**

```python
import sqlite3
from pathlib import Path
import pytest
from app.kho import ket_noi
from app.kho.schema import PHIEN_BAN_SCHEMA

def test_mo_kho_tao_file_va_bang(tmp_path):
    p = tmp_path / "3. Chot so" / "kho.sqlite"
    con = ket_noi.mo_kho(str(p))
    ten = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"snapshot", "snapshot_check", "snapshot_du_lieu", "schema_version"} <= ten
    assert con.execute("SELECT phien_ban FROM schema_version").fetchone()[0] == PHIEN_BAN_SCHEMA
    assert p.exists()

def test_mo_kho_tu_choi_phien_ban_moi_hon(tmp_path):
    p = tmp_path / "kho.sqlite"
    con = ket_noi.mo_kho(str(p)); con.execute(
        "UPDATE schema_version SET phien_ban = ?", (PHIEN_BAN_SCHEMA + 1,)); con.commit(); con.close()
    with pytest.raises(ket_noi.PhienBanMoiHon):
        ket_noi.mo_kho(str(p))
```

- [ ] **Step 2: Chạy — xác nhận đỏ**

Run: `pytest tests/test_kho_ket_noi.py -v`
Expected: FAIL ("No module named 'app.kho'").

- [ ] **Step 3: Viết schema.py**

```python
"""Định nghĩa bảng kho chốt sổ + phiên bản schema (để migrate nhẹ)."""
PHIEN_BAN_SCHEMA = 1

DDL = [
    """CREATE TABLE IF NOT EXISTS snapshot (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ky_nam INTEGER NOT NULL, ky_thang INTEGER NOT NULL, chi_nhanh TEXT NOT NULL,
        thoi_diem_chot TEXT NOT NULL, ghi_chu TEXT DEFAULT '',
        so_dong INTEGER NOT NULL, tong_ps REAL NOT NULL, van_tay TEXT NOT NULL,
        ket_luan_ma TEXT NOT NULL,
        so_do INTEGER DEFAULT 0, so_vang INTEGER DEFAULT 0,
        so_chua_lam INTEGER DEFAULT 0, so_can_ra INTEGER DEFAULT 0,
        con_hieu_luc INTEGER NOT NULL DEFAULT 1
    )""",
    "CREATE INDEX IF NOT EXISTS ix_snapshot_ky ON snapshot (ky_nam, ky_thang, chi_nhanh, con_hieu_luc)",
    """CREATE TABLE IF NOT EXISTS snapshot_check (
        snapshot_id INTEGER NOT NULL REFERENCES snapshot(id),
        ma TEXT, ten TEXT, muc_do TEXT, so_loi INTEGER, la_thong_ke INTEGER
    )""",
    "CREATE INDEX IF NOT EXISTS ix_check_snap ON snapshot_check (snapshot_id)",
    """CREATE TABLE IF NOT EXISTS snapshot_du_lieu (
        snapshot_id INTEGER PRIMARY KEY REFERENCES snapshot(id),
        du_lieu BLOB NOT NULL
    )""",
    "CREATE TABLE IF NOT EXISTS schema_version (phien_ban INTEGER NOT NULL)",
]
```

- [ ] **Step 4: Viết ket_noi.py**

```python
"""Mở/khởi tạo/migrate kho SQLite. Một file .sqlite = toàn bộ dữ liệu."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from . import schema


class PhienBanMoiHon(Exception):
    """File kho được tạo bởi bản tool mới hơn — từ chối để không làm hỏng dữ liệu."""


def mo_kho(path: str) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    for cau in schema.DDL:
        con.execute(cau)
    hang = con.execute("SELECT phien_ban FROM schema_version").fetchone()
    if hang is None:
        con.execute("INSERT INTO schema_version (phien_ban) VALUES (?)", (schema.PHIEN_BAN_SCHEMA,))
        con.commit()
    else:
        pb = int(hang[0])
        if pb > schema.PHIEN_BAN_SCHEMA:
            con.close()
            raise PhienBanMoiHon(f"Kho phiên bản {pb} > tool {schema.PHIEN_BAN_SCHEMA}. Hãy cập nhật tool.")
        # (migrate khi có phiên bản > 1 trong tương lai: chèn các bước ALTER ở đây)
    return con
```

Viết `app/kho/__init__.py`:

```python
from .ket_noi import PhienBanMoiHon, mo_kho  # noqa: F401
```

- [ ] **Step 5: Chạy — xác nhận xanh**

Run: `pytest tests/test_kho_ket_noi.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/kho/__init__.py app/kho/schema.py app/kho/ket_noi.py tests/test_kho_ket_noi.py
git commit -m "feat(kho): schema SQLite + mo_kho tao/migrate/tu choi ban moi hon"
```

---

### Task 5: Kho — lưu/đọc/liệt kê/mở lại snapshot (append-only)

**Files:**
- Create: `app/kho/luu_tru.py`
- Modify: `app/kho/__init__.py`
- Test: `tests/test_kho_luu_tru.py`

**Interfaces:**
- Consumes: `mo_kho` (Task 4), `chot_so.van_tay`/`chuoi_dong` (Task 2) chỉ ở phía gọi — kho nhận sẵn `van_tay_hash/so_dong/tong_ps`.
- Produces `class KhoChotSo`:
  - `__init__(self, path: str)`
  - `luu_snapshot(self, *, ky_nam:int, ky_thang:int, chi_nhanh:str, van_tay_hash:str, so_dong:int, tong_ps:float, ket_luan_ma:str, dem:dict, checks:list[dict], df:pd.DataFrame, ghi_chu:str="") -> int`
    - `dem` = `{"so_do","so_vang","so_chua_lam","so_can_ra"}`; `checks` = list `{"ma","ten","muc_do","so_loi","la_thong_ke"}`.
  - `doc_hieu_luc(self, ky_nam:int, ky_thang:int, chi_nhanh:str) -> dict | None` (header, không kèm df)
  - `doc_du_lieu(self, snapshot_id:int) -> pd.DataFrame`
  - `liet_ke(self, chi_nhanh:str|None=None, ky_nam:int|None=None, ky_thang:int|None=None) -> list[dict]`
  - `mo_lai(self, ky_nam:int, ky_thang:int, chi_nhanh:str) -> bool`
  - `dem_ky_hieu_luc(self) -> int`
  - `dong(self)`

- [ ] **Step 1: Viết test round-trip + append-only + mở lại**

```python
import pandas as pd
from app.kho.luu_tru import KhoChotSo

def _kho(tmp_path): return KhoChotSo(str(tmp_path / "kho.sqlite"))
DF = pd.DataFrame([{"DocCode": "PX", "DocNo": "1", "Amount": 100.0}])
CHECKS = [{"ma": "C1.1", "ten": "x", "muc_do": "vang", "so_loi": 0, "la_thong_ke": False}]

def _luu(kho, **ghi):
    args = dict(ky_nam=2026, ky_thang=8, chi_nhanh="A01", van_tay_hash="h1",
                so_dong=1, tong_ps=100.0, ket_luan_ma="SAN_SANG",
                dem={"so_do":0,"so_vang":0,"so_chua_lam":0,"so_can_ra":0},
                checks=CHECKS, df=DF, ghi_chu="")
    args.update(ghi)
    return kho.luu_snapshot(**args)

def test_luu_va_doc_hieu_luc(tmp_path):
    kho = _kho(tmp_path); sid = _luu(kho)
    h = kho.doc_hieu_luc(2026, 8, "A01")
    assert h["id"] == sid and h["van_tay"] == "h1" and h["ket_luan_ma"] == "SAN_SANG"

def test_du_lieu_round_trip(tmp_path):
    kho = _kho(tmp_path); sid = _luu(kho)
    lai = kho.doc_du_lieu(sid)
    assert list(lai["DocNo"]) == ["1"] and float(lai["Amount"].iloc[0]) == 100.0

def test_chot_lai_append_only(tmp_path):
    kho = _kho(tmp_path)
    sid1 = _luu(kho, van_tay_hash="h1", ghi_chu="lan 1")
    sid2 = _luu(kho, van_tay_hash="h2", ghi_chu="lan 2")
    assert sid2 != sid1
    assert kho.doc_hieu_luc(2026, 8, "A01")["id"] == sid2       # bản mới hiệu lực
    assert len(kho.liet_ke()) == 2                              # bản cũ vẫn còn
    assert kho.dem_ky_hieu_luc() == 1                           # nhưng chỉ 1 hiệu lực

def test_mo_lai(tmp_path):
    kho = _kho(tmp_path); _luu(kho)
    assert kho.mo_lai(2026, 8, "A01") is True
    assert kho.doc_hieu_luc(2026, 8, "A01") is None             # không còn bản hiệu lực
    assert len(kho.liet_ke()) == 1                              # nhưng lịch sử vẫn giữ
```

- [ ] **Step 2: Chạy — xác nhận đỏ**

Run: `pytest tests/test_kho_luu_tru.py -v`
Expected: FAIL (chưa có luu_tru).

- [ ] **Step 3: Viết `app/kho/luu_tru.py`**

```python
"""Repository kho chốt sổ: mọi thao tác đọc/ghi SQLite gói ở đây."""
from __future__ import annotations

import gzip
from datetime import datetime

import pandas as pd

from .ket_noi import mo_kho


def _nen(df: pd.DataFrame) -> bytes:
    return gzip.compress(df.to_json(orient="records", date_format="iso").encode("utf-8"))


def _giai_nen(blob: bytes) -> pd.DataFrame:
    import io
    return pd.read_json(io.StringIO(gzip.decompress(blob).decode("utf-8")))


class KhoChotSo:
    def __init__(self, path: str):
        self.path = path
        self.con = mo_kho(path)

    def dong(self):
        self.con.close()

    def luu_snapshot(self, *, ky_nam, ky_thang, chi_nhanh, van_tay_hash, so_dong,
                     tong_ps, ket_luan_ma, dem, checks, df, ghi_chu="") -> int:
        with self.con:  # transaction
            self.con.execute(
                "UPDATE snapshot SET con_hieu_luc=0 WHERE ky_nam=? AND ky_thang=? AND chi_nhanh=? AND con_hieu_luc=1",
                (ky_nam, ky_thang, chi_nhanh))
            cur = self.con.execute(
                """INSERT INTO snapshot (ky_nam, ky_thang, chi_nhanh, thoi_diem_chot, ghi_chu,
                     so_dong, tong_ps, van_tay, ket_luan_ma, so_do, so_vang, so_chua_lam, so_can_ra, con_hieu_luc)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1)""",
                (ky_nam, ky_thang, chi_nhanh, datetime.now().isoformat(timespec="seconds"), ghi_chu,
                 so_dong, tong_ps, van_tay_hash, ket_luan_ma,
                 dem.get("so_do", 0), dem.get("so_vang", 0), dem.get("so_chua_lam", 0), dem.get("so_can_ra", 0)))
            sid = int(cur.lastrowid)
            self.con.executemany(
                "INSERT INTO snapshot_check (snapshot_id, ma, ten, muc_do, so_loi, la_thong_ke) VALUES (?,?,?,?,?,?)",
                [(sid, c["ma"], c["ten"], c["muc_do"], int(c["so_loi"]), int(bool(c["la_thong_ke"]))) for c in checks])
            self.con.execute("INSERT INTO snapshot_du_lieu (snapshot_id, du_lieu) VALUES (?,?)", (sid, _nen(df)))
        return sid

    def doc_hieu_luc(self, ky_nam, ky_thang, chi_nhanh) -> dict | None:
        r = self.con.execute(
            "SELECT * FROM snapshot WHERE ky_nam=? AND ky_thang=? AND chi_nhanh=? AND con_hieu_luc=1",
            (ky_nam, ky_thang, chi_nhanh)).fetchone()
        return dict(r) if r else None

    def doc_du_lieu(self, snapshot_id) -> pd.DataFrame:
        r = self.con.execute("SELECT du_lieu FROM snapshot_du_lieu WHERE snapshot_id=?", (snapshot_id,)).fetchone()
        return _giai_nen(r[0]) if r else pd.DataFrame()

    def liet_ke(self, chi_nhanh=None, ky_nam=None, ky_thang=None) -> list[dict]:
        dk, tham = [], []
        if chi_nhanh: dk.append("chi_nhanh=?"); tham.append(chi_nhanh)
        if ky_nam: dk.append("ky_nam=?"); tham.append(ky_nam)
        if ky_thang: dk.append("ky_thang=?"); tham.append(ky_thang)
        sql = "SELECT * FROM snapshot"
        if dk: sql += " WHERE " + " AND ".join(dk)
        sql += " ORDER BY ky_nam DESC, ky_thang DESC, chi_nhanh, thoi_diem_chot DESC"
        return [dict(r) for r in self.con.execute(sql, tham)]

    def mo_lai(self, ky_nam, ky_thang, chi_nhanh) -> bool:
        with self.con:
            cur = self.con.execute(
                "UPDATE snapshot SET con_hieu_luc=0 WHERE ky_nam=? AND ky_thang=? AND chi_nhanh=? AND con_hieu_luc=1",
                (ky_nam, ky_thang, chi_nhanh))
        return cur.rowcount > 0

    def dem_ky_hieu_luc(self) -> int:
        return int(self.con.execute("SELECT COUNT(*) FROM snapshot WHERE con_hieu_luc=1").fetchone()[0])
```

Cập nhật `app/kho/__init__.py`:

```python
from .ket_noi import PhienBanMoiHon, mo_kho  # noqa: F401
from .luu_tru import KhoChotSo  # noqa: F401
```

- [ ] **Step 4: Chạy — xác nhận xanh**

Run: `pytest tests/test_kho_luu_tru.py -v`
Expected: PASS 5 test.

- [ ] **Step 5: Commit**

```bash
git add app/kho/luu_tru.py app/kho/__init__.py tests/test_kho_luu_tru.py
git commit -m "feat(kho): repository luu/doc/liet ke/mo lai snapshot (append-only)"
```

---

### Task 6: Kho — sao lưu / phục hồi / nhập-gộp

**Files:**
- Create: `app/kho/sao_luu.py`
- Modify: `app/kho/__init__.py`
- Test: `tests/test_kho_sao_luu.py`

**Interfaces:**
- Consumes: `KhoChotSo`, `mo_kho`, `PhienBanMoiHon`.
- Produces (module functions):
  - `sao_luu(path_kho:str, thu_muc_backup:str) -> str` — trả đường dẫn file backup.
  - `phuc_hoi(path_kho:str, path_nguon:str, thu_muc_backup:str) -> str` — backup kho hiện tại rồi thay bằng nguồn (sau kiểm hợp lệ). Trả đường dẫn backup vừa tạo.
  - `nhap_gop(path_kho:str, path_nguon:str) -> dict` — trả `{"da_them":int, "bo_qua_trung":int}`.

- [ ] **Step 1: Viết test backup/restore/merge**

```python
import pandas as pd
from pathlib import Path
from app.kho.luu_tru import KhoChotSo
from app.kho import sao_luu as sl

DF = pd.DataFrame([{"DocCode": "PX", "DocNo": "1", "Amount": 100.0}])
def _luu(kho, **g):
    a = dict(ky_nam=2026, ky_thang=8, chi_nhanh="A01", van_tay_hash="h1", so_dong=1,
             tong_ps=100.0, ket_luan_ma="SAN_SANG",
             dem={"so_do":0,"so_vang":0,"so_chua_lam":0,"so_can_ra":0},
             checks=[], df=DF, ghi_chu=""); a.update(g)
    return kho.luu_snapshot(**a)

def test_sao_luu_tao_file_mo_lai_duoc(tmp_path):
    kho = KhoChotSo(str(tmp_path / "kho.sqlite")); _luu(kho); kho.dong()
    bk = sl.sao_luu(str(tmp_path / "kho.sqlite"), str(tmp_path / "backup"))
    assert Path(bk).exists()
    assert KhoChotSo(bk).dem_ky_hieu_luc() == 1  # backup mở lại được, đủ dữ liệu

def test_phuc_hoi_backup_cu_roi_thay(tmp_path):
    a = KhoChotSo(str(tmp_path / "kho.sqlite")); _luu(a, chi_nhanh="A01"); a.dong()
    ng = KhoChotSo(str(tmp_path / "nguon.sqlite")); _luu(ng, chi_nhanh="B02"); ng.dong()
    sl.phuc_hoi(str(tmp_path / "kho.sqlite"), str(tmp_path / "nguon.sqlite"), str(tmp_path / "backup"))
    kho = KhoChotSo(str(tmp_path / "kho.sqlite"))
    assert kho.doc_hieu_luc(2026, 8, "B02") is not None  # đã thay bằng nguồn
    assert kho.doc_hieu_luc(2026, 8, "A01") is None
    assert any(Path(tmp_path / "backup").glob("*.sqlite"))  # có backup bản cũ

def test_nhap_gop_bo_qua_trung(tmp_path):
    a = KhoChotSo(str(tmp_path / "kho.sqlite")); _luu(a, chi_nhanh="A01", van_tay_hash="h1"); a.dong()
    ng = KhoChotSo(str(tmp_path / "nguon.sqlite"))
    _luu(ng, chi_nhanh="A01", van_tay_hash="h1")   # trùng
    _luu(ng, chi_nhanh="B02", van_tay_hash="h9")   # mới
    ng.dong()
    kq = sl.nhap_gop(str(tmp_path / "kho.sqlite"), str(tmp_path / "nguon.sqlite"))
    assert kq["da_them"] == 1 and kq["bo_qua_trung"] == 1
    kho = KhoChotSo(str(tmp_path / "kho.sqlite"))
    assert kho.doc_hieu_luc(2026, 8, "B02") is not None
```

- [ ] **Step 2: Chạy — xác nhận đỏ**

Run: `pytest tests/test_kho_sao_luu.py -v`
Expected: FAIL.

- [ ] **Step 3: Viết `app/kho/sao_luu.py`**

```python
"""Sao lưu / phục hồi / nhập-gộp kho — đều thao tác trên một file .sqlite."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from .ket_noi import mo_kho


def _ten_backup(thu_muc: str) -> str:
    Path(thu_muc).mkdir(parents=True, exist_ok=True)
    return str(Path(thu_muc) / f"kho_{datetime.now():%Y%m%d-%H%M%S}.sqlite")


def sao_luu(path_kho: str, thu_muc_backup: str) -> str:
    """Chép kho ra file có dấu thời gian bằng backup API (an toàn cả khi đang mở)."""
    dich = _ten_backup(thu_muc_backup)
    nguon = sqlite3.connect(path_kho); ra = sqlite3.connect(dich)
    with ra:
        nguon.backup(ra)
    nguon.close(); ra.close()
    return dich


def phuc_hoi(path_kho: str, path_nguon: str, thu_muc_backup: str) -> str:
    """Kiểm nguồn hợp lệ → sao lưu kho hiện tại → thay bằng nguồn. Trả đường dẫn backup."""
    mo_kho(path_nguon).close()                     # ném PhienBanMoiHon nếu nguồn mới hơn
    bk = sao_luu(path_kho, thu_muc_backup) if Path(path_kho).exists() else ""
    ra = sqlite3.connect(path_kho); ng = sqlite3.connect(path_nguon)
    with ra:
        ng.backup(ra)                              # ghi đè kho bằng nội dung nguồn
    ra.close(); ng.close()
    return bk


def nhap_gop(path_kho: str, path_nguon: str) -> dict:
    """Gộp snapshot chưa trùng từ nguồn vào kho; tính lại con_hieu_luc mỗi (kỳ,chi nhánh)."""
    dich = mo_kho(path_kho); ng = mo_kho(path_nguon)
    da_them = bo_qua = 0
    cham = set()
    try:
        with dich:
            for s in ng.execute("SELECT * FROM snapshot ORDER BY id"):
                trung = dich.execute(
                    "SELECT 1 FROM snapshot WHERE ky_nam=? AND ky_thang=? AND chi_nhanh=? "
                    "AND thoi_diem_chot=? AND van_tay=?",
                    (s["ky_nam"], s["ky_thang"], s["chi_nhanh"], s["thoi_diem_chot"], s["van_tay"])).fetchone()
                if trung:
                    bo_qua += 1; continue
                cur = dich.execute(
                    """INSERT INTO snapshot (ky_nam,ky_thang,chi_nhanh,thoi_diem_chot,ghi_chu,so_dong,
                         tong_ps,van_tay,ket_luan_ma,so_do,so_vang,so_chua_lam,so_can_ra,con_hieu_luc)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,0)""",
                    (s["ky_nam"], s["ky_thang"], s["chi_nhanh"], s["thoi_diem_chot"], s["ghi_chu"],
                     s["so_dong"], s["tong_ps"], s["van_tay"], s["ket_luan_ma"],
                     s["so_do"], s["so_vang"], s["so_chua_lam"], s["so_can_ra"]))
                moi = int(cur.lastrowid)
                for c in ng.execute("SELECT * FROM snapshot_check WHERE snapshot_id=?", (s["id"],)):
                    dich.execute("INSERT INTO snapshot_check (snapshot_id,ma,ten,muc_do,so_loi,la_thong_ke) VALUES (?,?,?,?,?,?)",
                                 (moi, c["ma"], c["ten"], c["muc_do"], c["so_loi"], c["la_thong_ke"]))
                d = ng.execute("SELECT du_lieu FROM snapshot_du_lieu WHERE snapshot_id=?", (s["id"],)).fetchone()
                if d:
                    dich.execute("INSERT INTO snapshot_du_lieu (snapshot_id,du_lieu) VALUES (?,?)", (moi, d[0]))
                da_them += 1
                cham.add((s["ky_nam"], s["ky_thang"], s["chi_nhanh"]))
            # Tính lại hiệu lực cho mỗi (kỳ,chi nhánh) bị chạm: bản thoi_diem_chot mới nhất = 1
            for ky_nam, ky_thang, cn in cham:
                dich.execute("UPDATE snapshot SET con_hieu_luc=0 WHERE ky_nam=? AND ky_thang=? AND chi_nhanh=?",
                             (ky_nam, ky_thang, cn))
                r = dich.execute(
                    "SELECT id FROM snapshot WHERE ky_nam=? AND ky_thang=? AND chi_nhanh=? "
                    "ORDER BY thoi_diem_chot DESC, id DESC LIMIT 1", (ky_nam, ky_thang, cn)).fetchone()
                if r:
                    dich.execute("UPDATE snapshot SET con_hieu_luc=1 WHERE id=?", (r["id"],))
    finally:
        dich.close(); ng.close()
    return {"da_them": da_them, "bo_qua_trung": bo_qua}
```

Cập nhật `app/kho/__init__.py` thêm: `from . import sao_luu  # noqa: F401`.

- [ ] **Step 4: Chạy — xác nhận xanh**

Run: `pytest tests/test_kho_sao_luu.py -v`
Expected: PASS 3 test.

- [ ] **Step 5: Commit**

```bash
git add app/kho/sao_luu.py app/kho/__init__.py tests/test_kho_sao_luu.py
git commit -m "feat(kho): sao luu / phuc hoi / nhap-gop kho SQLite"
```

---

### Task 7: Nối js_api — chốt/mở lại/đối chiếu/lịch sử/backup

**Files:**
- Modify: `app/api.py` (thêm import, thuộc tính kho, phương thức; bơm `chot` vào `_tom_tat`/`_danh_sach_don_vi`; đối chiếu trong `chay_kiem_tra`)
- Test: `tests/test_api_chot_so.py`

**Interfaces:**
- Consumes: `chot_so`, `app.kho.KhoChotSo`, `app.kho.sao_luu`, `tinh_ket_luan`, `checks.TEN_NHOM`.
- Produces (JsApi methods, tất cả trả `dict`):
  - `chot_so(ghi_chu="") -> dict` — chốt chi nhánh đang xem; trả `{"chot": {...}}` hoặc `{"loi":...}`.
  - `mo_lai_ky() -> dict`
  - `lich_su_chot(chi_nhanh=None) -> {"dong":[...]}`
  - `lay_diff_chot(trang=1, kich_thuoc=100, tim_kiem="") -> dict` (kiểu như `lay_chi_tiet`)
  - `sao_luu_kho() -> {"path":...}`, `phuc_hoi_kho(path) -> {...}`, `nhap_gop_kho(path) -> {...}`, `mo_thu_muc_kho() -> bool`
  - `_tom_tat`/`_danh_sach_don_vi` thêm khóa `chot` = `_trang_thai_chot(d)`.

- [ ] **Step 1: Viết test api chốt → đối chiếu**

```python
import pandas as pd
from app.api import JsApi
from app.loader import ThongTinFile
from app.checks.base import BoiCanh

def _api(tmp_path):
    api = JsApi(); api._thu_muc_kho = str(tmp_path)   # ép kho vào thư mục test
    return api

def _don_vi(df):
    from app.api import DonVi
    tt = ThongTinFile(path="x.xlsx", ten="x.xlsx", ky="08/2026", ky_thang=8, ky_nam=2026,
                      so_dong=len(df), tong_ps=float(df["Amount"].sum()), chi_nhanh="A01")
    return DonVi(df=df, tt=tt)

DF = pd.DataFrame([{"DocCode":"PX","DocNo":"1","DebitAccount":"621","CreditAccount":"1521","Amount":100.0}])

def test_chot_roi_bao_da_chot_va_khop(tmp_path):
    api = _api(tmp_path); d = _don_vi(DF); api._dv = [d]; api._i = 0
    api._chay_mot_don_vi(d)
    assert api.chot_so("lần 1")["chot"]["trang_thai"] == "DA_CHOT"
    # chạy lại kiểm tra: đối chiếu phải KHỚP
    tt = api._tom_tat()
    assert tt["tomtat"]["chot"]["doi_chieu"] == "KHOP"

def test_sua_du_lieu_thi_doi_chieu_lech(tmp_path):
    api = _api(tmp_path); d = _don_vi(DF); api._dv = [d]; api._i = 0
    api._chay_mot_don_vi(d); api.chot_so("")
    # đổi dữ liệu nguồn rồi chạy lại
    d.df = pd.concat([DF, pd.DataFrame([{"DocCode":"PX","DocNo":"2","DebitAccount":"621","CreditAccount":"1521","Amount":50.0}])], ignore_index=True)
    api._chay_mot_don_vi(d)
    tt = api._tom_tat()
    assert tt["tomtat"]["chot"]["doi_chieu"] == "LECH"
    assert tt["tomtat"]["chot"]["tom_tat_lech"]["delta_dong"] == 1
```

- [ ] **Step 2: Chạy — xác nhận đỏ**

Run: `pytest tests/test_api_chot_so.py -v`
Expected: FAIL (chưa có phương thức/`_thu_muc_kho`).

- [ ] **Step 3: Sửa `app/api.py`**

Thêm import (đầu file, cạnh import hiện có):

```python
from . import checks, chot_so, report
from .kho import KhoChotSo, sao_luu as kho_sao_luu
```

Thêm hằng thư mục (cạnh `THU_MUC_REPORT`):

```python
THU_MUC_CHOT = str(GOC / "3. Chot so")
```

Trong `JsApi.__init__`, thêm:

```python
        self._thu_muc_kho = THU_MUC_CHOT
```

Thêm helper mở kho (lazy, dùng chung một kết nối theo lần gọi để tránh khóa file):

```python
    def _kho(self) -> KhoChotSo:
        from pathlib import Path
        return KhoChotSo(str(Path(self._thu_muc_kho) / "kho_chot_so.sqlite"))

    def _duong_dan_kho(self) -> str:
        from pathlib import Path
        return str(Path(self._thu_muc_kho) / "kho_chot_so.sqlite")
```

Helper tính trạng thái chốt của một đơn vị (đọc kho + đối chiếu):

```python
    def _trang_thai_chot(self, d: "DonVi") -> dict:
        """Trạng thái chốt + đối chiếu cho một chi nhánh. Không có snapshot → CHUA_CHOT (im lặng)."""
        try:
            kho = self._kho()
        except Exception:  # noqa: BLE001 (kho lỗi không được làm chết màn kết quả)
            return {"trang_thai": "CHUA_CHOT", "doi_chieu": chot_so.CHUA_CHOT}
        try:
            h = kho.doc_hieu_luc(d.tt.ky_nam, d.tt.ky_thang, d.nhan)
            if h is None:
                return {"trang_thai": "CHUA_CHOT", "doi_chieu": chot_so.CHUA_CHOT}
            vt = chot_so.VanTay(h["so_dong"], h["tong_ps"], h["van_tay"])
            df_chot = kho.doc_du_lieu(h["id"])
            kq = chot_so.doi_chieu(vt, d.df, df_chot=df_chot)
            return {"trang_thai": "DA_CHOT", "ngay_chot": h["thoi_diem_chot"], "ghi_chu": h["ghi_chu"],
                    "ket_luan_ma": h["ket_luan_ma"], "doi_chieu": kq.trang_thai,
                    "tom_tat_lech": {"delta_dong": kq.delta_dong, "delta_ps": kq.delta_ps,
                                     "so_ct_anh_huong": kq.so_ct_anh_huong}}
        finally:
            kho.dong()
```

Bơm `chot` vào `_tom_tat` (trong `return {... "tomtat": {..., **ket_luan}}`) — thêm khóa `chot` vào dict `tomtat`:

```python
        tomtat = {"ky": t.ky, "ten": t.ten, "so_dong": t.so_dong, "tong_ps": t.tong_ps,
                  "chi_nhanh": self._hien.nhan, **ket_luan,
                  "chot": self._trang_thai_chot(self._hien)}
        return {"tomtat": tomtat, ...}   # phần còn lại giữ nguyên
```

Và vào `_danh_sach_don_vi` (mỗi phần tử thêm `"chot"`):

```python
            ds.append({"i": i, "ma": d.nhan, ..., **kl,
                       "chot": self._trang_thai_chot(d) if d.ket_qua else {"trang_thai": "CHUA_CHOT"}})
```

Thêm các phương thức công khai (cuối lớp, cạnh `xuat_bao_cao`):

```python
    def _dem_ket_luan(self, kl: dict) -> dict:
        return {k: kl.get(k, 0) for k in ("so_do", "so_vang", "so_chua_lam", "so_can_ra")}

    def chot_so(self, ghi_chu: str = ""):
        d = self._hien
        if d is None or not d.ket_qua:
            return {"loi": "Chưa chạy kiểm tra cho chi nhánh này"}
        try:
            vt = chot_so.van_tay(d.df)
            kl = tinh_ket_luan(d.ket_qua, d.trang_thai)
            checks_ = [{"ma": r.ma, "ten": r.ten, "muc_do": r.muc_do_thuc,
                        "so_loi": r.so_loi, "la_thong_ke": r.la_thong_ke} for r in d.ket_qua]
            kho = self._kho()
            try:
                kho.luu_snapshot(ky_nam=d.tt.ky_nam, ky_thang=d.tt.ky_thang, chi_nhanh=d.nhan,
                                 van_tay_hash=vt.ma_bam, so_dong=vt.so_dong, tong_ps=vt.tong_ps,
                                 ket_luan_ma=kl["muc_do_ket_luan"], dem=self._dem_ket_luan(kl),
                                 checks=checks_, df=d.df, ghi_chu=ghi_chu)
            finally:
                kho.dong()
            return {"chot": self._trang_thai_chot(d)}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không chốt được kỳ: {e}"}

    def mo_lai_ky(self):
        d = self._hien
        if d is None:
            return {"loi": "Chưa có chi nhánh đang xem"}
        try:
            kho = self._kho()
            try:
                kho.mo_lai(d.tt.ky_nam, d.tt.ky_thang, d.nhan)
            finally:
                kho.dong()
            return {"chot": self._trang_thai_chot(d)}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không mở lại được kỳ: {e}"}

    def lich_su_chot(self, chi_nhanh=None):
        try:
            kho = self._kho()
            try:
                dong = kho.liet_ke(chi_nhanh=chi_nhanh)
            finally:
                kho.dong()
            return {"dong": dong}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không đọc được lịch sử chốt: {e}"}

    def lay_diff_chot(self, trang: int = 1, kich_thuoc: int = 100, tim_kiem: str = ""):
        d = self._hien
        if d is None or not d.ket_qua:
            return {"loi": "Chưa chạy kiểm tra"}
        try:
            kho = self._kho()
            try:
                h = kho.doc_hieu_luc(d.tt.ky_nam, d.tt.ky_thang, d.nhan)
                if h is None:
                    return {"loi": "Kỳ này chưa chốt"}
                df_chot = kho.doc_du_lieu(h["id"])
            finally:
                kho.dong()
            diff = chot_so.dien_diff(df_chot, d.df)
            them = _dinh_dang_ngay(diff["them"]).assign(**{"Thay đổi": "＋ Thêm"})
            bot = _dinh_dang_ngay(diff["bot"]).assign(**{"Thay đổi": "－ Bớt"})
            df = pd.concat([them, bot], ignore_index=True) if len(them) or len(bot) else them
            if tim_kiem:
                tk = tim_kiem.lower()
                df = df[df.astype(str).apply(lambda s: s.str.lower().str.contains(tk, regex=False)).any(axis=1)]
            tong = int(len(df)); kich_thuoc = max(1, min(int(kich_thuoc), 500))
            a = max(0, (int(trang) - 1) * kich_thuoc); cot = list(df.columns)
            return {"tong": tong, "trang": int(trang), "cot": cot, "nhan": ten_cot(cot),
                    "tom_tat": diff["tom_tat"],
                    "dong": json.loads(df.iloc[a:a + kich_thuoc].to_json(orient="records", force_ascii=False))}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không lấy được thay đổi: {e}"}

    def sao_luu_kho(self):
        try:
            from pathlib import Path
            p = kho_sao_luu.sao_luu(self._duong_dan_kho(), str(Path(self._thu_muc_kho) / "backup"))
            return {"path": p}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không sao lưu được kho: {e}"}

    def phuc_hoi_kho(self, path: str):
        try:
            from pathlib import Path
            bk = kho_sao_luu.phuc_hoi(self._duong_dan_kho(), path, str(Path(self._thu_muc_kho) / "backup"))
            return {"da_sao_luu": bk}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không phục hồi được kho: {e}"}

    def nhap_gop_kho(self, path: str):
        try:
            return kho_sao_luu.nhap_gop(self._duong_dan_kho(), path)
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không nhập/gộp được kho: {e}"}

    def mo_thu_muc_kho(self):
        return self.mo_thu_muc(self._thu_muc_kho)
```

(`ten_cot` đã được import sẵn ở đầu `api.py`; `json`, `pd`, `_dinh_dang_ngay`, `tinh_ket_luan` cũng vậy.)

- [ ] **Step 4: Chạy test api + toàn bộ suite**

Run: `pytest tests/test_api_chot_so.py -v`
Expected: PASS.
Run: `pytest -W error`
Expected: PASS toàn bộ (259 cũ + mới). Nếu `_danh_sach_don_vi`/`_tom_tat` test cũ so khớp dict cứng, nới chúng để chấp nhận khóa `chot` mới.

- [ ] **Step 5: Commit**

```bash
git add app/api.py tests/test_api_chot_so.py
git commit -m "feat(api): chot/mo lai/lich su/diff + doi chieu drift + backup kho"
```

---

### Task 8: UI — badge chốt + khối "Chốt sổ" + modal xác nhận

**Files:**
- Modify: `app/web/app.js` (thanh chi nhánh `veThanhDonVi`; khối chốt trong chi tiết; modal), `app/web/index.html` (khung modal), `app/web/style.css` (badge, khối, modal) — *đường dẫn thực tế xác nhận ở Step 1*.

**Interfaces:**
- Consumes: `tomtat.chot`, `don_vi[i].chot` (Task 7); gọi `pywebview.api.chot_so(ghi_chu)`, `mo_lai_ky()`.

- [ ] **Step 1: Xác định file frontend**

Run: `git ls-files app | grep -Ei "\.(js|html|css)$"`
Ghi lại đường dẫn thực (giả định `app/web/app.js`, `index.html`, `style.css`). Dùng đúng đường dẫn đó ở các step sau.

- [ ] **Step 2: Badge chốt trên thẻ chi nhánh**

Trong `veThanhDonVi` (nơi dựng mỗi thẻ chi nhánh), thêm nhãn theo `dv.chot`:

```js
function nhanChot(chot) {
  if (!chot || chot.trang_thai !== 'DA_CHOT')
    return '<span class="chip-chot chua">Chưa chốt</span>';
  if (chot.doi_chieu === 'LECH')
    return '<span class="chip-chot lech">⚠ Dữ liệu đã đổi</span>';
  const ngay = (chot.ngay_chot || '').slice(8, 10) + '/' + (chot.ngay_chot || '').slice(5, 7);
  return `<span class="chip-chot khop">🔒 Đã chốt ${ngay}</span>`;
}
```

Chèn `nhanChot(dv.chot)` vào HTML mỗi thẻ.

- [ ] **Step 3: Khối "Chốt sổ" trong chi tiết chi nhánh**

Dưới banner kết luận, thêm vùng dựng từ `tomtat.chot`:

```js
function veKhoiChot(chot) {
  if (chot && chot.trang_thai === 'DA_CHOT') {
    const canhBao = chot.doi_chieu === 'LECH'
      ? '<div class="chot-lech">Dữ liệu nguồn đã khác bản đã chốt</div>' : '';
    return `<div class="khoi-chot da-chot">
      <div>🔒 <b>Đã chốt</b> ${chot.ngay_chot || ''} ${chot.ghi_chu ? '· ' + chot.ghi_chu : ''}</div>
      ${canhBao}
      <div class="hang-nut">
        <button class="btn-phu" onclick="moLaiKy()">Mở lại kỳ</button>
        <button class="btn-phu" onclick="moModalChot(true)">Chốt lại</button>
      </div></div>`;
  }
  return `<div class="khoi-chot">
    <button class="btn-chinh" onclick="moModalChot(false)">🔒 Chốt sổ kỳ này</button></div>`;
}
```

- [ ] **Step 4: Modal xác nhận chốt**

Thêm khung modal vào `index.html` (ẩn mặc định), điền số liệu từ `tomtat`:

```html
<div id="modalChot" class="modal an">
  <div class="modal-hop">
    <h3 id="modalChotTieuDe">Chốt sổ kỳ này</h3>
    <div id="modalChotThongTin" class="modal-tt"></div>
    <label>Ghi chú (tùy chọn)</label>
    <input id="modalChotGhiChu" type="text" placeholder="VD: Đã đối chiếu sổ phụ ngân hàng"/>
    <div class="hang-nut">
      <button class="btn-phu" onclick="dongModalChot()">Hủy</button>
      <button class="btn-chinh" onclick="xacNhanChot()">Chốt sổ</button>
    </div>
  </div></div>
```

JS điều khiển modal + gọi API:

```js
function moModalChot(chotLai) {
  const t = window._tomtat || {};
  document.getElementById('modalChotThongTin').innerHTML =
    `Kỳ <b>${t.ky}</b> · Chi nhánh <b>${t.chi_nhanh}</b><br/>` +
    `Số dòng: <b>${(t.so_dong||0).toLocaleString('vi-VN')}</b> · ` +
    `Tổng PS: <b>${Math.round(t.tong_ps||0).toLocaleString('vi-VN')}</b><br/>` +
    `Kết luận: <b>${t.cau_ket_luan||''}</b>`;
  document.getElementById('modalChot').classList.remove('an');
}
function dongModalChot(){ document.getElementById('modalChot').classList.add('an'); }
async function xacNhanChot() {
  const gc = document.getElementById('modalChotGhiChu').value || '';
  const kq = await pywebview.api.chot_so(gc);
  dongModalChot();
  if (kq.loi) return baoLoi(kq.loi);
  await chayLaiHienThi();   // dựng lại màn kết quả để badge/khối cập nhật
}
async function moLaiKy() {
  if (!confirm('Mở lại kỳ này? Bản đã chốt vẫn được giữ trong lịch sử.')) return;
  const kq = await pywebview.api.mo_lai_ky();
  if (kq.loi) return baoLoi(kq.loi);
  await chayLaiHienThi();
}
```

(Dùng lại hàm dựng màn kết quả hiện có; đặt tên `chayLaiHienThi`/`baoLoi` khớp hàm sẵn có trong app.js — xác nhận ở Step 1.)

- [ ] **Step 5: CSS badge + khối + modal (hệ Premium Light)**

Thêm vào `style.css`:

```css
.chip-chot{font-size:12px;padding:2px 8px;border-radius:999px;margin-left:6px}
.chip-chot.chua{background:#f1f5f9;color:#64748b;border:1px solid #e2e8f0}
.chip-chot.khop{background:#ecfdf5;color:#047857;border:1px solid #a7f3d0}
.chip-chot.lech{background:#fff7ed;color:#c2410c;border:1px solid #fed7aa}
.khoi-chot{margin:12px 0;padding:14px 16px;border-radius:14px;background:#f8fafc;box-shadow:0 1px 2px rgba(2,6,23,.06)}
.khoi-chot.da-chot{background:#ecfdf5}
.chot-lech{margin-top:6px;color:#c2410c;font-weight:600}
.btn-chinh{background:#1E40AF;color:#fff;border:0;border-radius:10px;padding:9px 16px;font-weight:600;cursor:pointer}
.btn-phu{background:#fff;color:#1E40AF;border:1px solid #c7d2fe;border-radius:10px;padding:8px 14px;cursor:pointer}
.hang-nut{display:flex;gap:10px;margin-top:10px}
.modal{position:fixed;inset:0;background:rgba(15,23,42,.45);display:flex;align-items:center;justify-content:center;z-index:50}
.modal.an{display:none}
.modal-hop{background:#fff;border-radius:18px;padding:22px;min-width:380px;max-width:90vw;box-shadow:0 20px 50px rgba(2,6,23,.25)}
.modal-tt{margin:8px 0 14px;line-height:1.6;color:#334155}
.modal input{width:100%;padding:9px 12px;border:1px solid #e2e8f0;border-radius:10px;margin:6px 0 4px}
```

- [ ] **Step 6: Chạy app & kiểm tra thủ công qua preview**

Dùng `preview_start`/pywebview theo lối dự án; nạp một file mẫu, bấm **Chốt sổ kỳ này** → xác nhận badge chuyển "🔒 Đã chốt", khối đổi sang trạng thái đã chốt. Kiểm `read_console_messages` không lỗi.

- [ ] **Step 7: Commit**

```bash
git add app/web
git commit -m "feat(ui): badge chot + khoi chot so + modal xac nhan (Premium Light)"
```

---

### Task 9: UI — banner drift + "Xem thay đổi" + "Cập nhật & chốt lại"

**Files:**
- Modify: `app/web/app.js`, `app/web/index.html`, `app/web/style.css`

**Interfaces:**
- Consumes: `tomtat.chot.doi_chieu`, `tomtat.chot.tom_tat_lech`; gọi `pywebview.api.lay_diff_chot(...)`, `chot_so(...)`.

- [ ] **Step 1: Banner drift trên đầu vùng kết quả**

```js
function veBannerDrift(chot) {
  if (!chot || chot.trang_thai !== 'DA_CHOT') return '';
  if (chot.doi_chieu === 'KHOP')
    return `<div class="dai-khop">✓ Dữ liệu khớp bản đã chốt ${chot.ngay_chot||''}</div>`;
  const t = chot.tom_tat_lech || {};
  return `<div class="banner-lech">
    <div><b>⚠ Kỳ đã chốt nhưng dữ liệu nguồn đã thay đổi</b></div>
    <div>Δ dòng: ${t.delta_dong>0?'+':''}${t.delta_dong||0} ·
         Δ tổng PS: ${Math.round(t.delta_ps||0).toLocaleString('vi-VN')} ·
         ${t.so_ct_anh_huong||0} chứng từ ảnh hưởng</div>
    <div class="hang-nut">
      <button class="btn-phu" onclick="moModalDiff()">Xem thay đổi</button>
      <button class="btn-chinh" onclick="capNhatChotLai()">Cập nhật & chốt lại</button>
    </div></div>`;
}
```

- [ ] **Step 2: Modal "Xem thay đổi" (bảng thêm/bớt, tìm kiếm, phân trang)**

Thêm khung `#modalDiff` vào `index.html` (giống bảng chi tiết lỗi hiện có). JS nạp trang:

```js
let _diffTrang = 1;
async function moModalDiff(){ _diffTrang = 1; document.getElementById('modalDiff').classList.remove('an'); await taiDiff(); }
function dongModalDiff(){ document.getElementById('modalDiff').classList.add('an'); }
async function taiDiff() {
  const tk = document.getElementById('diffTimKiem').value || '';
  const kq = await pywebview.api.lay_diff_chot(_diffTrang, 100, tk);
  if (kq.loi) return baoLoi(kq.loi);
  // dựng bảng từ kq.cot/kq.nhan/kq.dong — DÙNG LẠI hàm vẽ bảng chi tiết sẵn có
  veBangChiTiet('#diffBang', kq);
  document.getElementById('diffTomTat').textContent =
    `Thêm ${kq.tom_tat.so_them} · Bớt ${kq.tom_tat.so_bot} · ${kq.tom_tat.so_ct_anh_huong} chứng từ`;
}
```

- [ ] **Step 3: "Cập nhật & chốt lại"**

```js
async function capNhatChotLai() {
  if (!confirm('Đóng băng dữ liệu MỚI làm bản chốt hiện hành? Bản cũ vẫn được giữ trong lịch sử.')) return;
  const kq = await pywebview.api.chot_so('Cập nhật dữ liệu mới');
  if (kq.loi) return baoLoi(kq.loi);
  await chayLaiHienThi();
}
```

- [ ] **Step 4: CSS banner/diff**

```css
.banner-lech{margin:12px 0;padding:14px 16px;border-radius:14px;background:#fff7ed;border:1px solid #fed7aa;color:#9a3412}
.dai-khop{margin:12px 0;padding:8px 14px;border-radius:12px;background:#ecfdf5;color:#047857;font-size:13px}
#modalDiff .modal-hop{min-width:70vw}
#diffTomTat{margin:6px 0;color:#9a3412;font-weight:600}
```

- [ ] **Step 5: Kiểm tra thủ công**

Chốt một kỳ → sửa file nguồn (thêm/bớt dòng) → chạy lại: banner cam hiện đúng Δ; "Xem thay đổi" liệt kê dòng thêm/bớt; "Cập nhật & chốt lại" đưa về trạng thái khớp. `read_console_messages` sạch.

- [ ] **Step 6: Commit**

```bash
git add app/web
git commit -m "feat(ui): banner drift + xem thay doi + cap nhat & chot lai"
```

---

### Task 10: UI — tab "Lịch sử chốt sổ" + thanh công cụ kho

**Files:**
- Modify: `app/web/app.js`, `app/web/index.html`, `app/web/style.css`

**Interfaces:**
- Consumes: `pywebview.api.lich_su_chot()`, `sao_luu_kho()`, `phuc_hoi_kho(path)`, `nhap_gop_kho(path)`, `mo_thu_muc_kho()`, và `chon_file`-style để chọn `.sqlite` (thêm `chon_file_sqlite` nếu cần, hoặc tái dùng `create_file_dialog`).

- [ ] **Step 1: Nút mở tab & bảng lịch sử**

Thêm nút "Lịch sử chốt sổ" trên header. Khi mở, gọi `lich_su_chot()` và dựng bảng: kỳ · chi nhánh · ngày chốt · kết luận · hiệu lực. Dòng `con_hieu_luc=0` thêm class mờ.

```js
async function moLichSu() {
  const kq = await pywebview.api.lich_su_chot();
  if (kq.loi) return baoLoi(kq.loi);
  const rows = kq.dong.map(r => `<tr class="${r.con_hieu_luc? '':'het-hieu-luc'}">
     <td>${String(r.ky_thang).padStart(2,'0')}/${r.ky_nam}</td><td>${r.chi_nhanh}</td>
     <td>${r.thoi_diem_chot}</td><td>${r.ket_luan_ma}</td>
     <td>${r.con_hieu_luc? 'Hiệu lực':'Đã thay'}</td>
     <td>${r.ghi_chu||''}</td></tr>`).join('');
  document.getElementById('lichSuBody').innerHTML = rows ||
     '<tr><td colspan="6">Chưa có kỳ nào được chốt.</td></tr>';
  document.getElementById('manLichSu').classList.remove('an');
}
```

- [ ] **Step 2: Thanh công cụ kho (backup/restore/import/mở thư mục)**

Trên đầu tab lịch sử:

```html
<div class="hang-nut">
  <button class="btn-phu" onclick="saoLuuKho()">Sao lưu kho</button>
  <button class="btn-phu" onclick="phucHoiKho()">Phục hồi từ file…</button>
  <button class="btn-phu" onclick="nhapGopKho()">Nhập & gộp từ file…</button>
  <button class="btn-phu" onclick="pywebview.api.mo_thu_muc_kho()">Mở thư mục kho</button>
</div>
```

```js
async function saoLuuKho(){ const k=await pywebview.api.sao_luu_kho(); alert(k.loi||('Đã sao lưu: '+k.path)); }
async function phucHoiKho(){
  const f = await pywebview.api.chon_file_sqlite();
  if(!f || f.huy) return;
  if(!confirm('Phục hồi sẽ THAY kho hiện tại (đã tự sao lưu bản cũ). Tiếp tục?')) return;
  const k = await pywebview.api.phuc_hoi_kho(f.path); alert(k.loi||('Đã phục hồi. Backup: '+k.da_sao_luu)); await moLichSu();
}
async function nhapGopKho(){
  const f = await pywebview.api.chon_file_sqlite();
  if(!f || f.huy) return;
  const k = await pywebview.api.nhap_gop_kho(f.path);
  alert(k.loi||(`Đã thêm ${k.da_them} bản, bỏ qua ${k.bo_qua_trung} bản trùng.`)); await moLichSu();
}
```

Thêm `chon_file_sqlite` vào `api.py` (tương tự `chon_file`, `file_types=("SQLite (*.sqlite;*.db)",)`, trả `{"path":...}` hoặc `{"huy":True}`):

```python
    def chon_file_sqlite(self):
        if self._window is None:
            return {"loi": "Chưa có cửa sổ"}
        try:
            import webview
            loai = getattr(getattr(webview, "FileDialog", None), "OPEN", None) or webview.OPEN_DIALOG
            chon = self._window.create_file_dialog(loai, directory=self._thu_muc_kho,
                                                   file_types=("SQLite (*.sqlite;*.db)",))
            return {"path": chon[0]} if chon else {"huy": True}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không mở được hộp thoại: {e}"}
```

- [ ] **Step 3: CSS tab lịch sử**

```css
.het-hieu-luc{opacity:.5}
#manLichSu table{width:100%;border-collapse:collapse}
#manLichSu td,#manLichSu th{padding:8px 10px;border-bottom:1px solid #eef2f7;text-align:left}
```

- [ ] **Step 4: Kiểm tra thủ công**

Mở tab lịch sử: thấy các kỳ đã chốt; bản đã thay hiển thị mờ. Bấm **Sao lưu kho** → báo đường dẫn; kiểm file backup xuất hiện trong `3. Chot so/backup`. Thử **Nhập & gộp** từ một file `.sqlite` khác → báo số bản thêm/trùng.

- [ ] **Step 5: Commit**

```bash
git add app/web app/api.py
git commit -m "feat(ui): tab lich su chot so + thanh cong cu sao luu/phuc hoi/nhap kho"
```

---

### Task 11: Git-ignore kho + nhật ký thực thi

**Files:**
- Modify: `.gitignore`
- Create: `docs/ket-qua/them-kho-chot-so.md`

- [ ] **Step 1: Bỏ qua thư mục kho khỏi git**

Thêm vào `.gitignore`:

```
# Kho chốt sổ — dữ liệu kế toán, không commit
3. Chot so/
```

- [ ] **Step 2: Xác nhận không có file kho nào bị theo dõi**

Run: `git status --porcelain "3. Chot so/"`
Expected: rỗng (không có gì được stage).

- [ ] **Step 3: Ghi nhật ký đợt**

Tạo `docs/ket-qua/them-kho-chot-so.md`: tóm tắt tính năng (kho SQLite append-only, đối chiếu drift, UI chốt/xem thay đổi/lịch sử, backup/restore/merge), các quyết định (BLOB nén thay bảng cột, băm cả dòng để diff, C7.5 hạ cấp), và điểm còn để lại (diff mức từng ô — stretch).

- [ ] **Step 4: Chạy lại toàn bộ test**

Run: `pytest -W error`
Expected: PASS toàn bộ.

- [ ] **Step 5: Commit**

```bash
git add .gitignore docs/ket-qua/them-kho-chot-so.md
git commit -m "chore: git-ignore kho chot so + nhat ky thuc thi"
```

---

## Self-Review

**Spec coverage:**
- §2 quyết định 1–9 → Task 1 (C7.5), 2–3 (vân tay/đối chiếu), 4–6 (kho + append-only + backup), 7 (api), 8–10 (UI, lịch sử). ✔
- §3 kiến trúc `app/kho/` + `chot_so.py` → Task 2–7. ✔
- §4 schema (snapshot/snapshot_check/snapshot_du_lieu/schema_version) → Task 4–5. ✔
- §5 đối chiếu & diff → Task 3, 7, 9. ✔
- §6 UI (badge, khối chốt, modal, banner drift, xem thay đổi, tab lịch sử) → Task 8–10. ✔
- §7 sao lưu/phục hồi/nhập → Task 6, 10. ✔
- §8 API → Task 7, 10. ✔
- §9 C7.5 → Task 1. ✔
- §10 test → mỗi task có test (UI kiểm thủ công). ✔

**Placeholder scan:** không có TODO/TBD; mọi step code có nội dung thật. UI step ghi rõ "dùng lại hàm sẵn có" + xác nhận tên ở Task 8 Step 1 (không phải placeholder mà là ràng buộc khớp code hiện hữu).

**Type consistency:** `VanTay(so_dong, tong_ps, ma_bam)` dùng nhất quán; `doi_chieu`/`dien_diff` trả đúng kiểu Task 3 định nghĩa và Task 7 tiêu thụ; `KhoChotSo.luu_snapshot(**kwargs)` khớp giữa Task 5 (định nghĩa), Task 6 (test) và Task 7 (gọi); hằng `KHOP/LECH/CHUA_CHOT` dùng chung.

**Rủi ro cần lưu ý khi thực thi:**
- Đường dẫn frontend (`app/web/*`) là **giả định** — Task 8 Step 1 bắt buộc xác nhận trước.
- Test cũ so khớp `_tom_tat`/`_danh_sach_don_vi` bằng dict cứng có thể đỏ khi thêm khóa `chot` → nới ở Task 7 Step 4.
- `pd.read_json` cần bọc chuỗi bằng `io.StringIO` (đã làm) để tránh FutureWarning thành lỗi dưới `-W error`.
