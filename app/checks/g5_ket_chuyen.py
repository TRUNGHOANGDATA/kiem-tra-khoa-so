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
