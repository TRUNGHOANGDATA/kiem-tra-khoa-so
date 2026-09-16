# Nâng cấp: Bút toán phân bổ & trích lập cuối kỳ (Nhóm 7) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development để thực thi plan này theo từng task. Các bước dùng checkbox (`- [ ]`).

**Goal:** Bổ sung nhóm kiểm tra các bút toán cuối kỳ *hay quên* (khấu hao, phân bổ 242, trích lương, thuế TNDN, đánh giá tỷ giá, dự phòng) và đưa chúng thành các bước trong "11 bước khóa sổ" — nâng lên 16 bước, **mà không phá kết luận "SẴN SÀNG KHÓA SỔ"**.

**Architecture:** Thêm `app/checks/g7_phan_bo_trich_lap.py` theo khuôn mẫu G1–G6. Thêm một **trạng thái bước mới** `TU_XAC_NHAN` cho Tab A. Không đổi mô hình dữ liệu, không thêm nguồn dữ liệu, không thêm dependency.

**Tech Stack:** Python 3.14, pandas 3.0, pytest (`-W error`).

**Spec:** `docs/spec/2026-09-15-tool-kiem-tra-khoa-so-design.md` (§7 Nhóm 7, §5 bảng 16 bước).

---

## ⚠️ Kết quả spike — bản plan trước SAI ở đâu

Plan v1 đã được **dựng thử và chạy full suite** ngày 16/09. Kết quả: **8 test đỏ**. Bản này sửa cả nguyên nhân gốc lẫn các đầu việc bị bỏ sót.

### Lỗi thiết kế (nghiêm trọng — không phải lỗi đếm)

Plan v1 cho C7.1/C7.2/C7.3 mức **🟡 VANG**. Nhưng `tinh_ket_luan` gộp mọi check vàng vào kết luận, nên **một bộ sổ sạch hoàn toàn cũng không bao giờ đạt "SẴN SÀNG KHÓA SỔ" nữa**:

```
test_ket_luan.py::test_san_sang_khi_khong_con_gi
  mong đợi: "SẴN SÀNG KHÓA SỔ"
  thực tế : "CÒN 3 MỤC CẦN RÀ SOÁT  ·  🔴 0  🟡 3"
```

Kịch bản `SAN_SANG` chỉ là một bút toán `Nợ 1111 / Có 1121` — không có 214/242/334 nên cả ba check "nhắc" đều bắn. Đây **đúng là bẫy dương-tính-giả của C4.1 tái diễn dưới dạng khác**: khẳng định dựa trên *sự vắng mặt của bằng chứng*. Tệ hơn C4.1 ở chỗ nó làm hỏng **băng kết luận** — thứ giá trị nhất trên màn hình.

**Cách sửa (quyết định thiết kế của bản này):** tách Nhóm 7 làm hai loại theo **sức mạnh bằng chứng**:

| Loại | Check | Cơ chế | Ảnh hưởng kết luận |
|------|-------|--------|--------------------|
| **📋 Checklist** — chỉ biết "kỳ này không thấy", không biết DN có hay không | C7.1, C7.2, C7.3, C7.4, C7.7 | `la_thong_ke=True` | **Không** — `tinh_ket_luan` đã lọc `if not r.la_thong_ke` |
| **🟡 Cảnh báo thật** — có bằng chứng đối ứng ngay trong file | C7.5, C7.6 | `VANG` bình thường | Có |

Checklist vẫn **hiện đủ** ở Tab A (trạng thái mới `TU_XAC_NHAN`) và Tab B (thẻ Nhóm 7), bấm vào vẫn đọc được dòng giải thích — chỉ là không tự ý hạ kết luận thay kế toán.

### Đầu việc plan v1 bỏ sót

