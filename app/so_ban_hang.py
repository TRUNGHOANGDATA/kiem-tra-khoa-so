"""Đọc Sổ chi tiết bán hàng (Bravo) — nguồn có THUẾ GTGT THEO TỪNG DÒNG HÀNG.

Bảng kê chứng từ chỉ có MỘT dòng 33311 gộp, không mang ItemCode, nên không biết dòng
hàng nào thiếu thuế. Sổ này thì có: `Amount2` = doanh thu, `Amount3` = thuế GTGT của
đúng dòng đó (TotalAmount = Amount2 + Amount3 khớp 100% trên A01 09/2026). `Amount`
ở đây là GIÁ VỐN, không phải doanh thu — đừng nhầm với bảng kê.

File nguồn: 1 sheet `Table1`, header dòng đầu, không có BranchCode → chi nhánh + kỳ suy
từ TÊN FILE, mã nằm GIỮA tên: `So chi tiet ban hang A01 092026.xlsx`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# mã chi nhánh (chữ + số) + khoảng trắng + MMYYYY ở BẤT KỲ đâu trong tên file
RE_TEN = re.compile(r"(?<![A-Za-z0-9])([A-Za-z]+\d+)\s+(\d{2})(\d{4})(?!\d)")

COT_BAT_BUOC = ("DocNo", "DocCode", "DocDate", "TransCode",
                "DebitAccount2", "CreditAccount2", "Amount2", "Amount3")
COT_SO = ("Quantity", "UnitPrice", "Amount", "Amount2", "Amount3")
COT_CHUOI = ("DocNo", "DocCode", "TransCode", "DebitAccount2", "CreditAccount2",
             "CustomerCode", "CustomerName", "ItemCode", "ItemName", "Unit", "Description")


class KhongPhaiSoBanHang(Exception):
    """Thiếu cột chuẩn, tên file không suy được kỳ, hoặc kỳ tên file ≠ ngày chứng từ."""


@dataclass
class MetaSoBanHang:
    ma: str
    nam: int
    thang: int


def suy_branch_ky(ten_file: str) -> tuple[str, int, int] | None:
    """(mã_chi_nhánh, năm, tháng) suy từ tên file; None nếu không khớp quy ước."""
    for m in RE_TEN.finditer(Path(ten_file).stem):
        thang = int(m.group(2))
        if 1 <= thang <= 12:
            return m.group(1).upper(), int(m.group(3)), thang
    return None


def la_so_ban_hang(cot) -> bool:
    """Nhận diện theo cột — bảng kê không bao giờ có cặp DebitAccount2/Amount3."""
    return {"DebitAccount2", "CreditAccount2", "Amount3"} <= set(cot)


def chuan_hoa(raw: pd.DataFrame) -> pd.DataFrame:
    """Chỉ giữ cột cần, ép kiểu ổn định (chuỗi giữ số 0 đầu, số về float, ngày về datetime)."""
    thieu = [c for c in COT_BAT_BUOC if c not in raw.columns]
    if thieu:
        raise KhongPhaiSoBanHang("Không phải sổ chi tiết bán hàng — thiếu cột: " + ", ".join(thieu))
    df = pd.DataFrame(index=raw.index)
    for c in COT_CHUOI:
        s = raw[c] if c in raw.columns else pd.Series(None, index=raw.index, dtype="object")
        df[c] = s.astype("string").str.strip().astype("object")
    df["DocDate"] = pd.to_datetime(raw["DocDate"], errors="coerce")
    for c in COT_SO:
        s = raw[c] if c in raw.columns else 0
        df[c] = pd.to_numeric(s, errors="coerce").fillna(0.0).astype(float)
    return df.reset_index(drop=True)


def doc_so_ban_hang(path: str) -> tuple[pd.DataFrame, MetaSoBanHang]:
    meta = suy_branch_ky(path)
    if meta is None:
        raise KhongPhaiSoBanHang(f"Không suy được chi nhánh/kỳ từ tên file: {Path(path).name}")
    try:
        raw = pd.read_excel(path, sheet_name="Table1", dtype=str, engine="calamine")
    except Exception:  # noqa: BLE001 (calamine thiếu / file lạ -> engine mặc định)
        raw = pd.read_excel(path, sheet_name="Table1", dtype=str)
    df = chuan_hoa(raw)
    ma, nam, thang = meta
    # Tên file nói một kỳ, ngày chứng từ nói kỳ khác -> nạp nhầm file, KHÔNG đoán.
    ngay = df["DocDate"].dropna()
    if len(ngay):
        pho_bien = (ngay.dt.year * 100 + ngay.dt.month).mode().iloc[0]
        if int(pho_bien) != nam * 100 + thang:
            raise KhongPhaiSoBanHang(
                f"{Path(path).name}: tên file ghi kỳ {thang:02d}/{nam} nhưng chứng từ thuộc "
                f"kỳ {int(pho_bien) % 100:02d}/{int(pho_bien) // 100}")
    return df, MetaSoBanHang(ma, nam, thang)
