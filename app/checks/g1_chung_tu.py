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
