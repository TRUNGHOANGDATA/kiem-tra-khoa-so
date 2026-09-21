"""Nhóm 9 — Toàn vẹn Bảng cân đối số phát sinh (CĐPS).

Bốn đẳng thức mà mọi CĐPS đúng đều phải thỏa (nguồn: hướng dẫn soát CĐPS của nghề —
Đức Minh, MISA, Lê Ánh; và review trial balance quốc tế). Sai một trong bốn nghĩa là
sổ sai CHẮC CHẮN, không phải nghi ngờ — nên để ĐỎ, khác hẳn các check suy đoán.

    C9.1  Σ Nợ = Σ Có ở cả ba cột (dư đầu / phát sinh / dư cuối)
    C9.2  Từng TK: dư đầu + PS Nợ − PS Có = dư cuối
    C9.3  TK cha = Σ TK con
    C9.4  TK loại 5/6/7/8/9 phải hết số dư cuối kỳ (đã kết chuyển hết)
    C9.5  Phát sinh trên bảng kê chứng từ = phát sinh trên CĐPS (theo TK cấp 1)

Chưa nạp CĐPS -> cả nhóm đứng ngoài (la_thong_ke), KHÔNG báo "đạt" giả.
"""
from __future__ import annotations

import pandas as pd

from . import cdps_tien_ich as cd
from .base import DO, BoiCanh, CheckResult, fmt_so, so_phat_sinh_tai_khoan

NHOM = "G9"
# TK loại 5–9 (doanh thu, chi phí, xác định KQKD) không được còn số dư cuối kỳ.
LOAI_KHONG_DU = ("5", "6", "7", "8", "9")

# C9.5 — chỉ đối chiếu ở CẤP 1 (3 chữ số đầu). Xem test_g9_doi_chieu.py: hai nguồn khác
# độ chi tiết, và cây tài khoản của phần mềm kế toán KHÔNG theo tiền tố mã (62781 nằm
# dưới 6277). Cấp 1 là cấp sâu nhất mà tiền tố chắc chắn đúng.
CAP_DOI_CHIEU = 3
# Chênh do làm tròn đơn giá bình quân: trên dữ liệu thật lớn nhất 980đ/tài khoản.
NGUONG_DOI_CHIEU = 1_000.0


def _tong(df: pd.DataFrame, cot: str) -> float:
    return float(df[cot].fillna(0).sum()) if len(df) else 0.0


def _c91(la: pd.DataFrame) -> CheckResult:
    """Σ Nợ = Σ Có ở ba cặp cột. Mỗi cặp lệch -> một dòng chứng minh."""
    cap = [("Dư đầu kỳ", "du_dau_no", "du_dau_co"),
           ("Phát sinh trong kỳ", "ps_no", "ps_co"),
           ("Dư cuối kỳ", "du_cuoi_no", "du_cuoi_co")]
    dong = []
    for nhan, cn, cc in cap:
        no, co = _tong(la, cn), _tong(la, cc)
        if abs(no - co) > cd.NGUONG_DONG:
            dong.append({"Cột": nhan, "Tổng Nợ": no, "Tổng Có": co, "Chênh lệch": no - co,
                         "ly_do": f"{nhan}: Nợ {fmt_so(no)} ≠ Có {fmt_so(co)}"
                                  f" — lệch {fmt_so(abs(no - co))}"})
    return CheckResult("C9.1", "CĐPS không cân (tổng Nợ ≠ tổng Có)", NHOM, DO,
                       pd.DataFrame(dong, columns=["Cột", "Tổng Nợ", "Tổng Có", "Chênh lệch", "ly_do"]),
                       ghi_chu="Chỉ cộng dòng lá của CĐPS")


