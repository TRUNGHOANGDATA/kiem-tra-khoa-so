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
    "ItemCode": "Mã hàng", "ItemName": "Tên hàng", "Quantity9": "Số lượng",
    "UnitCost": "Đơn giá", "WarehouseName": "Kho",
    "don_gia": "Đơn giá suy ra", "don_gia_pho_bien": "Đơn giá phổ biến của mã hàng",
    "so_lan_xuat": "Số lần xuất trong kỳ",
    "chi_nhanh": "Chi nhánh", "ky": "Kỳ", "ket_luan": "Kết luận", "co_phat_sinh": "Có phát sinh",
    "ma_khoan_muc": "Mã khoản mục", "ten_khoan_muc": "Tên khoản mục",
    "so_do": "Nghiêm trọng", "so_vang": "Cảnh báo",
    "so_chua_lam": "Bước chưa làm", "so_can_ra": "Bước cần rà",
    "tong_ps": "Tổng phát sinh", "cac_file": "Nguồn dữ liệu",
}
# Cột canh phải & định dạng số — một danh sách duy nhất cho cả giao diện lẫn Excel.
COT_SO_HIEN_THI = ("Amount", "ps_no", "ps_co", "net", "tong", "so_dong",
                   "thue_vao_1331", "thue_ra_33311", "UnitCost", "Quantity9",
                   "don_gia", "don_gia_pho_bien", "so_lan_xuat", "tong_ps",
                   "so_do", "so_vang", "so_chua_lam", "so_can_ra")
# Cột số CÓ PHẦN THẬP PHÂN — làm tròn 0 chữ số ở đây là nói sai sự thật: số lượng
# 0,059 in ra "0" đọc đúng thành "không có số lượng", ngược hẳn với dòng đang được
# nêu. Cột Quantity9 của Bravo mang tới 9 chữ số thập phân (xem fmt_sl).
COT_SO_LE = ("Quantity9",)


def ten_cot(cot) -> list[str]:
    """Nhãn hiển thị của một dãy tên cột (giữ nguyên nếu chưa đặt tên tiếng Việt)."""
    return [TEN_COT.get(c, c) for c in cot]


@dataclass
class BoiCanh:
    ky_thang: int
    ky_nam: int
    # Lỗ lũy kế đầu kỳ (dư đầu Nợ − Có của 421x) từ CĐPS; None = CHƯA nhập CĐPS.
    # Dương = có lỗ lũy kế; dùng ở C7.6 để chỉ đòi 8211 khi lãi kỳ > lỗ lũy kế.
    lo_luy_ke_dau: float | None = None


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


def fmt_sl(x: float) -> str:
    """Số lượng — giữ phần thập phân, ngăn cách kiểu Việt Nam (1.234,567).

    fmt_so làm tròn 0 chữ số thập phân, nên số lượng 0,16 in ra thành "SL 0" —
    đọc đúng thành "không có số lượng", tức là ngược hẳn với điều kiện đang được
    báo ("có số lượng nhưng chưa có giá trị"). Cột Quantity9 của Bravo mang tới
    9 chữ số thập phân; ở đây in đủ 9 rồi cắt các số 0 thừa, nên số nguyên vẫn
    hiện gọn ("10") còn số lẻ hiện đúng ("0,16" / "2,429").
    """
    if pd.isna(x):
        return ""
    s = f"{x:,.9f}".rstrip("0").rstrip(".")
    nguyen, _, le = s.partition(".")
    nguyen = nguyen.replace(",", ".")
    return f"{nguyen},{le}" if le else nguyen
