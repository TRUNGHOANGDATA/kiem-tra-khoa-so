"""Xuất báo cáo kiểm tra khóa sổ ra Excel (xlsxwriter)."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from .checks import TEN_NHOM
from .checks.base import DO, VANG, XANH, CheckResult, fmt_so
from .loader import ThongTinFile
from .trang_thai import BuocKhoaSo, tinh_ket_luan

TEN_MUC_DO = {DO: "Nghiêm trọng", VANG: "Cảnh báo", XANH: "Đạt"}
TEN_TRANG_THAI = {"da_lam": "Đã làm", "chua_lam": "CHƯA LÀM", "can_ra": "Cần rà", "khong_ap_dung": "Không áp dụng"}
MAU = {DO: "#FFC7CE", VANG: "#FFEB9C", XANH: "#C6EFCE",
       "da_lam": "#C6EFCE", "chua_lam": "#FFC7CE", "can_ra": "#FFEB9C", "khong_ap_dung": "#EDEDED"}
FONT = "Segoe UI"


def ten_sheet_an_toan(ten: str) -> str:
    return re.sub(r"[\[\]:*?/\\]", "-", ten)[:31]


def _ghi_bang(writer, ten_sheet, df: pd.DataFrame, fmt, dong_dau=0):
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].dt.strftime("%d/%m/%Y")
    df.to_excel(writer, sheet_name=ten_sheet, index=False, startrow=dong_dau)
    ws = writer.sheets[ten_sheet]
    for j, c in enumerate(df.columns):
        ws.write(dong_dau, j, c, fmt["header"])
        if len(df):
            do_dai = df[c].astype("string").fillna("").str.len()
            rong = max(10, min(60, int(do_dai.quantile(0.9)) + 2))
        else:
            rong = 12
        ws.set_column(j, j, rong, fmt["so"] if c in ("Amount", "ps_no", "ps_co", "net", "tong",
                                                          "thue_vao_1331", "thue_ra_33311") else None)
    ws.freeze_panes(dong_dau + 1, 0)
    if len(df):
        ws.autofilter(dong_dau, 0, dong_dau + len(df), len(df.columns) - 1)
    return ws


def xuat_bao_cao(ket_qua: list[CheckResult], trang_thai: list[BuocKhoaSo],
                 thong_tin: ThongTinFile, thu_muc_out: str) -> str:
    Path(thu_muc_out).mkdir(parents=True, exist_ok=True)
    ky_ten = thong_tin.ky.replace("/", "-")
    path = Path(thu_muc_out) / f"Bao cao kiem tra khoa so - {ky_ten} - {datetime.now():%Y%m%d_%H%M}.xlsx"

    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        wb = writer.book
        fmt = {
            "header": wb.add_format({"bold": True, "font_color": "white", "bg_color": "#1F4E79",
                                     "font_name": FONT, "border": 1, "text_wrap": True, "valign": "vcenter"}),
            "so": wb.add_format({"num_format": "#,##0", "font_name": FONT}),
            "tieu_de": wb.add_format({"bold": True, "font_size": 14, "font_color": "#1F4E79", "font_name": FONT}),
        }
        for md, mau in MAU.items():
            fmt[md] = wb.add_format({"bg_color": mau, "font_name": FONT, "border": 1})

        # --- Tổng quan ---
        loi = [r for r in ket_qua if not r.la_thong_ke]
        ket_luan = tinh_ket_luan(ket_qua, trang_thai)
        tq = pd.DataFrame([{
            "Mã": r.ma, "Nhóm": TEN_NHOM[r.nhom], "Kiểm tra": r.ten,
            "Số dòng vi phạm": r.so_loi, "Mức độ": TEN_MUC_DO[r.muc_do_thuc], "Ghi chú": r.ghi_chu,
        } for r in loi])
        ws = _ghi_bang(writer, "Tong quan", tq, fmt, dong_dau=4)
        ws.write(0, 0, f"BÁO CÁO KIỂM TRA KHÓA SỔ — KỲ {thong_tin.ky}", fmt["tieu_de"])
        ws.write(1, 0, f"File: {thong_tin.ten} · {fmt_so(thong_tin.so_dong)} dòng"
                       f" · Tổng phát sinh {fmt_so(thong_tin.tong_ps)}")
        ws.write(2, 0, f"Kết luận: {ket_luan['cau_ket_luan']}"
                       f"  ·  🔴 {ket_luan['so_do']}  🟡 {ket_luan['so_vang']}", fmt["tieu_de"])
        for i, r in enumerate(loi, start=5):
            ws.write(i, 4, TEN_MUC_DO[r.muc_do_thuc], fmt[r.muc_do_thuc])

        # --- Trạng thái khóa sổ ---
        ts = pd.DataFrame([{"Bước": b.buoc, "Trạng thái": TEN_TRANG_THAI[b.trang_thai],
                            "Tóm tắt": b.tom_tat, "Mã check": b.ma_check} for b in trang_thai])
        ws = _ghi_bang(writer, "Trang thai khoa so", ts, fmt)
        for i, b in enumerate(trang_thai, start=1):
            ws.write(i, 1, TEN_TRANG_THAI[b.trang_thai], fmt[b.trang_thai])

        # --- Chi tiết từng check ---
        for r in ket_qua:
            if r.so_loi > 0 or r.la_thong_ke:
                _ghi_bang(writer, ten_sheet_an_toan(r.ma), r.chi_tiet, fmt)

        # --- Nhật ký ---
        nk = pd.DataFrame({"Thông điệp": thong_tin.nhat_ky or ["Không có cảnh báo khi đọc dữ liệu"]})
        _ghi_bang(writer, "Nhat ky xu ly", nk, fmt)
    return str(path)