| Nơi | Vấn đề |
|-----|--------|
| `tests/test_api.py:33` | `len(trang_thai) == 11 and len(nhom) == 6` — v1 không nhắc |
| `tests/test_e2e_file_that.py:25` | `len(trang_thai) == 11` — v1 không nhắc |
| `tests/test_du_lieu_bien.py:16` | `len(ds) == 11` (số bước) — v1 chỉ nhắc dòng 14 (số check) |
| `tests/test_trang_thai.py:131` | ngoài `len == 11` còn `ds[0].buoc.startswith("Tập hợp CP NVL")` — đổi bước đầu sẽ vỡ |
| `tests/test_trang_thai.py` `test_kich_ban_phu_du_bon_trang_thai` | khẳng định tập trạng thái **đúng bằng 4**; thêm `TU_XAC_NHAN` là 5 |
| `tests/test_trang_thai.py` `test_thieu_ket_qua_kiem_tra_thi_khong_ap_dung` | gọi `suy_trang_thai(df, {})` — v1 đọc `ket_qua[ma]` sẽ **KeyError** |
| `app/report.py` | `TEN_TRANG_THAI[b.trang_thai]` và `fmt[b.trang_thai]` — **KeyError** với trạng thái mới |
| `app/web/app.js` | `khoaTT()` khoá giá trị lạ về `khong_ap_dung` → bước mới hiển thị sai nhãn |

### Đã kiểm và **không** phải vấn đề

- `pd.DataFrame([], columns=["ket_luan"])` và bản 1 dòng — chạy sạch dưới `-W error`.
- `TEN_COT["ket_luan"] = "Kết luận"` **đã có sẵn** (thêm ở nhánh nhiều chi nhánh).
- ⚠️ Nhưng `TEN_COT` **chưa có `co_phat_sinh`** — cột mới của bảng checklist. Thiếu nhãn này thì `test_moi_cot_cac_check_sinh_ra_deu_co_nhan_tieng_viet` đỏ ngay (nó quét mọi cột của mọi check). Đã đưa vào Task 1 Step 4.
- `phat_sinh_theo_prefix` / `co_dong` trên frame rỗng trả `(0.0, 0.0)` / `False` — an toàn.
- Bất biến **D1** (`test_buoc_can_xu_ly_luon_tro_toi_bang_chung_co_that`) vẫn giữ: chỉ soi `CHUA_LAM`/`CAN_RA`; `TU_XAC_NHAN` được miễn, còn C7.5/C7.6 khi bắn đều sinh đúng 1 dòng chứng minh.

---

## Global Constraints

- **Chỉ dùng phát sinh trong kỳ** — không số dư đầu kỳ, không so nhiều kỳ.
- **So khớp ở tài khoản CẤP 1** — prefix 3 chữ số (`214`, `242`, `334`, `338`, `335`, `821`, `413`, `229`).
- **Không khẳng định dựa trên sự vắng mặt của bằng chứng.** Không có bằng chứng đối ứng trong file → `la_thong_ke=True` (checklist), **không** được là 🟡/🔴.
- **Kết luận "SẴN SÀNG KHÓA SỔ" phải còn đạt được** với một bộ sổ sạch. `test_ket_luan.py` là hàng rào — không sửa nó để hợp thức hoá.
- **Trạng thái bước phải đọc từ chính check được trích dẫn**, và phải chịu được `ket_qua` rỗng (`.get()` → `KHONG_AP_DUNG`).
- Chạy được dưới `pytest -W error`; G7 nhận `df` của một `DonVi` như mọi nhóm khác.

---

### Task 1: Khung G7 + C7.1–C7.3 (checklist)

**Files:**
- Create: `app/checks/g7_phan_bo_trich_lap.py`
- Modify: `app/checks/__init__.py`
- Test: `tests/test_g7_phan_bo_trich_lap.py`

**Interfaces:**
- Consumes: `base.VANG`, `base.BoiCanh`, `base.CheckResult`, `base.co_dong`, `base.phat_sinh_theo_prefix`.
- Produces: `NHOM = "G7"`, `TK_CHI_PHI`, `kiem_tra(df, ctx) -> list[CheckResult]`.

- [ ] **Step 1: Viết test thất bại**

