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
