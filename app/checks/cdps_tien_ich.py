"""Tiện ích đọc Bảng cân đối số phát sinh (CĐPS) dùng chung cho G9 / G10 / G7.

Hai quy ước quan trọng:

1. **Chỉ cộng DÒNG LÁ** (`is_group` falsy). CĐPS Bravo có cả dòng nhóm (TK cha) lẫn
   dòng con; cộng cả hai là đếm trùng gấp đôi (xem `du_dau_theo_prefix` ở kho).
2. **Chưa nạp CĐPS thì check phải ĐỨNG NGOÀI**, không được báo "đạt". `khong_co_cdps`
   trả CheckResult rỗng + `la_thong_ke=True` nên không vào ô Đạt lẫn ô Lỗi — đúng luật
   "không kết luận từ thứ mình không có bằng chứng".
"""
from __future__ import annotations

import pandas as pd

from .base import CheckResult

# Sai số làm tròn cho mọi đẳng thức số dư (đồng).
NGUONG_DONG = 1.0

COT_SO = ("du_dau_no", "du_dau_co", "ps_no", "ps_co", "du_cuoi_no", "du_cuoi_co")
# Nhãn tiếng Việt cho bảng chi tiết lấy từ CĐPS (UI/Excel đọc tên cột trực tiếp).
NHAN_COT = {
    "account": "Tài khoản", "ten": "Tên tài khoản",
    "du_dau_no": "Dư đầu Nợ", "du_dau_co": "Dư đầu Có",
    "ps_no": "PS Nợ", "ps_co": "PS Có",
    "du_cuoi_no": "Dư cuối Nợ", "du_cuoi_co": "Dư cuối Có",
}


def co_cdps(ctx) -> bool:
    b = getattr(ctx, "cdps", None)
    return isinstance(b, pd.DataFrame) and not b.empty


def tk_that(cdps: pd.DataFrame) -> pd.Series:
    """Mặt nạ các dòng LÀ tài khoản thật (số hiệu bắt đầu bằng chữ số).

    CĐPS thật có dòng "Tổng cộng:" với số hiệu rỗng — không phải tài khoản, không được
    cộng vào tổng lẫn coi là TK cha.
    """
    return _ma(cdps).str.match(r"^\d")


def co_tk_con(cdps: pd.DataFrame) -> pd.Series:
    """Mặt nạ các dòng có ít nhất một tài khoản con xuất hiện trong chính bảng này."""
    ma = _ma(cdps)
    tap = {m for m in ma[tk_that(cdps)]}
    return ma.map(lambda m: bool(m) and any(o != m and o.startswith(m) for o in tap))


def dong_la(cdps: pd.DataFrame) -> pd.DataFrame:
    """Các dòng được PHÉP CỘNG (không phải dòng tổng của những dòng khác trong bảng).

    Hai bẫy đã gặp trên CĐPS thật, quy tắc phải thỏa cả hai:

    1. `is_group=True` NHƯNG file không có dòng con nào (1388, 3388, 5111, 6221… —
       17 dòng ở A08). Loại chúng làm tổng hụt 236 triệu -> C9.1 báo nhầm "không cân".
    2. `is_group=False` NHƯNG lại có con (6272 có con 62721 ở A03/A04). Hai dòng là
       hai khoản RIÊNG; loại 6272 làm hụt 150.394.609 -> C9.3 báo nhầm "cha ≠ tổng con".

    => Chỉ loại khi dòng VỪA là dòng tổng (`is_group`) VỪA thật sự có dòng con.
    """
    if cdps.empty or "account" not in cdps.columns:
        return cdps
    nhom = (cdps["is_group"].fillna(0).astype(bool) if "is_group" in cdps.columns
            else pd.Series(False, index=cdps.index))
    return cdps[tk_that(cdps) & ~(nhom & co_tk_con(cdps))]


def _ma(df: pd.DataFrame) -> pd.Series:
    return df["account"].fillna("").astype(str).str.strip()


def theo_prefix(df: pd.DataFrame, *prefixes: str) -> pd.DataFrame:
    return df[_ma(df).str.startswith(tuple(prefixes))]


def loai(df: pd.DataFrame) -> pd.Series:
    """Chữ số đầu của số hiệu TK (loại 1..9)."""
    return _ma(df).str[:1]


def net(df: pd.DataFrame, cot_no: str, cot_co: str) -> pd.Series:
    return df[cot_no].fillna(0) - df[cot_co].fillna(0)


def bang_chi_tiet(df: pd.DataFrame, ly_do) -> pd.DataFrame:
    """Bảng chứng minh cho check dựa trên CĐPS — giữ nguyên cột CĐPS + cột ly_do."""
    cols = [c for c in NHAN_COT if c in df.columns]
    ct = df[cols].copy()
    ct["ly_do"] = ly_do.values if isinstance(ly_do, pd.Series) else ly_do
    return ct.rename(columns=NHAN_COT).reset_index(drop=True)


def du_net(ctx, *prefixes: str, cot: str = "du_cuoi") -> float:
    """Số dư net (Nợ − Có) của các TK lá khớp prefix; 0.0 khi chưa nạp CĐPS.

    `cot` = "du_dau" hoặc "du_cuoi". Dùng làm BẰNG CHỨNG cho C7.1–C7.3: có tài sản /
    nghĩa vụ trên số dư thì việc "kỳ này không thấy bút toán" mới là thiếu sót thật.
    """
    if not co_cdps(ctx):
        return 0.0
    sub = theo_prefix(dong_la(ctx.cdps), *prefixes)
    if sub.empty:
        return 0.0
    return float(net(sub, f"{cot}_no", f"{cot}_co").sum())


def khong_co_cdps(ma: str, ten: str, nhom: str, muc_do: str) -> CheckResult:
    """Chưa nạp CĐPS -> check đứng ngoài (không Đạt, không Lỗi)."""
    return CheckResult(ma, ten, nhom, muc_do, pd.DataFrame(),
                       ghi_chu="Chưa nạp CĐPS cho kỳ/chi nhánh này — không kiểm tra được",
                       la_thong_ke=True)