```python
# tests/test_g7_phan_bo_trich_lap.py
from app.checks import g7_phan_bo_trich_lap as g7
from tests.conftest import tao_df

def _kq(df, ctx): return {r.ma: r for r in g7.kiem_tra(df, ctx)}

def test_c71_c72_c73_la_checklist_khong_doi_ket_luan(ctx):
    """Bài học C4.1: không được khẳng định dựa trên sự vắng mặt của bằng chứng.
    Sổ sạch không có 214/242/334 vẫn phải đạt SẴN SÀNG -> ba check này la_thong_ke."""
    df = tao_df([{"DebitAccount": "1111", "CreditAccount": "1121", "Amount": 100}])
    kq = _kq(df, ctx)
    for ma in ("C7.1", "C7.2", "C7.3"):
        assert kq[ma].la_thong_ke, ma
        assert kq[ma].so_loi == 0 and kq[ma].muc_do_thuc == "xanh", ma
        assert len(kq[ma].chi_tiet) == 1        # vẫn có dòng để kế toán đọc

def test_c71_noi_ro_co_hay_khong_thay_khau_hao(ctx):
    thieu = _kq(tao_df([{"DebitAccount": "6421", "CreditAccount": "1111"}]), ctx)["C7.1"]
    du = _kq(tao_df([{"DebitAccount": "6274", "CreditAccount": "2141"}]), ctx)["C7.1"]
    assert thieu.chi_tiet.iloc[0]["co_phat_sinh"] is False
    assert du.chi_tiet.iloc[0]["co_phat_sinh"] is True

def test_c73_luong_vao_chi_phi(ctx):
    du = _kq(tao_df([{"DebitAccount": "6221", "CreditAccount": "3341"}]), ctx)["C7.3"]
    du338 = _kq(tao_df([{"DebitAccount": "6271", "CreditAccount": "3383"}]), ctx)["C7.3"]
    thieu = _kq(tao_df([{"DebitAccount": "6421", "CreditAccount": "1111"}]), ctx)["C7.3"]
    assert du.chi_tiet.iloc[0]["co_phat_sinh"] is True
    assert du338.chi_tiet.iloc[0]["co_phat_sinh"] is True
    assert thieu.chi_tiet.iloc[0]["co_phat_sinh"] is False
```

- [ ] **Step 2: Chạy — FAIL** (`ModuleNotFoundError`).

- [ ] **Step 3: Viết module**

```python
# app/checks/g7_phan_bo_trich_lap.py
"""Nhóm 7 — Bút toán phân bổ & trích lập cuối kỳ (nhóm hay quên nhất).

Chỉ dùng phát sinh TRONG KỲ, so khớp ở TÀI KHOẢN CẤP 1.

Vì sao phần lớn nhóm này là CHECKLIST (la_thong_ke) chứ không phải cảnh báo:
không có số dư đầu kỳ nên tool chỉ biết "kỳ này không thấy bút toán", KHÔNG biết
DN có TSCĐ / khoản trả trước / lao động hay không. Biến "không thấy" thành cảnh
báo vàng là khẳng định dựa trên sự vắng mặt của bằng chứng — đúng bẫy đã làm
C4.1 sinh 30.492 dương tính giả. Lần này hậu quả còn nặng hơn: mọi bộ sổ đều
kẹt ở "CÒN N MỤC CẦN RÀ SOÁT" và băng "SẴN SÀNG KHÓA SỔ" thành bất khả thi
(đã dựng thử và thấy test_ket_luan đỏ).

Chỉ C7.5 và C7.6 là cảnh báo thật, vì bằng chứng nằm ngay trong file: có phát
sinh ngoại tệ trên tài khoản tiền tệ mà không có 413; có kết chuyển lãi mà
không có 8211.
"""
import pandas as pd

from .base import VANG, BoiCanh, CheckResult, bat_dau, co_dong, phat_sinh_theo_prefix

NHOM = "G7"
TK_CHI_PHI = ("622", "627", "641", "642")
# TK gốc ngoại tệ có số dư phải đánh giá lại cuối kỳ (TT200 §69).
TK_TIEN_TE = ("111", "112", "113", "131", "136", "138", "331", "341")


def _checklist(ma: str, ten: str, co: bool, khi_co: str, khi_khong: str) -> CheckResult:
    """Một dòng checklist: luôn hiện tình trạng, KHÔNG bao giờ đổi kết luận khóa sổ."""
    bang = pd.DataFrame([{"co_phat_sinh": bool(co),
                          "ket_luan": khi_co if co else khi_khong}])
    return CheckResult(ma, ten, NHOM, VANG, bang, la_thong_ke=True)


def _canh_bao(ma: str, ten: str, thieu: bool, ly_do: str, ghi_chu: str = "") -> CheckResult:
    """Cảnh báo thật: chỉ bắn khi có bằng chứng đối ứng trong chính file."""
    ct = pd.DataFrame([{"ket_luan": ly_do}] if thieu else [], columns=["ket_luan"])
    return CheckResult(ma, ten, NHOM, VANG, ct, ghi_chu)


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    kq = []

    _, co_214 = phat_sinh_theo_prefix(df, "214")
    kq.append(_checklist("C7.1", "Khấu hao TSCĐ", co_214 > 0,
                         "Đã có bút toán Có 214 trong kỳ",
                         "Kỳ này KHÔNG thấy bút toán Có 214 — xác nhận lại nếu DN có TSCĐ đang dùng"))

    _, co_242 = phat_sinh_theo_prefix(df, "242")
    kq.append(_checklist("C7.2", "Phân bổ chi phí trả trước / CCDC", co_242 > 0,
                         "Đã có bút toán Có 242 trong kỳ",
                         "Kỳ này KHÔNG thấy bút toán Có 242 — xác nhận lại nếu DN có chi phí trả trước/CCDC đang phân bổ"))

    luong = any(co_dong(df, no=TK_CHI_PHI, co=(tk,)) for tk in ("334", "338"))
    kq.append(_checklist("C7.3", "Trích lương & các khoản theo lương", luong,
                         "Đã có bút toán đưa 334/338 vào chi phí 622/627/641/642",
                         "KHÔNG thấy bút toán đưa lương/BHXH (334/338) vào chi phí trong kỳ"))
    return kq
```

