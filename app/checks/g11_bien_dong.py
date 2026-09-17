"""Nhóm 11 — Biến động kỳ (Đợt 4).

Ba câu hỏi mà kế toán hỏi khi cầm CĐPS lên, xếp theo SỨC MẠNH BẰNG CHỨNG:

    C11.1  Tài khoản nào biến động mạnh trong kỳ?           THỐNG KÊ (chỉ để soi)
    C11.2  Biên lợi nhuận gộp có vô lý không?                VÀNG (bằng chứng thật)
    C11.3  Phát sinh kỳ này lệch hẳn kỳ trước ở đâu?         THỐNG KÊ (chỉ để soi)

C11.1 KHÔNG cần nạp CĐPS kỳ trước: cột dư ĐẦU kỳ của chính CĐPS này chính là dư
cuối của kỳ trước. C11.3 thì cần thật, vì so PHÁT SINH chứ không so số dư.

C11.2 để VÀNG vì nó là bằng chứng trực tiếp trên số liệu: bán dưới giá vốn, hoặc
có doanh thu mà không ghi giá vốn, là chuyện phải giải thích được trước khi khóa sổ.
"""
from __future__ import annotations

import pandas as pd

from . import cdps_tien_ich as cd
from .base import VANG, BoiCanh, CheckResult, fmt_so

NHOM = "G11"

# C11.1 — chỉ xét TK loại 1–4. Loại 5–9 còn dư chỉ vì chưa kết chuyển, đó là việc
# của G5/C9.4; để lại thì 6/9 dòng của A01 là báo trùng.
LOAI_XET = ("1", "2", "3", "4")
# Phải vượt CẢ HAI: biến động tương đối lớn VÀ số tiền đáng kể. Chỉ một trong hai
# thì danh sách toàn tài khoản vụn (2 nghìn thành 20 nghìn = tăng 900%).
# Đo trên CĐPS thật 8 chi nhánh: 30%+50tr -> 4–15 dòng/chi nhánh. Mốc 100%+200tr
# chỉ còn 1–4 dòng, bỏ sót đúng khoản đáng soi nhất (A01: 2281 tăng 30 tỷ mà chỉ
# là +85%; 2442 giảm 15,4 tỷ mà chỉ là −83%).
NGUONG_TY_LE = 0.30
NGUONG_TUYET_DOI = 50_000_000.0
# 35–51 trong 60–92 dòng lá có dư đầu = 0 -> không có mẫu số. Nhánh riêng theo số
# tuyệt đối, nếu không sẽ mù đúng chỗ cần nhìn (A01: 3331 từ 0 lên 5,98 tỷ).
NGUONG_DU_MOI = 200_000_000.0

# C11.2 — biên gộp = (doanh thu thuần − giá vốn) / doanh thu thuần.
# DÙNG ps_co CỦA 511 VÀ ps_no CỦA 632, không dùng net: bút toán kết chuyển 632→911
# nằm ở ps_co nên net đẩy biên của 6/8 chi nhánh lên đúng 100% — vô nghĩa.
TK_DOANH_THU, TK_GIAM_TRU, TK_GIA_VON = ("511",), ("521", "531", "532"), ("632",)
# 7/8 chi nhánh thật nằm trong 0,3–20,6%; A02 = 71,1% là thiếu ghi giá vốn thật
# (6322 chỉ 129 triệu đối ứng 12,7 tỷ doanh thu). Mốc 90% ban đầu bỏ sót đúng ca
# duy nhất có lỗi.
BIEN_CAO = 0.40
LOAI_PHAI_KET_CHUYEN = ("5", "6", "7", "8", "9")

# C11.3 — so ở CẤP 1 (3 chữ số) vì cây tài khoản không theo tiền tố mã (xem C9.5).
CAP_SO_SANH = 3
NGUONG_TY_LE_PS = 1.0
NGUONG_TUYET_DOI_PS = 500_000_000.0

TEN = {
    "C11.1": "Số dư biến động mạnh trong kỳ",
    "C11.2": "Biên lợi nhuận gộp bất thường",
    "C11.3": "Phát sinh lệch mạnh so với kỳ trước",
}


def _c111(la: pd.DataFrame) -> CheckResult:
    la = la[cd.loai(la).isin(LOAI_XET)]
    if la.empty:
        return _thong_ke("C11.1", pd.DataFrame(), "")
    dau = cd.net(la, "du_dau_no", "du_dau_co")
    cuoi = cd.net(la, "du_cuoi_no", "du_cuoi_co")
    delta = cuoi - dau
    co_goc = dau.abs() >= 1
    ty_le = (delta.abs() / dau.abs()).where(co_goc)
    bat_ty_le = co_goc & (ty_le >= NGUONG_TY_LE) & (delta.abs() >= NGUONG_TUYET_DOI)
    bat_moi = ~co_goc & (cuoi.abs() >= NGUONG_DU_MOI)
    bat = la[bat_ty_le | bat_moi]
    if bat.empty:
        ly_do = ""
    else:
        pct = (ty_le[bat.index] * 100).round(0)
        ly_do = pd.Series(
            ["Dư đầu 0 → dư cuối " + fmt_so(c) + " (tài khoản mới phát sinh số dư)"
             if pd.isna(p) else
             f"Dư đầu {fmt_so(d)} → dư cuối {fmt_so(c)} ({p:.0f}%)"
             for d, c, p in zip(dau[bat.index], cuoi[bat.index], pct)],
            index=bat.index)
    return _thong_ke("C11.1", cd.bang_chi_tiet(bat, ly_do),
                     f"TK loại 1–4; đổi ≥ {NGUONG_TY_LE:.0%} và ≥ {fmt_so(NGUONG_TUYET_DOI)}đ,"
                     f" hoặc dư đầu 0 mà dư cuối ≥ {fmt_so(NGUONG_DU_MOI)}đ."
                     " So với dư đầu kỳ của chính CĐPS — không cần nạp CĐPS kỳ trước")