def _c92(la: pd.DataFrame) -> CheckResult:
    """Dư đầu + PS Nợ − PS Có = dư cuối, xét từng tài khoản."""
    if la.empty:
        return CheckResult("C9.2", "Số dư không khớp phát sinh (từng TK)", NHOM, DO, pd.DataFrame())
    tinh = cd.net(la, "du_dau_no", "du_dau_co") + la["ps_no"].fillna(0) - la["ps_co"].fillna(0)
    thuc = cd.net(la, "du_cuoi_no", "du_cuoi_co")
    lech = (tinh - thuc).abs() > cd.NGUONG_DONG
    ly_do = ("Dư đầu + PS Nợ − PS Có = " + tinh.map(fmt_so)
             + " nhưng dư cuối ghi " + thuc.map(fmt_so)
             + " — lệch " + (tinh - thuc).abs().map(fmt_so))
    return CheckResult("C9.2", "Số dư không khớp phát sinh (từng TK)", NHOM, DO,
                       cd.bang_chi_tiet(la[lech], ly_do[lech]))


def _c93(cdps: pd.DataFrame, la: pd.DataFrame) -> CheckResult:
    """TK cha (dòng nhóm) phải bằng tổng các TK con là dòng lá."""
    if "is_group" not in cdps.columns:
        return CheckResult("C9.3", "Tài khoản cha ≠ tổng tài khoản con", NHOM, DO, pd.DataFrame())
    # Chỉ xét TK cha THẬT (bỏ dòng "Tổng cộng:" số hiệu rỗng — nó không phải tài khoản).
    nhom = cdps[cdps["is_group"].fillna(0).astype(bool) & cd.tk_that(cdps)]
    ma_la = la["account"].fillna("").astype(str).str.strip()
    dong, ly_do = [], []
    for _, cha in nhom.iterrows():
        ma = str(cha["account"]).strip()
        con = la[ma_la.str.startswith(ma) & (ma_la != ma)]
        if con.empty:
            continue                      # nhóm không có dòng lá -> không kết luận
        sai = [f"{cd.NHAN_COT[c]}: cha {fmt_so(float(cha[c] or 0))}"
               f" ≠ con {fmt_so(_tong(con, c))}"
               for c in cd.COT_SO if abs(float(cha[c] or 0) - _tong(con, c)) > cd.NGUONG_DONG]
        if sai:
            dong.append(cha)
            ly_do.append("; ".join(sai))
    bang = pd.DataFrame(dong) if dong else la.iloc[0:0]
    return CheckResult("C9.3", "Tài khoản cha ≠ tổng tài khoản con", NHOM, DO,
                       cd.bang_chi_tiet(bang, ly_do if dong else ""))


def _c94(la: pd.DataFrame) -> CheckResult:
    """TK loại 5–9 còn số dư cuối kỳ = chưa kết chuyển hết (bằng chứng trực tiếp)."""
    if la.empty:
        return CheckResult("C9.4", "TK loại 5/6/7/8/9 còn số dư cuối kỳ", NHOM, DO, pd.DataFrame())
    la_pl = cd.loai(la).isin(LOAI_KHONG_DU)
    con_du = cd.net(la, "du_cuoi_no", "du_cuoi_co").abs() > cd.NGUONG_DONG
    bat = la[la_pl & con_du]
    # Series rỗng vẫn mang dtype float -> nối chuỗi sẽ ném UFuncTypeError, phải guard.
    ly_do = "" if bat.empty else (
        "Còn dư cuối kỳ " + cd.net(bat, "du_cuoi_no", "du_cuoi_co").abs().map(fmt_so)
        + " — TK doanh thu/chi phí phải kết chuyển hết về 0")
    return CheckResult("C9.4", "TK loại 5/6/7/8/9 còn số dư cuối kỳ", NHOM, DO,
                       cd.bang_chi_tiet(bat, ly_do))


TEN_C95 = "Phát sinh bảng kê ≠ phát sinh CĐPS"


def _gop_cap_1(df: pd.DataFrame, cot_ma: str) -> pd.DataFrame:
    ma = df[cot_ma].fillna("").astype(str).str.strip().str[:CAP_DOI_CHIEU]
    return df.assign(_c1=ma).groupby("_c1")[["ps_no", "ps_co"]].sum()