- [ ] **Step 4: Đăng ký + nhãn cột**
  - `app/checks/__init__.py`: thêm `g7_phan_bo_trich_lap` vào import, `"G7": "Phân bổ & trích lập cuối kỳ"` vào `TEN_NHOM`, `("G7", g7_phan_bo_trich_lap.kiem_tra)` vào `DANH_SACH`.
  - `app/checks/base.py`: thêm `"co_phat_sinh": "Có phát sinh"` vào `TEN_COT`. **Bắt buộc** — `test_moi_cot_cac_check_sinh_ra_deu_co_nhan_tieng_viet` quét mọi cột của mọi check và bắt cột nào còn tên tiếng Anh. (`_ghi_bang` của `report.py` đã tự đổi cột bool thành "Có"/"Không" nên Excel đọc được ngay.)

- [ ] **Step 5: Chạy `pytest tests/test_g7_phan_bo_trich_lap.py tests/test_ket_luan.py tests/test_api.py::test_moi_cot_cac_check_sinh_ra_deu_co_nhan_tieng_viet -W error` — PASS.** `test_ket_luan` xanh là bằng chứng lỗi thiết kế v1 đã được sửa.

- [ ] **Step 6: Commit**

```bash
git add app/checks/g7_phan_bo_trich_lap.py app/checks/__init__.py tests/test_g7_phan_bo_trich_lap.py
git commit -m "feat(checks): G7 checklist C7.1-C7.3 (khau hao, phan bo, luong)"
```

---

### Task 2: C7.4 Trích trước 335, C7.7 Dự phòng 229 (thống kê)

**Files:** Modify `app/checks/g7_phan_bo_trich_lap.py`; Test `tests/test_g7_phan_bo_trich_lap.py`.

- [ ] **Step 1: Test**

```python
def test_c74_c77_la_thong_ke_ps(ctx):
    df = tao_df([{"DebitAccount": "6421", "CreditAccount": "335", "Amount": 50},
                 {"DebitAccount": "632111", "CreditAccount": "2294", "Amount": 30}])
    kq = _kq(df, ctx)
    assert kq["C7.4"].la_thong_ke and kq["C7.4"].chi_tiet.iloc[0]["ps_co"] == 50
    assert kq["C7.7"].la_thong_ke and kq["C7.7"].chi_tiet.iloc[0]["ps_co"] == 30
```

- [ ] **Step 2: FAIL** (KeyError C7.4).

- [ ] **Step 3: Thêm hàm + gọi**

```python
def _thong_ke_ps(ma: str, ten: str, prefix: str, df: pd.DataFrame) -> CheckResult:
    no, co = phat_sinh_theo_prefix(df, prefix)
    bang = pd.DataFrame([{"TK": prefix, "ps_no": no, "ps_co": co}])
    return CheckResult(ma, ten, NHOM, VANG, bang, la_thong_ke=True)
```

Gọi trong `kiem_tra`: `kq.append(_thong_ke_ps("C7.4", "Trích trước chi phí (335)", "335", df))` và `kq.append(_thong_ke_ps("C7.7", "Dự phòng tổn thất tài sản (229)", "229", df))`. Cột `TK/ps_no/ps_co` đã có nhãn trong `TEN_COT`.

