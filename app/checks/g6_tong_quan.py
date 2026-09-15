"""Nhóm 6 — Thống kê & soát xét (không phải lỗi)."""
import pandas as pd

from .base import XANH, BoiCanh, CheckResult, so_phat_sinh_tai_khoan

NHOM = "G6"
TOP_N = 50


def _tk(ma, ten, bang) -> CheckResult:
    return CheckResult(ma, ten, NHOM, XANH, bang.reset_index(drop=True), la_thong_ke=True)


def _gom(df, cot) -> pd.DataFrame:
    g = df.groupby(cot, dropna=False)["Amount"].agg(so_dong="size", tong="sum").reset_index()
    return g.sort_values("tong", ascending=False)


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    cols = ["DocNo", "DocDate", "DebitAccount", "CreditAccount", "Amount", "Description", "CreatedByName"]
    top = df.nlargest(TOP_N, "Amount")[[c for c in cols if c in df.columns]]

    theo_ngay = _gom(df, "DocDate").sort_values("DocDate")
    m, s = theo_ngay["so_dong"].mean(), theo_ngay["so_dong"].std(ddof=0)
    theo_ngay["bat_thuong"] = theo_ngay["so_dong"] > (m + 2 * s) if len(theo_ngay) > 1 else False

    return [
        _tk("C6.1", f"Top {TOP_N} giao dịch giá trị lớn", top),
        _tk("C6.2", "Phát sinh theo tài khoản", so_phat_sinh_tai_khoan(df).sort_values("ps_no", ascending=False)),
        _tk("C6.3", "Phát sinh theo loại chứng từ", _gom(df, "DocCode")),
        _tk("C6.4", "Phát sinh theo người lập", _gom(df, "CreatedByName")),
        _tk("C6.5", "Phân bố bút toán theo ngày", theo_ngay),
    ]
