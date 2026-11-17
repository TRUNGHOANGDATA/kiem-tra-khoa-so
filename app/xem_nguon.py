"""Màn "Dữ liệu đã nạp": lọc / tổng / chọn cột cho bảng kê và sổ chi tiết bán hàng trong kho.

Thuần DataFrame — api.py lo đọc kho, nhớ tạm và phân trang. Chỉ ĐỌC: muốn đổi dữ liệu thì
nạp lại file.
"""
from __future__ import annotations

import pandas as pd

from .checks.base import bat_dau
from .kho import BANG_KE, SO_BAN_HANG

# Bảng kê có ~80 cột; màn xem chỉ hiện các cột đọc được, xuất Excel thì ra đủ.
COT_HIEN = {
    BANG_KE: ("DocCode", "DocNo", "DocDate", "Description", "DebitAccount", "CreditAccount",
              "Amount", "CustomerName", "ItemCode", "ItemName", "Quantity9", "TaxCode",
              "TransCode", "CreatedByName"),
    SO_BAN_HANG: ("DocCode", "DocNo", "DocDate", "TransCode", "DebitAccount2", "CreditAccount2",
                  "CustomerName", "ItemCode", "ItemName", "Quantity", "UnitPrice",
                  "Amount2", "Amount3", "Description"),
}
NHAN = {"Amount2": "Doanh thu", "Amount3": "Thuế GTGT", "DebitAccount2": "TK Nợ",
        "CreditAccount2": "TK Có", "TransCode": "Loại GD", "CustomerName": "Khách hàng",
        "ItemCode": "Mã hàng", "ItemName": "Tên hàng", "Quantity9": "Số lượng",
        "Quantity": "Số lượng", "UnitPrice": "Đơn giá"}


def _tk(df: pd.DataFrame, loai: str) -> tuple[str, str]:
    return ("DebitAccount2", "CreditAccount2") if loai == SO_BAN_HANG else ("DebitAccount", "CreditAccount")


def loc(df: pd.DataFrame, loai: str, *, loc_no="", loc_co="", chi_thue_0=False,
        loai_ct="", tim="") -> pd.DataFrame:
    """Lọc theo đầu số TK Nợ/Có, loại chứng từ, dòng thuế 0 (sổ bán hàng) và ô tìm."""
    no, co = _tk(df, loai)
    m = pd.Series(True, index=df.index)
    if str(loc_no).strip() and no in df.columns:
        m &= bat_dau(df[no], str(loc_no).strip())
    if str(loc_co).strip() and co in df.columns:
        m &= bat_dau(df[co], str(loc_co).strip())
    if loai_ct and "DocCode" in df.columns:
        m &= df["DocCode"].fillna("").astype(str).str.strip().eq(str(loai_ct).strip())
    if chi_thue_0 and loai == SO_BAN_HANG and {"Amount2", "Amount3"} <= set(df.columns):
        # Doanh thu ≠ 0 mà thuế = 0 — đúng cách KTTH lọc tay. Hàng tặng giá 0 không tính.
        m &= df["Amount3"].eq(0) & df["Amount2"].ne(0)
    df = df[m]
    q = str(tim or "").strip().lower()
    if q:
        hien = [c for c in COT_HIEN[loai] if c in df.columns]
        chu = df[hien].copy()
        for c in hien:
            if pd.api.types.is_datetime64_any_dtype(chu[c]):
                chu[c] = chu[c].dt.strftime("%d/%m/%Y")
        hop = chu.astype(str).apply(lambda s: s.str.lower().str.contains(q, regex=False)).any(axis=1)
        df = df[hop]
    return df


def tong_hop(df: pd.DataFrame, loai: str) -> list[dict]:
    """Các ô tổng ở đầu bảng (tính trên phần ĐANG LỌC)."""
    if loai == SO_BAN_HANG:
        ban = bat_dau(df["DebitAccount2"], "131") & bat_dau(df["CreditAccount2"], "511")
        tl = bat_dau(df["DebitAccount2"], "521") & bat_dau(df["CreditAccount2"], "131")
        return [
            {"nhan": "Doanh thu (Nợ131/Có511)", "gia_tri": float(df.loc[ban, "Amount2"].sum())},
            {"nhan": "Thuế ra", "gia_tri": float(df.loc[ban, "Amount3"].sum())},
            {"nhan": "Trả lại (Nợ521/Có131)", "gia_tri": float(df.loc[tl, "Amount2"].sum())},
            {"nhan": "Thuế trả lại", "gia_tri": float(df.loc[tl, "Amount3"].sum())},
        ]
    so_ct = (df["DocCode"].fillna("").astype(str) + "·" + df["DocNo"].fillna("").astype(str)).nunique()
    return [{"nhan": "Tổng phát sinh", "gia_tri": float(df["Amount"].sum())},
            {"nhan": "Số chứng từ", "gia_tri": float(so_ct)}]


def cot_hien(df: pd.DataFrame, loai: str) -> list[str]:
    return [c for c in COT_HIEN[loai] if c in df.columns]