- [ ] **Step 4: PASS. Commit** `feat(checks): C7.4 trich truoc 335, C7.7 du phong 229`.

---

### Task 3: C7.5 Đánh giá tỷ giá, C7.6 Thuế TNDN (cảnh báo thật)

**Files:** Modify `app/checks/g7_phan_bo_trich_lap.py`; Test tương ứng.

**Interfaces:** C7.5 dùng `CurrencyCode` + `TK_TIEN_TE`; C7.6 dùng `co_dong(df, no=("911",), co=("421",))` (chiều kết chuyển lãi).

- [ ] **Step 1: Test**

```python
def test_c75_chi_ban_khi_ngoai_te_nam_tren_tk_tien_te(ctx):
    # Bằng chứng mạnh: ngoại tệ trên 331/112 -> nhiều khả năng còn số dư gốc ngoại tệ
    tren_tk_tien_te = tao_df([{"CurrencyCode": "USD", "DebitAccount": "3311",
                               "CreditAccount": "1122", "Amount": 100}])
    # Ngoại tệ chỉ chạy qua TK phi tiền tệ (vật tư) -> không suy ra số dư phải đánh giá
    tren_tk_vat_tu = tao_df([{"CurrencyCode": "USD", "DebitAccount": "1521",
                              "CreditAccount": "1521", "Amount": 100}])
    da_danh_gia = tao_df([{"CurrencyCode": "USD", "DebitAccount": "3311",
                           "CreditAccount": "1122", "Amount": 100},
                          {"CurrencyCode": "VND", "DebitAccount": "413",
                           "CreditAccount": "3311", "Amount": 5}])
    chi_vnd = tao_df([{"CurrencyCode": "VND", "DebitAccount": "1111",
                       "CreditAccount": "1121", "Amount": 100}])
    assert _kq(tren_tk_tien_te, ctx)["C7.5"].so_loi == 1
    assert _kq(tren_tk_vat_tu, ctx)["C7.5"].so_loi == 0
    assert _kq(da_danh_gia, ctx)["C7.5"].so_loi == 0
    assert _kq(chi_vnd, ctx)["C7.5"].so_loi == 0      # sổ thuần VND không bao giờ bị nhắc

def test_c76_co_lai_ma_khong_co_thue_tndn(ctx):
    lai_ko_thue = tao_df([{"DebitAccount": "911", "CreditAccount": "4212", "Amount": 100}])
    co_thue = tao_df([{"DebitAccount": "911", "CreditAccount": "4212", "Amount": 100},
                      {"DebitAccount": "8211", "CreditAccount": "3334", "Amount": 20}])
    lo = tao_df([{"DebitAccount": "4212", "CreditAccount": "911", "Amount": 100}])
    assert _kq(lai_ko_thue, ctx)["C7.6"].so_loi == 1
    assert _kq(co_thue, ctx)["C7.6"].so_loi == 0
    assert _kq(lo, ctx)["C7.6"].so_loi == 0           # lỗ thì không phải trích thuế
```

- [ ] **Step 2: FAIL.**

- [ ] **Step 3: Thêm vào `kiem_tra`**

```python
    # Chỉ suy "còn số dư gốc ngoại tệ" khi ngoại tệ chạy qua TK TIỀN TỆ. Ngoại tệ
    # trên TK vật tư/hàng hoá được ghi nhận theo tỷ giá lúc phát sinh và KHÔNG
    # phải đánh giá lại — nhắc ở đó là dương tính giả.
    cc = (df["CurrencyCode"].astype("string").str.strip()
          if "CurrencyCode" in df.columns else pd.Series(dtype="string", index=df.index))
    la_ngoai_te = cc.notna() & ~cc.isin(["", "VND"])
    cham_tk_tien_te = bat_dau(df["DebitAccount"], *TK_TIEN_TE) | bat_dau(df["CreditAccount"], *TK_TIEN_TE)
    co_du_ngoai_te = bool((la_ngoai_te & cham_tk_tien_te).any())
    no_413, co_413 = phat_sinh_theo_prefix(df, "413")
    kq.append(_canh_bao("C7.5", "Chưa đánh giá chênh lệch tỷ giá cuối kỳ",
                        co_du_ngoai_te and no_413 == 0 and co_413 == 0,
                        "Có phát sinh ngoại tệ trên tài khoản tiền tệ nhưng không thấy bút toán 413"
                        " — kiểm tra đánh giá lại số dư gốc ngoại tệ cuối kỳ",
                        ghi_chu="Chỉ xét dòng ngoại tệ chạm TK " + "/".join(TK_TIEN_TE)))

    co_lai = co_dong(df, no=("911",), co=("421",))
    no_821, _ = phat_sinh_theo_prefix(df, "821")
    kq.append(_canh_bao("C7.6", "Chưa trích/kết chuyển chi phí thuế TNDN",
                        co_lai and no_821 == 0,
                        "KQKD có lãi (911 → 421) nhưng không thấy phát sinh 8211"
                        " — kiểm tra thuế TNDN tạm tính",
                        ghi_chu="Chỉ xét khi kỳ có kết chuyển lãi"))
```

