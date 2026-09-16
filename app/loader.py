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
             "CurrencyCode", "CreatedByName", "CashFlowName", "ExpenseCatgName", "DeptName",
             "BranchCode", "Đơn vị", "ExpenseCatgCode"]
# Chi nhánh có thể nằm ở nhiều cột tùy cách xuất Bravo: "BranchCode" (file 08/2026:
# "A01"), hoặc cột tiếng Việt "Đơn vị" (file BC quản trị: VXHN/VXHO). Thử theo thứ tự
# ưu tiên, dùng cột đầu tiên CÓ giá trị. Một file có thể chứa nhiều chi nhánh, một chi
# nhánh có thể trải trên nhiều file — nên đơn vị suy từ giá trị cột này, không từ tên file.
COT_CHI_NHANH = ("BranchCode", "Đơn vị")
CHI_NHANH_KHONG_RO = "(không có mã chi nhánh)"


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
    chi_nhanh: str = ""
    # Mọi file đã góp dòng vào đơn vị này — một chi nhánh có thể được xuất làm nhiều lần.
    cac_file: list[str] = field(default_factory=list)


def doc_ngay(s: pd.Series) -> pd.Series:
    """Đọc cột ngày chứng từ, chấp nhận cả datetime thật, "dd/mm/yyyy" và "yyyy-mm-dd".

    Xuất Bravo bình thường mang datetime thật, nhưng chỉ cần lưu lại file một lần là
    ngày thành chuỗi "dd/mm/yyyy". Mặc định pandas đọc tháng trước -> "05/08/2026"
    hóa 08/05, cả kỳ bị suy sai mà không có một dòng cảnh báo nào.

    Không thể bật dayfirst cho toàn cột: pandas áp cờ này cho cả chuỗi bắt đầu bằng
    năm, biến "2026-08-05" thành 08/05 và "2026-08-20" thành NaT. Chuỗi năm-trước vốn
    không nhập nhằng, nên chỉ những giá trị còn lại mới cần dayfirst.
    """
    if pd.api.types.is_datetime64_any_dtype(s):
        return s
    txt = s.astype("string").str.strip()
    nam_truoc = txt.str.match(r"\d{4}[-/.]").fillna(False)
    return (pd.to_datetime(txt.where(nam_truoc), errors="coerce")
            .fillna(pd.to_datetime(txt.where(~nam_truoc), errors="coerce", dayfirst=True)))


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
    ngay = doc_ngay(df["DocDate"])
    hong_ngay = int(ngay.isna().sum() - pd.isna(df["DocDate"]).sum())
    if hong_ngay > 0:
        log.append(f"Cột DocDate: {hong_ngay} giá trị không phải ngày hợp lệ, đã để trống")
    df["DocDate"] = ngay
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
    if df.empty:
        raise ValueError("Bảng kê không có dòng dữ liệu nào để kiểm tra")
    thang, nam = xac_dinh_ky(df)
    ten = Path(path).name
    tt = ThongTinFile(path=path, ten=ten, ky=f"{thang:02d}/{nam}",
                      ky_thang=thang, ky_nam=nam, so_dong=len(df),
                      tong_ps=float(df["Amount"].sum()), nhat_ky=log,
                      chi_nhanh=mot_chi_nhanh(df), cac_file=[ten])
    return df, tt


def ma_chi_nhanh(df: pd.DataFrame) -> pd.Series:
    """Cột mã chi nhánh đã điền chỗ trống — dòng không có mã vẫn phải thuộc một đơn vị,
    nếu không chúng lặng lẽ biến mất khỏi mọi kiểm tra khi tách theo chi nhánh.

    Tự cắt khoảng trắng thay vì tin rằng chuan_hoa đã chạy: một mã toàn dấu cách
    lọt qua sẽ thành một chi nhánh mang nhãn rỗng — trên thanh chọn chi nhánh nó
    là một nút không có chữ, không cách nào biết đang xem sổ của ai.
    """
    for cot in COT_CHI_NHANH:
        if cot not in df.columns:
            continue
        s = df[cot].astype("string").str.strip()
        s = s.mask(s.isna() | s.eq("") | s.str.upper().eq("NULL"))
        if s.notna().any():
            return s.fillna(CHI_NHANH_KHONG_RO).astype("object")
    return pd.Series(CHI_NHANH_KHONG_RO, index=df.index, dtype="object")


