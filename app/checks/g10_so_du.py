"""Nhóm 10 — Tính chất số dư cuối kỳ trên CĐPS.

Lớp phát hiện mạnh thứ hai của nghề (sau toàn vẹn CĐPS): nhìn CHIỀU số dư là ra ngay
sai sót mà nhìn phát sinh không thấy. Nguồn: hướng dẫn soát CĐPS (Đức Minh, MISA) và
bảng nhận diện rủi ro theo tài khoản (htttdn).

Phân mức theo sức mạnh bằng chứng:
  ĐỎ   — không thể đúng trong thực tế: quỹ/kho âm, hao mòn dư Nợ, nguyên giá dư Có.
  VÀNG — bất thường cần rà: dư ngược chiều ngoài nhóm lưỡng tính, ứng trước 131/331,
         khoản chờ xử lý 1381/3381 MỚI phát sinh trong kỳ.
  THỐNG KÊ — chỉ để soát: phải thu/phải trả khác (1388/3388) chiếm tỷ trọng lớn,
         khoản chờ xử lý 1381/3381 TỒN từ kỳ trước.

Chưa nạp CĐPS -> cả nhóm đứng ngoài, KHÔNG báo "đạt" giả.
"""
from __future__ import annotations

import pandas as pd

from . import cdps_tien_ich as cd
from .base import DO, VANG, BoiCanh, CheckResult, fmt_so

NHOM = "G10"

# TK được phép dư cả hai chiều (chốt với người dùng: TT200 + mở rộng cho DN nhiều chi
# nhánh). Sửa danh sách ở ĐÚNG MỘT CHỖ này.
TK_LUONG_TINH = ("131", "138", "141", "331", "333", "334", "338",
                 "412", "413", "421", "136", "336", "244", "344")

TK_TIEN = ("111", "112")
TK_KHO_SO_DU = ("152", "153", "155", "156", "157")
TK_HAO_MON = ("214",)
# TK ĐIỀU CHỈNH GIẢM tài sản (contra-asset): thuộc loại 1–2 nhưng dư CÓ mới là đúng
# bản chất — hao mòn 214, dự phòng 229 (và 129/139/159 của hệ TK cũ). Không loại ra thì
# C10.4 bắt nhầm, đã thấy với 2293 "Dự phòng phải thu khó đòi" ở A03/A04.
TK_DIEU_CHINH_GIAM = ("214", "229", "129", "139", "159")
TK_NGUYEN_GIA = ("211", "213")
TK_CHO_XU_LY = ("1381", "3381")
TK_PHAI_THU_TRA_KHAC = ("1388", "3388")
# C10.7: ngưỡng tỷ trọng trên tổng dư cuối Nợ (≈ tổng tài sản) để coi là "lớn".
TY_TRONG_LON = 0.05