- [ ] **Step 4: PASS.** Chạy lại `tests/test_ket_luan.py` — vẫn xanh (hai kịch bản `SAN_SANG`/`CAN_RA_SOAT` đều thuần VND và không kết chuyển lãi).

- [ ] **Step 5: Commit** `feat(checks): C7.5 ty gia, C7.6 thue TNDN`.

---

### Task 4: Trạng thái bước mới `TU_XAC_NHAN` + đường ống hiển thị

> Task này **phải xong trước Task 5**. Thêm một trạng thái mà quên nối vào `report.py` / `app.js` sẽ gây `KeyError` lúc xuất Excel và hiển thị sai nhãn trên Tab A — cả hai đã được xác nhận bằng đọc mã.

**Files:**
- Modify: `app/trang_thai.py` (hằng số), `app/report.py` (`TEN_TRANG_THAI`, `MAU`), `app/web/app.js` (`ICON_TT`, `NHAN_TT`), `app/web/style.css` (`.tt-tu_xac_nhan`, `.chip-tt`)
- Test: `tests/test_trang_thai.py`, `tests/test_report.py`, `tests/test_web_static.py`

- [ ] **Step 1: Test**

```python
# tests/test_trang_thai.py
def test_tu_xac_nhan_khong_tinh_vao_ket_luan(ctx):
    """Trạng thái nhắc không được kéo sổ sạch ra khỏi 'SẴN SÀNG KHÓA SỔ'."""
    b = tt.BuocKhoaSo("X", tt.TU_XAC_NHAN, "chưa thấy", "C7.1")
    kl = tt.tinh_ket_luan([], [b])
    assert kl["muc_do_ket_luan"] == tt.SAN_SANG and kl["con_viec"] == 0
```

```python
# tests/test_report.py — trạng thái mới phải có nhãn & màu, không được KeyError
def test_report_biet_moi_trang_thai():
    from app import report, trang_thai as tt
    for s in (tt.DA_LAM, tt.CHUA_LAM, tt.CAN_RA, tt.KHONG_AP_DUNG, tt.TU_XAC_NHAN):
        assert s in report.TEN_TRANG_THAI and s in report.MAU
```

```python
# tests/test_web_static.py — app.js phải biết trạng thái mới, nếu không khoaTT() nuốt về "không áp dụng"
def test_app_js_biet_trang_thai_tu_xac_nhan():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert "tu_xac_nhan" in js
    css = (WEB / "style.css").read_text(encoding="utf-8")
    assert "tt-tu_xac_nhan" in css
```

- [ ] **Step 2: FAIL** (`AttributeError: TU_XAC_NHAN`).

- [ ] **Step 3: Nối đường ống**
  - `trang_thai.py`: `TU_XAC_NHAN = "tu_xac_nhan"` cạnh 4 hằng hiện có. `tinh_ket_luan` **không cần sửa** — nó chỉ đếm `CHUA_LAM`/`CAN_RA`, trạng thái mới tự động không tính; thêm `so_tu_xac_nhan` vào dict trả về để băng kết luận hiện dòng phụ.
  - `report.py`: `TEN_TRANG_THAI["tu_xac_nhan"] = "Tự xác nhận"`; `MAU["tu_xac_nhan"] = "#E7F0FA"` (xanh nhạt trung tính, khác hẳn vàng cảnh báo).
  - `app.js`: `ICON_TT.tu_xac_nhan = "bo-qua"` *(hoặc thêm hình mới `"hoi"`)*; `NHAN_TT.tu_xac_nhan = "Tự xác nhận"`.
  - `style.css`: `.buoc.tt-tu_xac_nhan` dùng token trung tính (`--chu-phu`, viền `--vien`), **không** dùng `--vang` để mắt không đọc nhầm thành cảnh báo.