def _thong_ke(ma: str, bang: pd.DataFrame, ghi_chu: str) -> CheckResult:
    r = CheckResult(ma, TEN[ma], NHOM, VANG, bang, ghi_chu=ghi_chu)
    r.la_thong_ke = True
    return r


def _chua_ket_chuyen(la: pd.DataFrame) -> bool:
    """Loại 5–9 còn số dư cuối = kỳ chưa kết chuyển xong (cùng bằng chứng với C9.4)."""
    pl = la[cd.loai(la).isin(LOAI_PHAI_KET_CHUYEN)]
    return bool(len(pl) and (cd.net(pl, "du_cuoi_no", "du_cuoi_co").abs() > 1).any())


def _c112(la: pd.DataFrame) -> CheckResult:
    cot = ["Doanh thu thuần", "Giá vốn", "Biên lợi nhuận gộp", "ly_do"]
    dt = cd.theo_prefix(la, *TK_DOANH_THU)["ps_co"].fillna(0).sum()
    giam = cd.theo_prefix(la, *TK_GIAM_TRU)["ps_no"].fillna(0).sum()
    gv = cd.theo_prefix(la, *TK_GIA_VON)["ps_no"].fillna(0).sum()
    thuan = float(dt) - float(giam)
    dong = []
    if thuan > 0:
        bien = (thuan - float(gv)) / thuan
        if float(gv) <= 0:
            ly_do = ("Có doanh thu thuần " + fmt_so(thuan)
                     + " nhưng KHÔNG ghi nhận giá vốn 632 nào trong kỳ")
        elif bien < 0:
            ly_do = ("Biên lợi nhuận gộp ÂM " + f"{bien:.1%}"
                     + " — giá vốn " + fmt_so(gv) + " lớn hơn doanh thu thuần " + fmt_so(thuan))
        elif bien > BIEN_CAO:
            ly_do = (f"Biên lợi nhuận gộp {bien:.1%} > {BIEN_CAO:.0%}"
                     " — soát lại xem đã kết chuyển đủ giá vốn chưa")
        else:
            ly_do = ""
        if ly_do:
            dong.append({"Doanh thu thuần": thuan, "Giá vốn": float(gv),
                         "Biên lợi nhuận gộp": round(bien, 4), "ly_do": ly_do})
    ghi_chu = "Doanh thu thuần = PS Có 511 − PS Nợ 521/531/532; giá vốn = PS Nợ 632"
    r = CheckResult("C11.2", TEN["C11.2"], NHOM, VANG, pd.DataFrame(dong, columns=cot),
                    ghi_chu=ghi_chu)
    # Kỳ chưa kết chuyển xong thì giá vốn chưa đủ, biên cao là chuyện đương nhiên —
    # kết luận lúc này vừa là suy từ số chưa chốt, vừa báo trùng với G5.
    if _chua_ket_chuyen(la):
        r.la_thong_ke = True
        r.ghi_chu = ghi_chu + " · Kỳ chưa kết chuyển hết TK 5–9 nên chỉ nêu để soát"
    return r


def _gop_cap_1(la: pd.DataFrame) -> pd.DataFrame:
    ma = la["account"].fillna("").astype(str).str.strip().str[:CAP_SO_SANH]
    return la.assign(_c1=ma).groupby("_c1")[["ps_no", "ps_co"]].sum()


def _c113(la: pd.DataFrame, la_truoc: pd.DataFrame) -> CheckResult:
    cot = ["Tài khoản", "PS kỳ này", "PS kỳ trước", "Chênh lệch", "ly_do"]
    nay, truoc = _gop_cap_1(la), _gop_cap_1(la_truoc)
    g = truoc.join(nay, how="outer", lsuffix="_truoc", rsuffix="_nay").fillna(0.0)
    dong = []
    for tk, r in g.iterrows():
        a = float(r["ps_no_truoc"]) + float(r["ps_co_truoc"])
        b = float(r["ps_no_nay"]) + float(r["ps_co_nay"])
        d = b - a
        if a <= 0 or abs(d) < NGUONG_TUYET_DOI_PS or abs(d) / a < NGUONG_TY_LE_PS:
            continue
        dong.append({"Tài khoản": tk, "PS kỳ này": b, "PS kỳ trước": a, "Chênh lệch": d,
                     "ly_do": f"TK {tk}: phát sinh {fmt_so(a)} → {fmt_so(b)}"
                              f" ({'tăng' if d > 0 else 'giảm'} {abs(d) / a:.0%})"})
    return _thong_ke("C11.3", pd.DataFrame(dong, columns=cot),
                     f"So ở TK cấp 1 với kỳ liền trước; chỉ nêu mức đổi ≥ "
                     f"{NGUONG_TY_LE_PS:.0%} và ≥ {fmt_so(NGUONG_TUYET_DOI_PS)}đ")


def _khong_co_ky_truoc() -> CheckResult:
    return _thong_ke("C11.3", pd.DataFrame(),
                     "Chưa nạp CĐPS kỳ trước — không so sánh được")


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    if not cd.co_cdps(ctx):
        return [cd.khong_co_cdps(ma, t, NHOM, VANG) for ma, t in TEN.items()]
    la = cd.dong_la(ctx.cdps)
    truoc = getattr(ctx, "cdps_truoc", None)
    co_truoc = isinstance(truoc, pd.DataFrame) and not truoc.empty
    return [_c111(la), _c112(la),
            _c113(la, cd.dong_la(truoc)) if co_truoc else _khong_co_ky_truoc()]
