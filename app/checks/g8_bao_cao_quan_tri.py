"""Nhóm 8 — Sẵn sàng cho Báo cáo quản trị (khoản mục chi phí & bộ phận).

Báo cáo quản trị của kế toán tổng hợp phân loại lại chi phí theo KHOẢN MỤC (KMCP)
và BỘ PHẬN. Dòng chi phí thiếu hai trục này sẽ rơi khỏi báo cáo — chính là "chênh
lệch" mà kế toán phải dò tay trong sheet CHECK (Bravo vs Tổng hợp). Nhóm này bắt
nguyên nhân đó ngay trên file Bravo, trước khi chênh lệch xuất hiện.

Đúng luật "đừng cảnh báo từ sự vắng mặt của bằng chứng" (xem C4.1, Nhóm 7): chỉ bật
khi công ty THẬT SỰ dùng khoản mục/bộ phận. C8.1 chỉ soi khi kỳ có dòng chi phí đã
điền khoản mục; C8.2 tự suy theo TỪNG nhóm TK cấp 1 — nhóm nào có dòng đã điền bộ
phận thì dòng trống trong nhóm ấy mới là thiếu sót, nên 621 (NVL trực tiếp, không
phân bổ bộ phận) tự động đứng ngoài.

Không đụng Tab A (16 bước khóa sổ) — đây là chất lượng dữ liệu cho báo cáo, khác
trục với các bước khóa sổ; Nhóm 8 chỉ hiện ở Tab B.
"""
import pandas as pd

from .base import VANG, BoiCanh, CheckResult, bat_dau, tao_ket_qua

NHOM = "G8"
# Đúng phạm vi các TK mà sheet CHECK của kế toán đối chiếu.
TK_BCQT = ("621", "622", "627", "635", "641", "642", "515", "711", "811")


def _trong(s: pd.Series) -> pd.Series:
    t = s.astype("string").str.strip()
    return t.isna() | t.eq("") | t.str.upper().eq("NULL")


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    kq = []
    la_cp = bat_dau(df["DebitAccount"], *TK_BCQT)

    # --- C8.1: thiếu mã khoản mục ---
    thieu_km = la_cp & _trong(df["ExpenseCatgCode"])
    co_dung_km = bool((la_cp & ~_trong(df["ExpenseCatgCode"])).any())
    ct81 = df[thieu_km] if co_dung_km else df.iloc[0:0]
    kq.append(tao_ket_qua(ct81, "C8.1", "Chi phí thiếu mã khoản mục (KMCP)", NHOM, VANG,
                          "Dòng chi phí không có mã khoản mục — sẽ rơi khỏi báo cáo quản trị theo khoản mục",
                          ghi_chu="" if co_dung_km else "Kỳ này không dùng khoản mục chi phí — không áp dụng"))

    # --- C8.2: thiếu bộ phận, tự suy theo nhóm TK cấp 1 ---
    tk3 = df["DebitAccount"].astype("string").str.strip().str[:3]
    trong_dept = _trong(df["DeptName"])
    nhom_co_dept = set(tk3[la_cp & ~trong_dept].dropna())
    thieu_dept = la_cp & trong_dept & tk3.isin(nhom_co_dept)
    kq.append(tao_ket_qua(df[thieu_dept], "C8.2", "Chi phí thiếu bộ phận (theo nhóm TK có dùng)",
                          NHOM, VANG,
                          "Dòng chi phí thuộc nhóm TK có phân bổ bộ phận nhưng bỏ trống bộ phận"
                          " — sẽ rơi khỏi báo cáo theo bộ phận",
                          ghi_chu="Chỉ xét nhóm TK cấp 1 mà kỳ này có dòng đã điền bộ phận"))

    # --- C8.3: thống kê tổng hợp chi phí theo khoản mục × TK (cột "Bravo" sạch) ---
    sub = df[la_cp].copy()
    if len(sub):
        sub["TK"] = tk3[la_cp]
        sub["ma_khoan_muc"] = sub["ExpenseCatgCode"].astype("string").str.strip()
        sub["ten_khoan_muc"] = sub["ExpenseCatgName"].astype("string").str.strip()
        bang = (sub.groupby(["TK", "ma_khoan_muc", "ten_khoan_muc"], dropna=False)
                .agg(so_dong=("Amount", "size"), tong=("Amount", "sum"))
                .reset_index().sort_values(["TK", "tong"], ascending=[True, False]))
    else:
        bang = pd.DataFrame(columns=["TK", "ma_khoan_muc", "ten_khoan_muc", "so_dong", "tong"])
    kq.append(CheckResult("C8.3", "Tổng hợp chi phí theo khoản mục × tài khoản", NHOM, VANG,
                          bang.reset_index(drop=True), la_thong_ke=True))
    return kq