- [ ] **Step 4: PASS. Commit** `feat(trang_thai): trang thai TU_XAC_NHAN + noi report/UI`.

---

### Task 5: 5 bước mới trong "16 bước khóa sổ"

**Files:** Modify `app/trang_thai.py`; Test `tests/test_trang_thai.py`.

**Interfaces:** `suy_trang_thai(df, ket_qua)` trả list `BuocKhoaSo`. Thứ tự theo bảng §5 của spec: 3 bước nhắc lên đầu; tỷ giá + thuế TNDN ngay trước "Khấu trừ thuế GTGT".

- [ ] **Step 1: Test**

```python
def test_du_16_buoc_dung_thu_tu(ctx):
    _, ds = _suy(kb("mac_dinh"), ctx)
    assert len(ds) == 16
    assert ds[0].buoc.startswith("Khấu hao TSCĐ")
    assert ds[-1].buoc.startswith("TK đầu 5/6/7/8")
    assert [b.buoc for b in ds[3:6]] == [
        "Tập hợp CP NVL trực tiếp 621 → 154",
        "Tập hợp CP nhân công trực tiếp 622 → 154",
        "Tập hợp & phân bổ CP SXC 627 → 154"]

def test_buoc_nhac_dung_trang_thai_tu_xac_nhan(ctx):
    b, _ = _suy(kb("mac_dinh"), ctx)          # sổ mặc định không có 214
    assert b["Khấu hao TSCĐ (Có 214 → 627/641/642)"].trang_thai == tt.TU_XAC_NHAN

def test_buoc_moi_chiu_duoc_ket_qua_rong(ctx):
    """F5/F7 mở rộng: suy_trang_thai({}) không được KeyError."""
    ds = tt.suy_trang_thai(kb("mac_dinh"), {})
    assert len(ds) == 16
    assert all(b.trang_thai == tt.KHONG_AP_DUNG
               for b in ds if b.ma_check.startswith("C7."))
```

- [ ] **Step 2: FAIL** (11 ≠ 16).

- [ ] **Step 3: Thêm helper + chèn bước**

```python
def _buoc_tu_check(ten, ma, ket_qua, tom_tat_dat, tom_tat_thieu, trang_thai_thieu):
    """Bước suy thẳng từ check được trích dẫn — không tự tính lại, để Tab A không
    bao giờ nói lệch với bảng chứng minh mà nó trỏ tới (lỗi đã tái diễn 7 lần).
    ket_qua rỗng (chưa chạy kiểm tra) -> KHONG_AP_DUNG, không KeyError."""
    r = ket_qua.get(ma)
    if r is None:
        return BuocKhoaSo(ten, KHONG_AP_DUNG, f"Chưa chạy kiểm tra {ma}", ma)
    if r.la_thong_ke:
        dat = bool(r.chi_tiet.iloc[0]["co_phat_sinh"]) if len(r.chi_tiet) else False
    else:
        dat = r.so_loi == 0
    if dat:
        return BuocKhoaSo(ten, DA_LAM, tom_tat_dat, ma)
    return BuocKhoaSo(ten, trang_thai_thieu, tom_tat_thieu, ma)
```

Chèn 3 bước C7.1/C7.2/C7.3 (`trang_thai_thieu=TU_XAC_NHAN`) lên đầu `ds`, và 2 bước C7.5/C7.6 (`trang_thai_thieu=CAN_RA`) ngay trước bước "Khấu trừ thuế GTGT". Tên bước lấy đúng chuỗi ở bảng §5 của spec.

- [ ] **Step 4: Sửa các test bị ảnh hưởng trong `tests/test_trang_thai.py`**
  - `test_du_11_buoc_dung_thu_tu` → thay bằng `test_du_16_buoc_dung_thu_tu` ở Step 1.
  - `test_kich_ban_phu_du_bon_trang_thai` → tập trạng thái nay là **5**; đổi tên thành `..._du_nam_trang_thai` và thêm `tt.TU_XAC_NHAN` vào tập khẳng định.

- [ ] **Step 5: PASS. Commit** `feat(trang_thai): them 5 buoc phan bo/trich lap/thue (16 buoc)`.

---

### Task 6: Đồng bộ mọi mốc đếm còn lại

