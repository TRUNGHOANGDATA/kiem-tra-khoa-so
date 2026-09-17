"""Nhóm 6 — Thống kê & soát xét (không phải lỗi).

C6.7/C6.8 (Đợt 3) nêu chỗ ĐÁNG NHÌN trong sổ, không chứng minh được sai — nên để
THỐNG KÊ, không kéo kết luận khóa sổ.

Ngưỡng lấy từ file 8 chi nhánh thật 08/2026, không phải chọn cho đẹp:
  C6.7  Q3 + 30·IQR của chính tài khoản, nhóm ≥ 30 dòng, tối đa 5 dòng mỗi TK
        -> 23–50 dòng/chi nhánh.
  C6.8  cặp cấp 1 xuất hiện ≤ 2 lần -> 24–66 cặp mỗi chi nhánh.

Hai rule cùng Đợt 3 đã BỎ sau khi đo trên dữ liệu thật:
  C4.7 "xuất 155/156 không về 632" — 421–2.281 dòng/chi nhánh, toàn hợp lệ (xuất
       NVL cho sản xuất Nợ 621, điều chuyển kho 152/155/156, thiếu hụt 338).
  C6.6 "bút toán dồn ngày cuối kỳ" — sau khi loại kết chuyển, ngày cuối chiếm
       4–9% số dòng (trung bình ngày của tháng ≈ 4%) và 8–18% giá trị: không có
       sức phân biệt. Chỉ có nghĩa khi so với CHÍNH chi nhánh đó ở kỳ trước (Đợt 4).
"""
import pandas as pd

from .base import XANH, BoiCanh, CheckResult, so_phat_sinh_tai_khoan

NHOM = "G6"
TOP_N = 50
# C6.7 — "gấp N lần TRUNG VỊ" đã thử và BỎ: tài khoản lệch phải như 1331 (thuế đầu
# vào) có trung vị 19.704đ nên mọi hóa đơn lớn đều thành "gấp 1.500 lần" — cả 50 dòng
# của A08 đều là 1331, vô dụng. Dùng Q3 + k·IQR: ngưỡng tự co giãn theo độ phân tán
# của chính tài khoản. k=30 -> 41–223 dòng/chi nhánh trên dữ liệu thật.
HE_SO_IQR = 30
TOI_THIEU_DONG_NHOM = 30
TOI_DA_MOI_TK = 5          # một tài khoản không được chiếm hết danh sách
# Bút toán kết chuyển/tổng hợp cuối kỳ: luôn là khoản lớn nhất của tài khoản và luôn
# chỉ xuất hiện 1–2 lần mỗi kỳ — để lại thì C6.7/C6.8 toàn nhắc chuyện đương nhiên.
TK_KET_CHUYEN = ("154", "621", "622", "627", "632", "511", "515",
                 "641", "642", "711", "811", "911", "421")
# C6.8 — cặp định khoản gộp ở CẤP 1 (3 chữ số): 13881/33881 và 13882/33882 là cùng
# một nghiệp vụ 138/338, tách ra thì cặp nào cũng thành "hiếm".
CAP_DINH_KHOAN = 3
TOI_DA_HIEM = 2


def _tk(ma, ten, bang) -> CheckResult:
    return CheckResult(ma, ten, NHOM, XANH, bang.reset_index(drop=True), la_thong_ke=True)


def _gom(df, cot) -> pd.DataFrame:
    g = df.groupby(cot, dropna=False)["Amount"].agg(so_dong="size", tong="sum").reset_index()
    return g.sort_values("tong", ascending=False)


