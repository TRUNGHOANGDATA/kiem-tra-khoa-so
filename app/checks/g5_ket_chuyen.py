"""Nhóm 5 — Kết chuyển cuối kỳ: phát hiện thiếu bút toán kết chuyển và TK 5/6/7/8 chưa về 0."""
import pandas as pd

from .base import (DO, VANG, NGUONG_CON_LAI, BoiCanh, CheckResult, bat_dau, co_dong, fmt_so,
                   phat_sinh_theo_prefix, so_phat_sinh_tai_khoan)

NHOM = "G5"
TK_DOANH_THU = ("511", "515", "711")
TK_CHI_PHI_911 = ("635", "641", "642", "811")
TK_TU_KET_CHUYEN_CUOI_KY = ("621", "622", "627")
COT_TH = ["TK", "ps_no", "ps_co", "ly_do"]


def _bang(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=COT_TH)


def _thieu(df, tk: str, no: tuple, co: tuple, ly_do: str, la_ben_no: bool = True) -> dict | None:
    ps_no, ps_co = phat_sinh_theo_prefix(df, tk)
    if ps_no <= 0 and ps_co <= 0:
        return None
    if not co_dong(df, no=no, co=co):
        return {"TK": tk, "ps_no": ps_no, "ps_co": ps_co, "ly_do": ly_do}
    con_lai = (ps_no - ps_co) if la_ben_no else (ps_co - ps_no)
    if con_lai > NGUONG_CON_LAI:
        return {"TK": tk, "ps_no": ps_no, "ps_co": ps_co,
                "ly_do": f"Đã kết chuyển một phần — còn {fmt_so(con_lai)} chưa kết chuyển về 911"}
    return None


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    kq = []
    bang = so_phat_sinh_tai_khoan(df)
    pl = bang[bat_dau(bang["TK"], "5", "6", "7", "8") & (bang["net"].abs() > 0.5)].copy()
    la_tu_ket_chuyen = bat_dau(pl["TK"], *TK_TU_KET_CHUYEN_CUOI_KY)
    pl["ly_do"] = pl["net"].map(lambda n: f"Net phát sinh trong kỳ còn {fmt_so(n)} — chưa kết chuyển hết")
    pl.loc[la_tu_ket_chuyen, "ly_do"] = pl.loc[la_tu_ket_chuyen, "net"].map(
        lambda n: f"621/622/627 không có tùy chọn kết chuyển cuối năm — phải đưa hết về 154 trong kỳ,"
                  f" còn {fmt_so(n)}")
    kq.append(CheckResult("C5.1", "TK đầu 5/6/7/8 chưa kết chuyển hết", NHOM, VANG,
                          pl[["TK", "ps_no", "ps_co", "net", "ly_do"]].reset_index(drop=True),
                          ghi_chu="Có DN chỉ kết chuyển cuối năm — kế toán tự quyết định"))

    r = _thieu(df, "632", ("911",), ("632",), "Có phát sinh 632 nhưng thiếu bút toán Nợ 911 / Có 632",
               la_ben_no=True)
    kq.append(CheckResult("C5.2", "Thiếu kết chuyển giá vốn 632 → 911", NHOM, DO, _bang([r] if r else [])))

    rows = [x for tk in TK_DOANH_THU
            if (x := _thieu(df, tk, (tk,), ("911",), f"Có phát sinh {tk} nhưng thiếu Nợ {tk} / Có 911",
                            la_ben_no=False))]
    kq.append(CheckResult("C5.3", "Thiếu kết chuyển doanh thu → 911", NHOM, DO, _bang(rows)))

    rows = [x for tk in TK_CHI_PHI_911
            if (x := _thieu(df, tk, ("911",), (tk,), f"Có phát sinh {tk} nhưng thiếu Nợ 911 / Có {tk}",
                            la_ben_no=True))]
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
    _, ra_co = phat_sinh_theo_prefix(df, "3331")
    if vao_no > 0 and ra_co > 0 and not co_dong(df, no=("3331",), co=("1331",)):
        rows.append({"TK": "3331", "ps_no": vao_no, "ps_co": ra_co,
                     "ly_do": "Có thuế vào và thuế ra nhưng thiếu bút toán khấu trừ Nợ 3331 / Có 1331"})
    kq.append(CheckResult("C5.6", "Thiếu khấu trừ thuế GTGT", NHOM, VANG, _bang(rows)))
    return kq