> Danh sách này lấy từ **kết quả chạy thật**, không phải phỏng đoán.

**Files:** `tests/test_api.py`, `tests/test_chay_tat_ca.py`, `tests/test_du_lieu_bien.py`, `tests/test_e2e_file_that.py`.

- [ ] **Step 1:** `tests/test_api.py:33` → `len(kq["trang_thai"]) == 16 and len(kq["nhom"]) == 7`
- [ ] **Step 2:** `tests/test_chay_tat_ca.py:5,8` → đổi tên hàm thành `..._tra_37_check_...`; `assert len(kq) == 6 + 4 + 3 + 6 + 6 + 5 + 7`
- [ ] **Step 3:** `tests/test_du_lieu_bien.py:14` → `== 37`; dòng `16` → `len(ds) == 16`
- [ ] **Step 4:** `tests/test_e2e_file_that.py:25` → `== 16`
- [ ] **Step 5:** Chạy `pytest -W error` **toàn bộ** — phải xanh 100%, đặc biệt `tests/test_ket_luan.py`.
- [ ] **Step 6: Commit** `test: dong bo 37 check / 7 nhom / 16 buoc`

---

### Task 7: Nghiệm thu trên file thật

**Files:** Create `docs/ket-qua/them-nhom-7-but-toan-cuoi-ky.md`.

- [ ] **Step 1:** `JsApi().chay_kiem_tra(<1. Source/Bang ke chung tu 082027.xlsx>)`. Đối chiếu với số liệu đã đo sẵn ngày 16/09:

  | Mục | Kỳ vọng |
  |-----|---------|
  | Số bước / nhóm | 16 / 7 |
  | C7.1 khấu hao | ✅ đã có (Có 214 = 149.952.590) |
  | C7.2 phân bổ 242 | ✅ đã có (Có 242 = 449.969.674) |
  | C7.3 lương | ✅ đã có (Có 334 = 5.141.384.321, đối ứng 642/641) |
  | C7.6 thuế TNDN | ✅ đã có (821 Nợ = Có = 15.115.962) |
  | C7.5 tỷ giá | 🟡 **bắn** — 25 dòng USD chạm 331/112, `413` = 0 |
  | Kết luận đầu trang | vẫn "CHƯA SẴN SÀNG — còn 2 việc" **+ 1 vàng mới (C7.5)** |

- [ ] **Step 2:** Mở app kiểm mắt: Tab A đủ 16 bước, 3 bước nhắc hiện **"Tự xác nhận"** màu trung tính (không phải vàng); Tab B có thẻ Nhóm 7; xuất báo cáo Excel **và** xuất tổng hợp chi nhánh đều chạy (kiểm `TEN_TRANG_THAI` không KeyError).
- [ ] **Step 3:** Ghi nhật ký kết quả. Commit `docs: nhat ky them nhom 7`.

---

## Self-Review

- **Spec coverage:** §7 Nhóm 7 (C7.1–C7.7) → Task 1–3 ✔ · §5 bảng 16 bước → Task 4–5 ✔ · mốc đếm → Task 6 ✔ · nghiệm thu → Task 7 ✔.
- **Lỗi thiết kế v1 đã đóng:** C7.1–C7.3 chuyển sang `la_thong_ke` → `tinh_ket_luan` lọc sẵn → `test_ket_luan` xanh mà **không phải sửa chính nó** ✔.
- **Mọi mốc đếm đã liệt kê theo file:line từ lần chạy thật**, không phỏng đoán ✔.
- **Đường ống trạng thái mới** (report + app.js + css) tách thành Task 4 riêng, đứng **trước** Task 5 ✔.
- **`ket_qua` rỗng** được test riêng (`test_buoc_moi_chiu_duoc_ket_qua_rong`) ✔.
- **Bất biến D1** không vỡ: `TU_XAC_NHAN` được miễn; C7.5/C7.6 khi bắn đều có đúng 1 dòng chứng minh ✔.
- **Nhãn cột:** `co_phat_sinh` được thêm vào `TEN_COT` ngay ở Task 1 ✔.
- **Type consistency:** `_checklist` → bảng `{co_phat_sinh, ket_luan}`; `_canh_bao` → `{ket_luan}`; `_thong_ke_ps` → `{TK, ps_no, ps_co}`; `_buoc_tu_check` đọc `co_phat_sinh` cho check thống kê và `so_loi` cho check thường ✔.
