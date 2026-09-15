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