def mot_chi_nhanh(df: pd.DataFrame) -> str:
    """Nhãn chi nhánh của một frame đã thuần nhất (rỗng nếu frame còn lẫn nhiều chi nhánh)."""
    ds = ma_chi_nhanh(df).unique()
    return str(ds[0]) if len(ds) == 1 else ""


def tach_theo_chi_nhanh(df: pd.DataFrame) -> list[tuple[str, pd.DataFrame]]:
    """Tách frame đã gộp thành từng đơn vị kế toán, sắp theo mã chi nhánh.

    Mỗi chi nhánh khóa sổ trên sổ của chính mình: 911 phải cân trong phạm vi một
    chi nhánh, kết chuyển 642 của chi nhánh này không bù được phần thiếu của chi
    nhánh kia. Vì vậy 30 bộ kiểm tra phải chạy trên từng frame con, không bao giờ
    trên frame đã gộp.
    """
    cn = ma_chi_nhanh(df)
    return [(ten, df[cn == ten].reset_index(drop=True)) for ten in sorted(cn.unique())]


def doc_nhieu_bang_ke(paths, on_file=None) -> list[tuple[pd.DataFrame, ThongTinFile]]:
    """Đọc nhiều file bảng kê -> danh sách (frame, thông tin) theo TỪNG CHI NHÁNH.

    Cùng một chi nhánh nằm ở hai file thì được gộp làm một đơn vị; một file chứa
    hai chi nhánh thì được tách làm hai. Đường dẫn trùng bị bỏ qua để bấm nhầm hai
    lần không nhân đôi phát sinh của cả chi nhánh.
    """
    khung, nhat_ky, nguon = [], [], {}
    da_doc: set[str] = set()
    for p in paths:
        khoa = os.path.normcase(os.path.abspath(p))
        if khoa in da_doc:
            nhat_ky.append(f"Bỏ qua file trùng: {Path(p).name}")
            continue
        da_doc.add(khoa)
        if on_file:
            on_file(Path(p).name)
        df, tt = doc_bang_ke(p)
        khung.append(df)
        nhat_ky += [f"{tt.ten}: {m}" for m in tt.nhat_ky]
        for cn in ma_chi_nhanh(df).unique():
            nguon.setdefault(str(cn), []).append((tt.ten, p))
    if not khung:
        raise ValueError("Chưa chọn file bảng kê nào")
    gop = pd.concat(khung, ignore_index=True) if len(khung) > 1 else khung[0]

    ds = []
    for cn, con in tach_theo_chi_nhanh(gop):
        thang, nam = xac_dinh_ky(con)
        goc = nguon.get(cn) or []
        ten_file = [t for t, _ in goc]
        duong_dan = [p for _, p in goc]
        ds.append((con, ThongTinFile(
            path=duong_dan[0] if duong_dan else "",
            ten=" + ".join(ten_file), ky=f"{thang:02d}/{nam}",
            ky_thang=thang, ky_nam=nam, so_dong=len(con),
            tong_ps=float(con["Amount"].sum()), nhat_ky=nhat_ky,
            chi_nhanh=cn, cac_file=list(ten_file))))
    return ds


def tim_file_excel(thu_muc: str) -> list[str]:
    """Mọi bảng kê trong thư mục, mới nhất trước — bỏ file tạm ~$ của Excel."""
    p = Path(thu_muc)
    if not p.is_dir():
        return []
    files = [f for f in p.glob("*.xls*") if not f.name.startswith("~$")]
    return [str(f) for f in sorted(files, key=os.path.getmtime, reverse=True)]


def tim_file_moi_nhat(thu_muc: str) -> str | None:
    ds = tim_file_excel(thu_muc)
    return ds[0] if ds else None