def _c95(df: pd.DataFrame, la: pd.DataFrame) -> CheckResult:
    """Hai nguồn phải cùng một quyển sổ: lệch = một bên thiếu/thừa chứng từ."""
    cot = ["Tài khoản", "PS Nợ bảng kê", "PS Nợ CĐPS", "Chênh Nợ",
           "PS Có bảng kê", "PS Có CĐPS", "Chênh Có", "ly_do"]
    bk = _gop_cap_1(so_phat_sinh_tai_khoan(df), "TK")
    cp = _gop_cap_1(la, "account") if len(la) else bk.iloc[0:0]
    g = cp.join(bk, how="outer", lsuffix="_cd", rsuffix="_bk").fillna(0.0)
    if g.empty:
        return CheckResult("C9.5", TEN_C95, NHOM, DO, pd.DataFrame(columns=cot))
    d_no = g["ps_no_bk"] - g["ps_no_cd"]
    d_co = g["ps_co_bk"] - g["ps_co_cd"]
    bat = g[(d_no.abs() > NGUONG_DOI_CHIEU) | (d_co.abs() > NGUONG_DOI_CHIEU)]

    dong = []
    for tk, r in bat.iterrows():
        dn, dc = r["ps_no_bk"] - r["ps_no_cd"], r["ps_co_bk"] - r["ps_co_cd"]
        ve = [f"{ben} lệch {fmt_so(abs(v))} ({'bảng kê thừa' if v > 0 else 'bảng kê thiếu'})"
              for ben, v in (("PS Nợ", dn), ("PS Có", dc)) if abs(v) > NGUONG_DOI_CHIEU]
        dong.append({"Tài khoản": tk,
                     "PS Nợ bảng kê": r["ps_no_bk"], "PS Nợ CĐPS": r["ps_no_cd"], "Chênh Nợ": dn,
                     "PS Có bảng kê": r["ps_co_bk"], "PS Có CĐPS": r["ps_co_cd"], "Chênh Có": dc,
                     "ly_do": "TK " + str(tk) + ": " + " · ".join(ve)})
    return CheckResult("C9.5", TEN_C95, NHOM, DO, pd.DataFrame(dong, columns=cot),
                       ghi_chu=f"Đối chiếu ở TK cấp 1 ({CAP_DOI_CHIEU} chữ số), bỏ qua chênh"
                               f" dưới {fmt_so(NGUONG_DOI_CHIEU)}đ do làm tròn")


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    ten = {"C9.1": "CĐPS không cân (tổng Nợ ≠ tổng Có)",
           "C9.2": "Số dư không khớp phát sinh (từng TK)",
           "C9.3": "Tài khoản cha ≠ tổng tài khoản con",
           "C9.4": "TK loại 5/6/7/8/9 còn số dư cuối kỳ",
           "C9.5": TEN_C95}
    if not cd.co_cdps(ctx):
        return [cd.khong_co_cdps(ma, t, NHOM, DO) for ma, t in ten.items()]
    cdps = ctx.cdps
    la = cd.dong_la(cdps)
    r95 = _c95(df, la)
    # CĐPS nạp trước khi bảng kê được kết xuất -> hai nguồn là hai lát cắt sổ khác nhau,
    # chênh lệch giữa chúng KHÔNG chứng minh sổ sai. Vẫn liệt kê để soi, nhưng không kéo
    # kết luận (xem BoiCanh.cdps_cu_hon). C9.1–C9.4 chỉ đọc CĐPS nên không bị ảnh hưởng.
    if getattr(ctx, "cdps_cu_hon", False):
        r95.la_thong_ke = True
        r95.ghi_chu = ("CĐPS đang lưu CŨ HƠN bảng kê — nạp lại CĐPS rồi kiểm tra lại thì"
                       " con số này mới có nghĩa. " + r95.ghi_chu)
    return [_c91(la), _c92(la), _c93(cdps, la), _c94(la), r95]
