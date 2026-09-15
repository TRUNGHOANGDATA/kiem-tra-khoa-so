"""Kiểu dữ liệu & tiện ích chung cho mọi bộ kiểm tra."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

DO, VANG, XANH = "do", "vang", "xanh"
THU_TU_MUC_DO = {DO: 0, VANG: 1, XANH: 2}
COT_CHUAN = ["DocNo", "DocDate", "DebitAccount", "CreditAccount", "Amount", "Description", "ly_do"]
NGUONG_CON_LAI = 0.5
TK_KHO = ("152", "153", "155", "156")

# Nhãn tiếng Việt cho mọi cột mà 29 bộ kiểm tra có thể sinh ra. Dùng chung cho bảng
# chi tiết trên giao diện và mọi sheet của báo cáo Excel — tên cột tiếng Anh của
# Bravo không được lọt ra trước mặt người dùng.
TEN_COT = {
    "DocCode": "Loại CT", "DocNo": "Số CT", "DocDate": "Ngày CT",
    "DebitAccount": "TK Nợ", "CreditAccount": "TK Có", "Amount": "Số tiền",
    "Description": "Diễn giải", "CreatedByName": "Người lập", "TaxCode": "Mã thuế",
    "ly_do": "Lý do",
    "TK": "Tài khoản", "ps_no": "Phát sinh Nợ", "ps_co": "Phát sinh Có",
    "net": "Chênh lệch Nợ − Có", "so_dong": "Số dòng", "tong": "Tổng tiền",
    "thue_vao_1331": "Thuế vào (1331)", "thue_ra_33311": "Thuế ra (33311)",
    "bat_thuong": "Bất thường",
}
# Cột canh phải & định dạng số — một danh sách duy nhất cho cả giao diện lẫn Excel.
COT_SO_HIEN_THI = ("Amount", "ps_no", "ps_co", "net", "tong", "so_dong",
                   "thue_vao_1331", "thue_ra_33311", "UnitCost", "Quantity9")


def ten_cot(cot) -> list[str]:
    """Nhãn hiển thị của một dãy tên cột (giữ nguyên nếu chưa đặt tên tiếng Việt)."""
    return [TEN_COT.get(c, c) for c in cot]


@dataclass
class BoiCanh:
    ky_thang: int
    ky_nam: int


@dataclass
class CheckResult:
    ma: str
    ten: str
    nhom: str
    muc_do: str
    chi_tiet: pd.DataFrame
    ghi_chu: str = ""
    la_thong_ke: bool = False

    @property
    def so_loi(self) -> int:
        return 0 if self.la_thong_ke else int(len(self.chi_tiet))

    @property
    def muc_do_thuc(self) -> str:
        if self.la_thong_ke or self.so_loi == 0:
            return XANH
        return self.muc_do


def bat_dau(s: pd.Series, *prefixes: str) -> pd.Series:
    return s.fillna("").astype(str).str.startswith(tuple(prefixes))


def loc_dong(df: pd.DataFrame, no: tuple[str, ...] | None = None,
             co: tuple[str, ...] | None = None) -> pd.DataFrame:
    m = pd.Series(True, index=df.index)
    if no:
        m &= bat_dau(df["DebitAccount"], *no)
    if co:
        m &= bat_dau(df["CreditAccount"], *co)
    return df[m]


def co_dong(df: pd.DataFrame, no=None, co=None) -> bool:
    return len(loc_dong(df, no, co)) > 0


def phat_sinh_theo_prefix(df: pd.DataFrame, prefix: str) -> tuple[float, float]:
    ps_no = df.loc[bat_dau(df["DebitAccount"], prefix), "Amount"].sum()
    ps_co = df.loc[bat_dau(df["CreditAccount"], prefix), "Amount"].sum()
    return float(ps_no), float(ps_co)


def so_phat_sinh_tai_khoan(df: pd.DataFrame) -> pd.DataFrame:
    no = df.groupby("DebitAccount")["Amount"].sum().rename("ps_no")
    co = df.groupby("CreditAccount")["Amount"].sum().rename("ps_co")
    bang = pd.concat([no, co], axis=1).fillna(0.0)
    bang.index.name = "TK"
    bang["net"] = bang["ps_no"] - bang["ps_co"]
    return bang.reset_index()


def tao_ket_qua(df_vi_pham: pd.DataFrame, ma: str, ten: str, nhom: str, muc_do: str,
                ly_do, ghi_chu: str = "") -> CheckResult:
    cols = [c for c in COT_CHUAN if c != "ly_do" and c in df_vi_pham.columns]
    ct = df_vi_pham[cols].copy()
    ct["ly_do"] = ly_do.values if isinstance(ly_do, pd.Series) else ly_do
    return CheckResult(ma, ten, nhom, muc_do, ct.reset_index(drop=True), ghi_chu)


def fmt_so(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")
