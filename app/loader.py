"""Đọc bảng kê chứng từ Bravo (Excel) và chuẩn hóa thành DataFrame."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

COT_BAT_BUOC = ["DocNo", "DocDate", "DebitAccount", "CreditAccount", "Amount"]
COT_SO = ["Amount", "OriginalAmount", "ExchangeRate", "Quantity9", "UnitCost"]
COT_CHUOI = ["DocCode", "DocNo", "Description", "DebitAccount", "CreditAccount", "TaxCode",
             "CustomerCode", "CustomerName", "ItemCode", "ItemName", "WarehouseName",
             "CurrencyCode", "CreatedByName", "CashFlowName", "ExpenseCatgName", "DeptName"]


@dataclass
class ThongTinFile:
    path: str
    ten: str
    ky: str
    ky_thang: int
    ky_nam: int
    so_dong: int
    tong_ps: float
    nhat_ky: list[str] = field(default_factory=list)


def chuan_hoa(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    log: list[str] = []
    df = df.copy()
    for c in COT_CHUOI:
        if c not in df.columns:
            df[c] = pd.NA
        s = df[c]
        # Cột mã (TK, mã đối tượng...) có thể bị pandas đọc thành float khi cột có ô trống
        # -> ép về Int64 trước, để "6421.0" không lọt vào so khớp prefix ở các bộ kiểm tra.
        if pd.api.types.is_float_dtype(s):
            khong_null = s.dropna()
            if len(khong_null) and (khong_null % 1 == 0).all():
                s = s.astype("Int64")
        s = s.astype("string").str.strip()
        df[c] = s.mask(s.isna() | s.eq("") | s.str.upper().eq("NULL"))
    for c in COT_SO:
        if c not in df.columns:
            df[c] = 0.0
        so = pd.to_numeric(df[c], errors="coerce")
        hong = int(so.isna().sum() - df[c].isna().sum())
        if hong > 0:
            log.append(f"Cột {c}: {hong} giá trị không phải số, đã ép về 0")
        df[c] = so.fillna(0.0).astype(float)
    df["DocDate"] = pd.to_datetime(df["DocDate"], errors="coerce")
    return df, log


def xac_dinh_ky(df: pd.DataFrame) -> tuple[int, int]:
    d = df["DocDate"].dropna()
    if d.empty:
        raise ValueError("Không có ngày chứng từ hợp lệ để xác định kỳ")
    ky = (d.dt.year * 100 + d.dt.month).mode().iloc[0]
    return int(ky % 100), int(ky // 100)


def doc_bang_ke(path: str) -> tuple[pd.DataFrame, ThongTinFile]:
    try:
        raw = pd.read_excel(path, engine="calamine")
    except Exception:
        raw = pd.read_excel(path, engine="openpyxl")
    thieu = [c for c in COT_BAT_BUOC if c not in raw.columns]
    if thieu:
        raise ValueError(f"Thiếu cột bắt buộc: {', '.join(thieu)}")
    df, log = chuan_hoa(raw)
    thang, nam = xac_dinh_ky(df)
    tt = ThongTinFile(path=path, ten=Path(path).name, ky=f"{thang:02d}/{nam}",
                      ky_thang=thang, ky_nam=nam, so_dong=len(df),
                      tong_ps=float(df["Amount"].sum()), nhat_ky=log)
    return df, tt


def tim_file_moi_nhat(thu_muc: str) -> str | None:
    p = Path(thu_muc)
    if not p.is_dir():
        return None
    files = [f for f in p.glob("*.xls*") if not f.name.startswith("~$")]
    if not files:
        return None
    return str(max(files, key=os.path.getmtime))
