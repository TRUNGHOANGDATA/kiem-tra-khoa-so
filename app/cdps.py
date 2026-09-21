"""Đọc Bảng cân đối số phát sinh (CĐPS) — bổ sung SỐ DƯ ĐẦU KỲ mà bảng kê chứng từ
không có (vd lỗ lũy kế 421x để C7.6 loại trừ đúng).

File nguồn: 1 sheet `Table1`, header dòng đầu, cột tiếng Anh. `BranchCode` để trống
nên chi nhánh + kỳ suy từ TÊN FILE theo quy ước `A08 082026 ...` (mã CN + MMYYYY)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# mã chi nhánh (chữ + số) + khoảng trắng + MMYYYY ở đầu tên file
RE_TEN = re.compile(r"^\s*([A-Za-z]+\d+)\s+(\d{2})(\d{4})\b")

# Cột số dùng để phát hiện CĐPS đổi (tên/level đổi không phải "sổ đổi").
COT_SO_SS = ("du_dau_no", "du_dau_co", "ps_no", "ps_co", "du_cuoi_no", "du_cuoi_co")
NGUONG_LECH = 0.5     # đồng — dưới mức này là làm tròn


def so_sanh(df_cu: pd.DataFrame, df_moi: pd.DataFrame, nguong: float = NGUONG_LECH) -> dict | None:
    """Hai bảng CĐPS khác nhau ở đâu: thêm / mất / đổi theo mã TK. None = y hệt hoặc
    chưa có bản cũ để so.

    Thuần DataFrame nên dùng được cho CẢ hai đường: "bản sắp nạp vs bản đang lưu"
    (trước khi ghi đè) và "bản đang lưu vs bản đã đóng băng lúc chốt sổ".

    CỘNG theo mã tài khoản chứ không `set_index` thẳng: CĐPS thật có mã LẶP (A01 có
    6222 và 8118 mỗi mã 2 dòng), set_index xong `.loc` trả về Series và float() nổ —
    từng làm chết cả nút "Nạp lại CĐPS" (commit 64dbbf9).
    """
    if df_cu is None or df_moi is None or df_cu.empty:
        return None
    khoa = lambda d: (d.assign(_a=d["account"].fillna("").astype(str).str.strip())
                      .groupby("_a")[list(COT_SO_SS)].sum().astype(float))
    a, b = khoa(df_cu), khoa(df_moi)
    them = sorted(set(b.index) - set(a.index))
    bot = sorted(set(a.index) - set(b.index))
    dong = []
    for tk in sorted(set(a.index) & set(b.index)):
        lech = {c: (float(a.loc[tk, c]), float(b.loc[tk, c])) for c in COT_SO_SS
                if abs(float(a.loc[tk, c]) - float(b.loc[tk, c])) > nguong}
        if lech:
            dong.append({"account": tk, "kieu": "đổi",
                         **{f"{c}_cu": v[0] for c, v in lech.items()},
                         **{f"{c}_moi": v[1] for c, v in lech.items()},
                         "cot": ", ".join(lech)})
    dong += [{"account": tk, "kieu": "thêm", "cot": ""} for tk in them]
    dong += [{"account": tk, "kieu": "mất", "cot": ""} for tk in bot]
    if not dong:
        return None
    return {"so_doi": len(dong) - len(them) - len(bot),
            "so_them": len(them), "so_bot": len(bot), "dong": dong}

# tên chuẩn nội bộ -> tên cột nguồn
COT_NGUON = {
    "account": "Account", "ten": "AccountName",
    "du_dau_no": "DebitBal1", "du_dau_co": "CreditBal1",
    "ps_no": "DebitAmount", "ps_co": "CreditAmount",
    "du_cuoi_no": "DebitBal2", "du_cuoi_co": "CreditBal2",
    "is_group": "IsGroup", "level": "Level",
}
COT_SO = ("du_dau_no", "du_dau_co", "ps_no", "ps_co", "du_cuoi_no", "du_cuoi_co")


class KhongPhaiCdps(Exception):
    """File không phải CĐPS hợp lệ (thiếu cột chuẩn) hoặc tên file không suy được kỳ."""


@dataclass
class MetaCdps:
    ma: str
    nam: int
    thang: int


def suy_branch_ky(ten_file: str) -> tuple[str, int, int] | None:
    """(mã_chi_nhánh, năm, tháng) suy từ tên file; None nếu không khớp quy ước."""
    m = RE_TEN.match(Path(ten_file).name)
    if not m:
        return None
    thang = int(m.group(2))
    if not 1 <= thang <= 12:
        return None
    return m.group(1).upper(), int(m.group(3)), thang


def _so(s: pd.Series) -> pd.Series:
    lam_sach = s.astype(str).str.replace(",", "", regex=False).str.strip().replace("", "0")
    return pd.to_numeric(lam_sach, errors="coerce").fillna(0.0)


def doc_cdps(path: str) -> tuple[pd.DataFrame, MetaCdps]:
    """Đọc CĐPS -> (DataFrame chuẩn hóa, MetaCdps). Ném KhongPhaiCdps nếu tên file
    không suy được kỳ hoặc thiếu cột chuẩn."""
    meta = suy_branch_ky(path)
    if meta is None:
        raise KhongPhaiCdps(f"Không suy được chi nhánh/kỳ từ tên file: {Path(path).name}")
    raw = pd.read_excel(path, sheet_name="Table1", dtype=str)
    thieu = [src for src in COT_NGUON.values() if src not in raw.columns]
    if thieu:
        raise KhongPhaiCdps("Không phải CĐPS — thiếu cột: " + ", ".join(thieu))

    df = pd.DataFrame()
    df["account"] = raw["Account"].fillna("").astype(str).str.strip()
    df["ten"] = raw["AccountName"].fillna("").astype(str).str.strip()
    for k in COT_SO:
        df[k] = _so(raw[COT_NGUON[k]])
    df["is_group"] = raw["IsGroup"].astype(str).str.strip().str.lower().isin(("true", "1"))
    df["level"] = pd.to_numeric(raw["Level"], errors="coerce").fillna(-1).astype(int)
    ma, nam, thang = meta
    return df, MetaCdps(ma, nam, thang)