def _bat(la: pd.DataFrame, dieu_kien: pd.Series, ma: str, ten: str, muc_do: str,
         mau_ly_do: str, ghi_chu: str = "") -> CheckResult:
    """Dựng CheckResult từ mặt nạ trên dòng lá; guard Series rỗng khi nối chuỗi."""
    bat = la[dieu_kien] if len(la) else la
    ly_do = "" if bat.empty else (
        mau_ly_do + " " + cd.net(bat, "du_cuoi_no", "du_cuoi_co").abs().map(fmt_so))
    return CheckResult(ma, ten, NHOM, muc_do, cd.bang_chi_tiet(bat, ly_do), ghi_chu=ghi_chu)


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    ten = {
        "C10.1": "Quỹ tiền mặt / ngân hàng âm (111/112 dư Có)",
        "C10.2": "Kho âm (15x dư Có)",
        "C10.3": "TSCĐ ngược chiều (214 dư Nợ / 211-213 dư Có)",
        "C10.4": "Số dư ngược chiều bản chất tài khoản",
        "C10.5": "Ứng trước còn treo (131 dư Có / 331 dư Nợ)",
        "C10.6": "Khoản chờ xử lý MỚI phát sinh chưa tất toán (1381/3381)",
        "C10.7": "Phải thu / phải trả khác chiếm tỷ trọng lớn",
        "C10.8": "Khoản chờ xử lý tồn từ kỳ trước (1381/3381)",
    }
    muc = {"C10.1": DO, "C10.2": DO, "C10.3": DO,
           "C10.4": VANG, "C10.5": VANG, "C10.6": VANG, "C10.7": VANG, "C10.8": VANG}
    if not cd.co_cdps(ctx):
        return [cd.khong_co_cdps(ma, t, NHOM, muc[ma]) for ma, t in ten.items()]

    la = cd.dong_la(ctx.cdps)
    ma_tk = la["account"].fillna("").astype(str).str.strip() if len(la) else pd.Series(dtype=str)
    du_no = cd.net(la, "du_cuoi_no", "du_cuoi_co") if len(la) else pd.Series(dtype=float)
    nguoc_no = du_no < -cd.NGUONG_DONG      # bản chất dư Nợ nhưng đang dư Có
    nguoc_co = du_no > cd.NGUONG_DONG       # bản chất dư Có nhưng đang dư Nợ

    la_tien = ma_tk.str.startswith(TK_TIEN)
    la_kho = ma_tk.str.startswith(TK_KHO_SO_DU)
    la_hao_mon = ma_tk.str.startswith(TK_HAO_MON)
    la_nguyen_gia = ma_tk.str.startswith(TK_NGUYEN_GIA)

    kq = [
        _bat(la, la_tien & nguoc_no, "C10.1", ten["C10.1"], DO,
             "Tiền dư Có (âm quỹ)", ghi_chu="Đối chiếu sổ quỹ / sao kê ngân hàng"),
        _bat(la, la_kho & nguoc_no, "C10.2", ten["C10.2"], DO,
             "Kho dư Có (xuất quá tồn)", ghi_chu="Đối chiếu bảng nhập–xuất–tồn"),
        _bat(la, (la_hao_mon & nguoc_co) | (la_nguyen_gia & nguoc_no), "C10.3", ten["C10.3"], DO,
             "Số dư ngược bản chất TSCĐ"),
    ]

    # C10.4 — quy tắc chung: loại 1–2 dư Có, loại 3–4 dư Nợ. Trừ nhóm lưỡng tính và
    # trừ các TK đã có check riêng ở trên để không báo trùng một lỗi hai lần.
    lt = ma_tk.str.startswith(TK_LUONG_TINH) | ma_tk.str.startswith(TK_DIEU_CHINH_GIAM)
    da_co_check = la_tien | la_kho | la_hao_mon | la_nguyen_gia
    lo = cd.loai(la) if len(la) else pd.Series(dtype=str)
    sai_chieu = ((lo.isin(("1", "2")) & nguoc_no) | (lo.isin(("3", "4")) & nguoc_co))
    kq.append(_bat(la, sai_chieu & ~lt & ~da_co_check, "C10.4", ten["C10.4"], VANG,
                   "Dư ngược bản chất tài khoản",
                   ghi_chu="Đã loại TK lưỡng tính: " + "/".join(TK_LUONG_TINH)))

    # C10.5 — ứng trước: khách trả trước (131 dư Có) / trả trước người bán (331 dư Nợ).
    ung_truoc = ((ma_tk.str.startswith("131") & nguoc_no)
                 | (ma_tk.str.startswith("331") & nguoc_co))
    kq.append(_bat(la, ung_truoc, "C10.5", ten["C10.5"], VANG,
                   "Ứng trước còn treo",
                   ghi_chu="Rà doanh thu/hóa đơn chưa ghi nhận & đối chiếu công nợ"))

    # C10.6 / C10.8 — thừa/thiếu chờ xử lý, TÁCH theo sức mạnh bằng chứng.
    #
    # Khoản MỚI phát sinh trong kỳ (dư đầu 0, dư cuối còn treo) là việc của chính kỳ
    # đang khóa -> VÀNG. Khoản TỒN từ kỳ trước là tồn đọng đã biết: TT200 đòi xử lý dứt
    # điểm trước khi lập BCTC NĂM, không phải trước mỗi lần khóa sổ tháng -> thống kê.
    #
    # Đo trên CĐPS thật 08/2026: cả 8 chi nhánh đều CHỈ có khoản tồn cũ (0 khoản mới),
    # số dư 3381 từ 184 triệu tới 1,74 tỷ — kể cả 5 chi nhánh kế toán tổng hợp đã xác
    # nhận OK và cả chi nhánh có dư NGƯỢC chiều (A08 dư Nợ 1,17 tỷ). Để nguyên một mức
    # VÀNG là kéo cả 8 xuống "cần rà soát" bất kể làm gì — đúng loại dương tính giả đã
    # sửa ở C4.1/C1.1. Tách ra thì răng vẫn còn: thừa/thiếu kiểm kê MỚI vẫn chặn.
    cho_xl = ma_tk.str.startswith(TK_CHO_XU_LY) & (du_no.abs() > cd.NGUONG_DONG)
    du_dau = cd.net(la, "du_dau_no", "du_dau_co") if len(la) else pd.Series(dtype=float)
    ton_cu = du_dau.abs() > cd.NGUONG_DONG
    kq.append(_bat(la, cho_xl & ~ton_cu, "C10.6", ten["C10.6"], VANG,
                   "Mới phát sinh trong kỳ, cuối kỳ còn treo",
                   ghi_chu="Chênh lệch kiểm kê phát sinh trong kỳ phải xử lý dứt điểm"
                           " trước khi khóa sổ"))
    r108 = _bat(la, cho_xl & ton_cu, "C10.8", ten["C10.8"], VANG,
                "Tồn từ kỳ trước, cuối kỳ còn treo",
                ghi_chu="Tồn đọng từ kỳ trước — TT200 đòi xử lý dứt điểm trước khi lập"
                        " BCTC năm, nên chỉ nêu để soát, không chặn khóa sổ tháng")
    r108.la_thong_ke = True

    # C10.7 — thống kê: 1388/3388 lớn so với tổng tài sản (nội dung thường không rõ).
    tong_ts = float(la["du_cuoi_no"].fillna(0).sum()) if len(la) else 0.0
    nguong = tong_ts * TY_TRONG_LON
    khac_lon = ma_tk.str.startswith(TK_PHAI_THU_TRA_KHAC) & (du_no.abs() > max(nguong, cd.NGUONG_DONG))
    r107 = _bat(la, khac_lon, "C10.7", ten["C10.7"], VANG,
                f"Dư lớn (> {TY_TRONG_LON:.0%} tổng dư Nợ = {fmt_so(nguong)})",
                ghi_chu="Chỉ để soát nội dung khoản phải thu/phải trả khác")
    r107.la_thong_ke = True
    kq.append(r107)
    kq.append(r108)
    return kq
