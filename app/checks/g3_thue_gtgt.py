"""Nhóm 3 — Thuế GTGT."""
import pandas as pd

from .base import VANG, XANH, BoiCanh, CheckResult, bat_dau, khoa_chung_tu, tao_ket_qua

NHOM = "G3"
TK_THUE = ("1331", "33311")


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    kq = []
    tax = df["TaxCode"].fillna("").astype(str).str.strip().str.upper()
    co_thue = tax.ne("") & tax.ne("V00")
    dong_tk_thue = bat_dau(df["DebitAccount"], *TK_THUE) | bat_dau(df["CreditAccount"], *TK_THUE)
    ct = khoa_chung_tu(df)

    docs_thieu = set(ct[co_thue]) - set(ct[dong_tk_thue])
    r31 = tao_ket_qua(df[co_thue & ct.isin(docs_thieu)], "C3.1",
                      "Có mã thuế nhưng chứng từ thiếu TK thuế", NHOM, VANG,
                      "TaxCode chịu thuế nhưng cả chứng từ không có dòng 1331/33311 — Bravo hay"
                      " gắn TaxCode cả dòng giá vốn/kho; chỉ để soát, không kéo kết luận")
    r31.la_thong_ke = True
    kq.append(r31)

    dt = bat_dau(df["CreditAccount"], "511") & co_thue
    dong_33311 = bat_dau(df["DebitAccount"], "33311") | bat_dau(df["CreditAccount"], "33311")
    docs_dt_thieu = set(ct[dt]) - set(ct[dong_33311])
    kq.append(tao_ket_qua(df[dt & ct.isin(docs_dt_thieu)], "C3.2",
                          "Doanh thu thiếu thuế đầu ra", NHOM, VANG,
                          "Ghi Có 511 với mã thuế chịu thuế nhưng cả chứng từ"
                          " không có dòng 33311 (thuế GTGT đầu ra)"))

    vao = df[bat_dau(df["DebitAccount"], "1331")].groupby(tax[bat_dau(df["DebitAccount"], "1331")])["Amount"].sum()
    ra = df[bat_dau(df["CreditAccount"], "33311")].groupby(tax[bat_dau(df["CreditAccount"], "33311")])["Amount"].sum()
    dem = df.groupby(tax)["Amount"].size()
    bang = pd.concat([vao.rename("thue_vao_1331"), ra.rename("thue_ra_33311"),
                      dem.rename("so_dong")], axis=1).fillna(0)
    bang.index.name = "TaxCode"
    kq.append(CheckResult("C3.3", "Tổng hợp thuế GTGT theo mã thuế", NHOM, XANH,
                          bang.reset_index(), la_thong_ke=True))
    return kq