def _c67(df: pd.DataFrame) -> CheckResult:
    """Giao dịch lớn bất thường SO VỚI CHÍNH TÀI KHOẢN ĐÓ.

    Khác C6.1 (top theo số tuyệt đối): một khoản 50 triệu trên tài khoản mà mọi
    bút toán chỉ vài trăm nghìn không bao giờ lọt top toàn sổ, nhưng chính nó mới
    là chỗ đáng hỏi.
    """
    ten = "Giao dịch đột biến so với mặt bằng tài khoản"
    cot = ["DocCode", "DocNo", "DocDate", "DebitAccount", "CreditAccount", "Amount",
           "nguong_tk", "Description"]
    if df.empty:
        return _tk("C6.7", ten, pd.DataFrame(columns=cot))
    tk = df["DebitAccount"].fillna("").astype(str).str.strip()
    g = df.assign(_tk=tk).groupby("_tk")["Amount"]
    q1, q3, so_dong = (g.transform(lambda s: s.quantile(.25)),
                       g.transform(lambda s: s.quantile(.75)), g.transform("size"))
    iqr = q3 - q1
    nguong = q3 + HE_SO_IQR * iqr
    dat = ((so_dong >= TOI_THIEU_DONG_NHOM) & (iqr > 0) & (df["Amount"] > nguong)
           & ~_la_ket_chuyen(df))
    # Gán cột TRƯỚC rồi mới lọc: .assign() một Series lên frame RỖNG sẽ dựng lại
    # nguyên số dòng của Series (toàn NaN) — bẫy đã làm check báo nhầm 6 dòng.
    bat = df.assign(nguong_tk=nguong, _tk=tk)[dat].sort_values("Amount", ascending=False)
    bat = bat.groupby("_tk", sort=False).head(TOI_DA_MOI_TK).head(TOP_N)
    return _tk("C6.7", ten, bat[[c for c in cot if c in bat.columns]])


def _la_ket_chuyen(df: pd.DataFrame) -> pd.Series:
    """Cả hai vế đều là TK kết chuyển/tổng hợp cuối kỳ -> nghiệp vụ đương nhiên."""
    lay = lambda c: df[c].fillna("").astype(str).str.strip()
    return (lay("DebitAccount").str.startswith(TK_KET_CHUYEN)
            & lay("CreditAccount").str.startswith(TK_KET_CHUYEN))


def _c68(df: pd.DataFrame) -> CheckResult:
    """Cặp định khoản Nợ/Có hiếm gặp trong kỳ — nơi sai sót và gian lận hay nấp."""
    cot = ["cap_dinh_khoan", "so_lan", "tong", "vi_du_ct", "Description"]
    ten = f"Cặp định khoản hiếm gặp (≤ {TOI_DA_HIEM} lần trong kỳ)"
    if df.empty:
        return _tk("C6.8", ten, pd.DataFrame(columns=cot))
    lay = lambda c: df[c].fillna("").astype(str).str.strip().str[:CAP_DINH_KHOAN]
    cap = lay("DebitAccount") + "/" + lay("CreditAccount")
    dem = cap.value_counts()
    hiem = set(dem[dem <= TOI_DA_HIEM].index)
    sub = df.assign(cap_dinh_khoan=cap)[cap.isin(hiem) & ~_la_ket_chuyen(df)]
    if sub.empty:
        return _tk("C6.8", ten, pd.DataFrame(columns=cot))
    bang = (sub.groupby("cap_dinh_khoan")
            .agg(so_lan=("Amount", "size"), tong=("Amount", "sum"),
                 vi_du_ct=("DocNo", "first"), Description=("Description", "first"))
            .reset_index().sort_values("tong", ascending=False))
    return _tk("C6.8", ten, bang)


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    cols = ["DocNo", "DocDate", "DebitAccount", "CreditAccount", "Amount", "Description", "CreatedByName"]
    top = df.nlargest(TOP_N, "Amount")[[c for c in cols if c in df.columns]]

    theo_ngay = _gom(df, "DocDate").sort_values("DocDate")
    m, s = theo_ngay["so_dong"].mean(), theo_ngay["so_dong"].std(ddof=0)
    theo_ngay["bat_thuong"] = theo_ngay["so_dong"] > (m + 2 * s) if len(theo_ngay) > 1 else False

    return [
        _tk("C6.1", f"Top {TOP_N} giao dịch giá trị lớn", top),
        _tk("C6.2", "Phát sinh theo tài khoản", so_phat_sinh_tai_khoan(df).sort_values("ps_no", ascending=False)),
        _tk("C6.3", "Phát sinh theo loại chứng từ", _gom(df, "DocCode")),
        _tk("C6.4", "Phát sinh theo người lập", _gom(df, "CreatedByName")),
        _tk("C6.5", "Phân bố bút toán theo ngày", theo_ngay),
        _c67(df), _c68(df),
    ]
