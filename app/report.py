"""Xuất báo cáo kiểm tra khóa sổ ra Excel (xlsxwriter)."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from .checks import TEN_NHOM
from .checks.base import (COT_SO_LE, DO, VANG, XANH, CheckResult, cot_so_cua, doi_bool,
                          fmt_so, ten_cot)
from .loader import ThongTinFile
from .trang_thai import BuocKhoaSo, tinh_ket_luan

# Người dùng MÙ MÀU: mọi nhãn mức độ phải mang KÝ HIỆU riêng đứng trước; màu tô chỉ là
# lớp phụ trợ. Không dùng emoji hình tròn đỏ/vàng/lục: chúng chỉ khác nhau về sắc.
TEN_MUC_DO = {DO: "✕ Nghiêm trọng", VANG: "▲ Cảnh báo", XANH: "✓ Đạt"}
TEN_TRANG_THAI = {"da_lam": "✓ Đã làm", "chua_lam": "✕ CHƯA LÀM", "can_ra": "▲ Cần rà",
                  "khong_ap_dung": "– Không áp dụng", "tu_xac_nhan": "☐ Tự xác nhận"}
MAU = {DO: "#FFC7CE", VANG: "#FFEB9C", XANH: "#C6EFCE",
       "da_lam": "#C6EFCE", "chua_lam": "#FFC7CE", "can_ra": "#FFEB9C",
       "khong_ap_dung": "#EDEDED", "tu_xac_nhan": "#E7F0FA"}
# Ba mức kết luận của tinh_ket_luan — tô ở sheet so sánh chi nhánh.
MAU_KET_LUAN = {"chua_san_sang": "#FFC7CE", "can_ra_soat": "#FFEB9C", "san_sang": "#C6EFCE"}
# Nhãn thay đổi so với bản chốt — ký hiệu đứng trước cho người dùng MÙ MÀU.
NHAN_THAY_DOI = {"them": "＋ Thêm", "bot": "－ Bớt",
                 "sua_cu": "✎ Sửa — trước", "sua_moi": "✎ Sửa — sau"}
FONT = "Segoe UI"


def ten_sheet_an_toan(ten: str) -> str:
    return re.sub(r"[\[\]:*?/\\]", "-", ten)[:31]


def _ghi_bang(writer, ten_sheet, df: pd.DataFrame, fmt, dong_dau=0):
    goc = list(df.columns)                     # tên gốc: dùng để chọn định dạng số
    la_so = set(cot_so_cua(df))                # nhận diện theo KIỂU, xem base.cot_so_cua
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].dt.strftime("%d/%m/%Y")
    df = doi_bool(df)                          # "Có"/"Không" — xem app/checks/base.py
    df.columns = ten_cot(goc)
    df.to_excel(writer, sheet_name=ten_sheet, index=False, startrow=dong_dau)
    ws = writer.sheets[ten_sheet]
    for j, (c, nhan) in enumerate(zip(goc, df.columns)):
        ws.write(dong_dau, j, nhan, fmt["header"])
        if len(df):
            do_dai = df[nhan].astype("string").fillna("").str.len()
            rong = max(10, min(60, int(do_dai.quantile(0.9)) + 2))
        else:
            rong = 12
        dinh_dang = fmt["so_le"] if c in COT_SO_LE else fmt["so"] if c in la_so else None
        ws.set_column(j, j, rong, dinh_dang)
    ws.freeze_panes(dong_dau + 1, 0)
    if len(df):
        ws.autofilter(dong_dau, 0, dong_dau + len(df), len(df.columns) - 1)
    return ws


def _dinh_dang(wb) -> dict:
    fmt = {
        "header": wb.add_format({"bold": True, "font_color": "white", "bg_color": "#1F4E79",
                                 "font_name": FONT, "border": 1, "text_wrap": True, "valign": "vcenter"}),
        "so": wb.add_format({"num_format": "#,##0", "font_name": FONT}),
        # Số lượng giữ phần thập phân — xem COT_SO_LE.
        "so_le": wb.add_format({"num_format": "#,##0.#########", "font_name": FONT}),
        "tieu_de": wb.add_format({"bold": True, "font_size": 14, "font_color": "#1F4E79", "font_name": FONT}),
    }
    for md, mau in MAU.items():
        fmt[md] = wb.add_format({"bg_color": mau, "font_name": FONT, "border": 1})
    for muc, mau in MAU_KET_LUAN.items():
        fmt[muc] = wb.add_format({"bg_color": mau, "font_name": FONT, "border": 1})
    return fmt


def _sheet_tong_quan(writer, fmt, ten_sheet: str, tieu_de: str, ket_qua, trang_thai, thong_tin):
    loi = [r for r in ket_qua if not r.la_thong_ke]
    ket_luan = tinh_ket_luan(ket_qua, trang_thai)
    tq = pd.DataFrame([{
        "Mã": r.ma, "Nhóm": TEN_NHOM[r.nhom], "Kiểm tra": r.ten,
        "Số dòng vi phạm": r.so_loi, "Mức độ": TEN_MUC_DO[r.muc_do_thuc], "Ghi chú": r.ghi_chu,
    } for r in loi])
    ws = _ghi_bang(writer, ten_sheet, tq, fmt, dong_dau=4)
    ws.write(0, 0, tieu_de, fmt["tieu_de"])
    ws.write(1, 0, f"Nguồn: {thong_tin.ten} · {fmt_so(thong_tin.so_dong)} dòng"
                   f" · Tổng phát sinh {fmt_so(thong_tin.tong_ps)}")
    ws.write(2, 0, f"Kết luận: {ket_luan['cau_ket_luan']}"
                   f"  ·  ✕ {ket_luan['so_do']} nghiêm trọng"
                   f"  ·  ▲ {ket_luan['so_vang']} cảnh báo", fmt["tieu_de"])
    for i, r in enumerate(loi, start=5):
        ws.write(i, 4, TEN_MUC_DO[r.muc_do_thuc], fmt[r.muc_do_thuc])
    return ws


def _sheet_trang_thai(writer, fmt, ten_sheet: str, trang_thai):
    ts = pd.DataFrame([{"Bước": b.buoc, "Trạng thái": TEN_TRANG_THAI[b.trang_thai],
                        "Tóm tắt": b.tom_tat, "Mã check": b.ma_check} for b in trang_thai])
    ws = _ghi_bang(writer, ten_sheet, ts, fmt)
    for i, b in enumerate(trang_thai, start=1):
        ws.write(i, 1, TEN_TRANG_THAI[b.trang_thai], fmt[b.trang_thai])
    return ws


def xuat_bao_cao(ket_qua: list[CheckResult], trang_thai: list[BuocKhoaSo],
                 thong_tin: ThongTinFile, thu_muc_out: str, ten_hien: str | None = None) -> str:
    # ten_hien: tên hiển thị chi nhánh (quy đổi). Tên file & tab sheet vẫn theo MÃ GỐC
    # cho ngắn/ổn định; chỉ tiêu đề trong sheet mới dùng tên hiển thị cho người đọc.
    Path(thu_muc_out).mkdir(parents=True, exist_ok=True)
    ky_ten = thong_tin.ky.replace("/", "-")
    cn = f" - {ten_sheet_an_toan(thong_tin.chi_nhanh)}" if thong_tin.chi_nhanh else ""
    path = (Path(thu_muc_out) /
            f"Bao cao kiem tra khoa so{cn} - {ky_ten} - {datetime.now():%Y%m%d_%H%M}.xlsx")

    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        fmt = _dinh_dang(writer.book)
        nhan_cn = f" — CHI NHÁNH {ten_hien or thong_tin.chi_nhanh}" if thong_tin.chi_nhanh else ""
        _sheet_tong_quan(writer, fmt, "Tong quan",
                         f"BÁO CÁO KIỂM TRA KHÓA SỔ — KỲ {thong_tin.ky}{nhan_cn}",
                         ket_qua, trang_thai, thong_tin)
        _sheet_trang_thai(writer, fmt, "Trang thai khoa so", trang_thai)

        # --- Chi tiết từng check ---
        for r in ket_qua:
            if r.so_loi > 0 or r.la_thong_ke:
                _ghi_bang(writer, ten_sheet_an_toan(r.ma), r.chi_tiet, fmt)

        # --- Nhật ký ---
        nk = pd.DataFrame({"Thông điệp": thong_tin.nhat_ky or ["Không có cảnh báo khi đọc dữ liệu"]})
        _ghi_bang(writer, "Nhat ky xu ly", nk, fmt)
    return str(path)


def _sheet_danh_sach_loi(writer, fmt, ds) -> None:
    """Bảng PHẲNG: mỗi dòng = một (chi nhánh × check có lỗi).

    Bản tổng hợp cũ bắt người đọc nhảy qua 8 cặp tab để biết chi nhánh nào sai gì.
    Sheet này để gửi thẳng cho kế toán tổng hợp các chi nhánh: lọc cột "Chi nhánh"
    là ra đúng phần việc của mình. Chỉ lấy check THẬT SỰ có lỗi (bỏ thống kê).
    """
    hang = [{"Chi nhánh": ten_hien, "Kỳ": tt.ky, "Mã": r.ma, "Nhóm": TEN_NHOM[r.nhom],
             "Kiểm tra": r.ten, "Mức độ": TEN_MUC_DO[r.muc_do_thuc],
             "Số dòng vi phạm": r.so_loi, "Ghi chú": r.ghi_chu}
            for _, ten_hien, ket_qua, _, tt in ds
            for r in ket_qua if r.so_loi > 0 and not r.la_thong_ke]
    # Nặng trước: chi nhánh nào nhiều lỗi nghiêm trọng nhất đứng đầu.
    hang.sort(key=lambda h: (h["Mức độ"] != TEN_MUC_DO[DO], h["Chi nhánh"], h["Mã"]))
    bang = pd.DataFrame(hang, columns=["Chi nhánh", "Kỳ", "Mã", "Nhóm", "Kiểm tra",
                                       "Mức độ", "Số dòng vi phạm", "Ghi chú"])
    ws = _ghi_bang(writer, "Danh sach loi", bang, fmt, dong_dau=3)
    ws.write(0, 0, "DANH SÁCH LỖI & CẢNH BÁO THEO CHI NHÁNH", fmt["tieu_de"])
    ws.write(1, 0, f"{len(hang)} mục · lập lúc {datetime.now():%d/%m/%Y %H:%M}"
                   " · lọc cột “Chi nhánh” để lấy phần của từng đơn vị")
    for i, h in enumerate(hang, start=4):
        ws.write(i, 5, h["Mức độ"], fmt[DO if h["Mức độ"] == TEN_MUC_DO[DO] else VANG])


def _sheet_chi_tiet_gop(writer, fmt, ds) -> None:
    """Chi tiết từng dòng vi phạm, gom theo CHECK và gắn cột "Chi nhánh".

    Gom theo check chứ không theo chi nhánh vì Excel chỉ cho 255 sheet: 60 check × 8
    chi nhánh là vỡ, còn 60 sheet thì luôn vừa dù bao nhiêu chi nhánh. Đổi lại mỗi
    dòng phải tự khai thuộc chi nhánh nào.
    """
    gom: dict[str, list[pd.DataFrame]] = {}
    for _, ten_hien, ket_qua, _, _ in ds:
        for r in ket_qua:
            if r.so_loi > 0 and not r.la_thong_ke and len(r.chi_tiet):
                ct = r.chi_tiet.copy()
                ct.insert(0, "Chi nhánh", ten_hien)
                gom.setdefault(r.ma, []).append(ct)
    for ma, phan in gom.items():
        _ghi_bang(writer, ten_sheet_an_toan(ma), pd.concat(phan, ignore_index=True), fmt)


def xuat_tong_hop(don_vi, thu_muc_out: str) -> str:
    """Một workbook cho nhiều chi nhánh: sheet so sánh + tổng quan & 11 bước mỗi chi nhánh.

    `don_vi` là dãy (mã, tên_hiển_thị, ket_qua, trang_thai, thong_tin). Chi tiết từng
    dòng vi phạm KHÔNG vào đây: 30 check × N chi nhánh vượt giới hạn 255 sheet của
    Excel từ chi nhánh thứ chín, và mỗi chi nhánh đã có báo cáo riêng đầy đủ.

    Tên sheet Excel tối đa 31 ký tự và phải duy nhất — đặt theo MÃ GỐC (ngắn, chắc
    chắn khác nhau), rồi vẫn cắt và đánh số phòng mã dài. Tên hiển thị chỉ dùng ở
    cột "Chi nhánh" và tiêu đề sheet cho người đọc.
    """
    ds = list(don_vi)
    if not ds:
        raise ValueError("Không có chi nhánh nào để xuất tổng hợp")
    Path(thu_muc_out).mkdir(parents=True, exist_ok=True)
    ky_ten = ds[0][4].ky.replace("/", "-")
    path = (Path(thu_muc_out) /
            f"Bao cao tong hop {len(ds)} chi nhanh - {ky_ten} - {datetime.now():%Y%m%d_%H%M}.xlsx")

    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        fmt = _dinh_dang(writer.book)

        # --- So sánh các chi nhánh ---
        hang, muc = [], []
        for ma, ten_hien, ket_qua, trang_thai, tt in ds:
            kl = tinh_ket_luan(ket_qua, trang_thai)
            muc.append(kl["muc_do_ket_luan"])
            hang.append({"Chi nhánh": ten_hien, "Kỳ": tt.ky, "Kết luận": kl["cau_ket_luan"],
                         "Nghiêm trọng": kl["so_do"], "Cảnh báo": kl["so_vang"],
                         "Bước chưa làm": kl["so_chua_lam"], "Bước cần rà": kl["so_can_ra"],
                         "Số dòng": tt.so_dong, "Tổng phát sinh": tt.tong_ps,
                         "Nguồn dữ liệu": tt.ten})
        ws = _ghi_bang(writer, "Tong hop chi nhanh", pd.DataFrame(hang), fmt, dong_dau=3)
        ws.write(0, 0, f"TỔNG HỢP KIỂM TRA KHÓA SỔ — {len(ds)} CHI NHÁNH", fmt["tieu_de"])
        ws.write(1, 0, f"Kỳ {' · '.join(dict.fromkeys(tt.ky for *_, tt in ds))}"
                       f" · lập lúc {datetime.now():%d/%m/%Y %H:%M}")
        for i, m in enumerate(muc, start=4):
            ws.write(i, 2, hang[i - 4]["Kết luận"], fmt[m])

        # --- Danh sách lỗi phẳng (gửi kế toán tổng hợp các chi nhánh) ---
        _sheet_danh_sach_loi(writer, fmt, ds)

        # --- Từng chi nhánh ---
        da_dung: set[str] = set()
        for ma, ten_hien, ket_qua, trang_thai, tt in ds:
            goc = ten_sheet_an_toan(ma)     # tab sheet theo MÃ GỐC (duy nhất, ngắn)
            for ten_tq, ten_ts in (_cap_ten_sheet(goc, da_dung),):
                _sheet_tong_quan(writer, fmt, ten_tq,
                                 f"CHI NHÁNH {ten_hien} — KỲ {tt.ky}", ket_qua, trang_thai, tt)
                _sheet_trang_thai(writer, fmt, ten_ts, trang_thai)

        # --- Chi tiết dòng vi phạm, gom theo check, có cột Chi nhánh ---
        _sheet_chi_tiet_gop(writer, fmt, ds)
    return str(path)


def xuat_mot_check(ma: str, ten: str, chi_nhanh_ten: str, ky: str, df: pd.DataFrame,
                   thu_muc_out: str, *, muc_do: str = VANG, ghi_chu: str = "",
                   loc: str = "") -> str:
    """Xuất bảng chứng minh của MỘT check ra Excel — ngay từ bảng đang xem trên màn.

    Báo cáo đầy đủ đã có mọi check, nhưng khi kế toán đang soi đúng một cảnh báo thì
    thứ họ cần gửi đi là đúng bảng đó. Tên file mang mã check + chi nhánh để không đè
    nhau khi xuất nhiều cái liên tiếp.
    """
    Path(thu_muc_out).mkdir(parents=True, exist_ok=True)
    path = (Path(thu_muc_out) /
            f"{ten_sheet_an_toan(ma)} - {ten_sheet_an_toan(chi_nhanh_ten)}"
            f" - {ky.replace('/', '-')} - {datetime.now():%Y%m%d_%H%M}.xlsx")
    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        fmt = _dinh_dang(writer.book)
        ws = _ghi_bang(writer, ten_sheet_an_toan(ma), df, fmt, dong_dau=4)
        ws.write(0, 0, f"{ma} · {ten}", fmt["tieu_de"])
        ws.write(1, 0, f"Chi nhánh {chi_nhanh_ten} · kỳ {ky} · {fmt_so(len(df))} dòng"
                       f" · xuất lúc {datetime.now():%d/%m/%Y %H:%M}")
        ws.write(2, 0, TEN_MUC_DO.get(muc_do, ""), fmt.get(muc_do, fmt["tieu_de"]))
        if ghi_chu or loc:
            ws.write(3, 0, " · ".join(x for x in (ghi_chu, f'Đang lọc: "{loc}"' if loc else "") if x))
    return str(path)


def xuat_thay_doi(payload: dict, thu_muc_out: str) -> str:
    """Xuất "Thay đổi từ khi chốt" ra Excel — bằng chứng kiểm soát để lưu/gửi đi.

    `payload` là kết quả `api.thay_doi_tu_khi_chot`. Hai sheet phẳng, mỗi dòng tự mang
    tên chi nhánh: chứng từ (thêm/bớt/sửa) và chỉ số CĐPS (thêm/mất/đổi).
    Ký hiệu ＋ － ✎ đứng trước nhãn cho người dùng MÙ MÀU (xem TEN_MUC_DO).
    """
    Path(thu_muc_out).mkdir(parents=True, exist_ok=True)
    dv = payload.get("don_vi") or []
    ky_ten = (dv[0]["ky"].replace("/", "-") if dv else "khong-ky")
    path = (Path(thu_muc_out) /
            f"Thay doi tu khi chot - {ky_ten} - {datetime.now():%Y%m%d_%H%M}.xlsx")

    ct_rows, cd_rows = [], []
    for x in dv:
        chung = {"Chi nhánh": x["chi_nhanh_ten"], "Kỳ": x["ky"],
                 "Chốt lúc": x["thoi_diem_chot"]}
        c = x["chung_tu"]
        for loai, ds in (("them", c["them"]), ("bot", c["bot"])):
            for r in ds:
                ct_rows.append({**chung, "Thay đổi": NHAN_THAY_DOI[loai],
                                "Số chứng từ": f'{r.get("DocCode", "")}·{r.get("DocNo", "")}', **r})
        for s in c["sua"]:
            for loai, ds in (("sua_cu", s["dong_cu"]), ("sua_moi", s["dong_moi"])):
                for r in ds:
                    ct_rows.append({**chung, "Thay đổi": NHAN_THAY_DOI[loai],
                                    "Số chứng từ": s["so_ct"], **r})
        cd = x.get("cdps")
        if not x["co_cdps_chot"]:
            cd_rows.append({**chung, "Tài khoản": "—", "Thay đổi": "– Chưa có mốc",
                            "Cột lệch": "Bản chốt này không kèm CĐPS — không đối chiếu được"})
        elif cd:
            for r in cd["dong"]:
                cd_rows.append({**chung, "Tài khoản": r["account"],
                                "Thay đổi": {"đổi": "✎ Đổi", "thêm": "＋ Thêm",
                                             "mất": "－ Mất"}[r["kieu"]],
                                "Cột lệch": r.get("cot", ""),
                                **{k: v for k, v in r.items()
                                   if k.endswith(("_cu", "_moi"))}})

    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        fmt = _dinh_dang(writer.book)
        ws = _ghi_bang(writer, "Chung tu thay doi", pd.DataFrame(ct_rows), fmt, dong_dau=3)
        ws.write(0, 0, "CHỨNG TỪ ĐÃ ĐỔI KỂ TỪ KHI CHỐT SỔ", fmt["tieu_de"])
        ws.write(1, 0, f'{payload.get("tom_tat", {}).get("ct_them", 0)} chứng từ thêm · '
                       f'{payload.get("tom_tat", {}).get("ct_bot", 0)} bớt · '
                       f'{payload.get("tom_tat", {}).get("ct_sua", 0)} bị sửa'
                       f'  ·  lập lúc {datetime.now():%d/%m/%Y %H:%M}')
        ws = _ghi_bang(writer, "CDPS thay doi", pd.DataFrame(cd_rows), fmt, dong_dau=3)
        ws.write(0, 0, "CHỈ SỐ CĐPS ĐÃ ĐỔI KỂ TỪ KHI CHỐT SỔ", fmt["tieu_de"])
        ws.write(1, 0, f'{payload.get("tom_tat", {}).get("tk_doi", 0)} tài khoản thay đổi')
    return str(path)


def _cap_ten_sheet(goc: str, da_dung: set[str]) -> tuple[str, str]:
    """Cặp tên sheet (tổng quan, 11 bước) duy nhất cho một chi nhánh.

    Hậu tố chiếm chỗ trước khi cắt: " - TQ" dài 5 ký tự nên phần gốc chỉ còn 26,
    và hai chi nhánh trùng 26 ký tự đầu được đánh số để Excel không từ chối ghi.
    """
    for n in range(1, 1000):
        so = "" if n == 1 else f" ({n})"
        than = goc[:31 - 5 - len(so)] + so
        tq, ts = f"{than} - TQ", f"{than} - KS"
        if tq not in da_dung:
            da_dung.update((tq, ts))
            return tq, ts
    raise ValueError(f"Không đặt được tên sheet duy nhất cho chi nhánh {goc}")
