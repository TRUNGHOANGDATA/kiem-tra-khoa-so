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
