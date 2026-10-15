"""Nhóm 3 — Thuế GTGT."""
import pandas as pd

from .base import VANG, XANH, BoiCanh, CheckResult, bat_dau, fmt_so, khoa_chung_tu, tao_ket_qua

NHOM = "G3"
TK_THUE = ("1331", "33311")
# GIAO DỊCH NỘI BỘ — nhận theo MÃ LOẠI GIAO DỊCH của Bravo, KHÔNG đoán theo số hiệu TK.
#   2303 — bán nội bộ (hóa đơn HD, chủ yếu Nợ 1368 / Có 5112)
#   2110 — điều chuyển nội bộ (chứng từ TL: 1388/1368, 5213/1368, 1521/1388…)
#
# Bán/điều chuyển trong cùng pháp nhân không phát sinh thuế GTGT đầu ra, nên "chứng từ
# thiếu 33311" ở đó không phải thiếu sót. Ngoài hai mã này mà thiếu 33311 là THIẾU VAT
# THẬT (kế toán tổng hợp chốt 2026-09-21).
#
# ĐỪNG XÓA 2110 DÙ NÓ ĐANG KHÔNG KHỚP DÒNG NÀO. Trên sổ 08/2026, trong miền C3.2 xét
# (53.314 dòng Có 511 + có mã thuế): 2303 khớp 645 dòng, 2110 khớp **0 dòng** — điều
# chuyển không ghi Có 511 (175 dòng mang mã 2110 toàn 1388/1368, 5213/1368, 1551/6322…,
# không dòng nào Có 511) nên chưa bao giờ lọt vào diện C3.2. Người dùng chốt 2026-09-21:
# "2110 chưa có nhưng tương lai sẽ có" — giữ lại theo yêu cầu nghiệp vụ, KHÔNG phải
# code chết, đừng dọn.
#
# Tiêu chí cũ `Nợ 136/336` SAI CẢ HAI CHIỀU. Đo trên sổ 08/2026, trong miền C3.2 xét:
# tiêu chí TK bắt 639 dòng, TransCode bắt đúng 639 dòng ấy CỘNG 6 dòng nội bộ hạch toán
# qua 1311/1388 mà tiêu chí TK bỏ lọt (A05 từ 5 dòng về 0). Chiều ngược lại, 1368 với mã
# giao dịch bán thường thì VẪN phải có thuế đầu ra — số hiệu TK không phải căn cứ.
# A01 (68) và A08 (15) không đổi: đó là thiếu VAT thật.
TRANSCODE_NOI_BO = ("2303", "2110")


def _noi_bo(df: pd.DataFrame) -> pd.Series:
    """Mặt nạ dòng thuộc giao dịch nội bộ. Thiếu cột TransCode -> KHÔNG loại dòng nào:
    thiếu bằng chứng "là nội bộ" thì phải soi tiếp, không được im lặng bỏ qua."""
    if "TransCode" not in df.columns:
        return pd.Series(False, index=df.index)
    return df["TransCode"].fillna("").astype(str).str.strip().isin(TRANSCODE_NOI_BO)


# Cột chứng minh của C3.2/C3.4 — đọc từ SỔ CHI TIẾT BÁN HÀNG, từng dòng hàng.
COT_SBH = ("DocCode", "DocNo", "DocDate", "TransCode", "DebitAccount2", "CreditAccount2",
           "CustomerName", "ItemCode", "ItemName", "Quantity", "UnitPrice",
           "Amount2", "Amount3", "Description")
NGUONG_KHOP = 1.0   # đồng — lệch tổng giữa sổ bán hàng và bảng kê dưới mức này là làm tròn


def _dong_thue_0(sbh: pd.DataFrame, mat_na_tk: pd.Series) -> pd.Series:
    """Dòng hàng trong diện mà THUẾ = 0 — tiêu chí chung của C3.2 và C3.4.

    - `Amount2 != 0`: hàng tặng/khuyến mại giá 0 không có doanh thu thì không có thuế
      để thiếu (A01 09/2026: 88 dòng, toàn UnitPrice 0).
    - Ngoài giao dịch nội bộ (TransCode 2303/2110 — bán/trả lại CHI NHÁNH, cùng pháp
      nhân). 2304/2112 là "Công ty nội bộ" = pháp nhân khác → VẪN phải có thuế.
    - KHÔNG xét TaxCode: dòng để trống mã thuế chính là dòng quên nhập VAT (A01 09/2026:
      6 dòng khách FOD, 74,4 tr — check cũ trên bảng kê bỏ lọt vì đòi TaxCode).
    """
    return mat_na_tk & sbh["Amount3"].eq(0) & sbh["Amount2"].ne(0) & ~_noi_bo(sbh)


def _tong(df, no, co, cot="Amount") -> float:
    m = bat_dau(df["DebitAccount"], no) & bat_dau(df["CreditAccount"], co)
    return float(df.loc[m, cot].sum())


def _lech_voi_bang_ke(df: pd.DataFrame, sbh: pd.DataFrame, m511: pd.Series, m521: pd.Series) -> str:
    """Lá chắn độ tươi: 4 tổng của sổ bán hàng phải bằng bảng kê (A01 09/2026 khớp đến
    từng đồng). Lệch = hai nguồn không cùng một lát cắt sổ → kết quả C3.2/C3.4 chưa đáng
    tin cho tới khi kết xuất lại cùng lúc (bài học CĐPS 21/09). Rỗng = khớp.

    Chỉ so trên CÙNG LOẠI chứng từ mà sổ bán hàng chứa (HD/TL): phiếu kế toán PK cũng có
    thể ghi Nợ 131/Có 511 nhưng không bao giờ lên sổ bán hàng — A01 08/2026 có
    PK2608-000026/28 (540.000) làm lệch giả nếu so cả bảng kê."""
    if "DocCode" in df.columns and len(sbh):
        loai = set(sbh["DocCode"].dropna().astype(str).str.strip())
        df = df[df["DocCode"].fillna("").astype(str).str.strip().isin(loai)]
    cap = [
        ("doanh thu Nợ131/Có511", float(sbh.loc[m511, "Amount2"].sum()), _tong(df, "131", "511")),
        ("thuế ra Nợ131/Có33311", float(sbh.loc[m511, "Amount3"].sum()), _tong(df, "131", "33311")),
        ("trả lại Nợ5213/Có131", -float(sbh.loc[m521, "Amount2"].sum()), _tong(df, "5213", "131")),
        ("thuế trả lại Nợ33311/Có131", -float(sbh.loc[m521, "Amount3"].sum()), _tong(df, "33311", "131")),
    ]
    lech = [f"{ten} lệch {fmt_so(a - b)}" for ten, a, b in cap if abs(a - b) > NGUONG_KHOP]
    if not lech:
        return ""
    return ("⚠ Sổ bán hàng KHÔNG khớp bảng kê (" + "; ".join(lech) + ") — hai file không cùng"
            " thời điểm kết xuất; xuất lại cùng lúc rồi nạp lại trước khi tin kết quả này.")


def _c32_c34(df: pd.DataFrame, sbh: pd.DataFrame | None) -> list[CheckResult]:
    ten32, ten34 = "Doanh thu thiếu thuế đầu ra", "Hàng bán trả lại chưa giảm thuế đầu ra"
    if sbh is None:
        # Không có sổ thì KHÔNG được nói "đạt": luồng nạp đã chặn cứng khi kỳ có bán
        # hàng/trả lại, nên tới đây chỉ có thể là kỳ không có — hoặc gọi ngoài luồng UI.
        co_ban = bool((bat_dau(df["DebitAccount"], "131") & bat_dau(df["CreditAccount"], "511")).any())
        co_tl = bool((bat_dau(df["DebitAccount"], "5213") & bat_dau(df["CreditAccount"], "131")).any())
        ra = []
        for ma, ten, co in (("C3.2", ten32, co_ban), ("C3.4", ten34, co_tl)):
            r = CheckResult(ma, ten, NHOM, VANG, pd.DataFrame(columns=list(COT_SBH) + ["ly_do"]),
                            "Chưa nạp sổ chi tiết bán hàng — chưa kiểm được thuế từng dòng hàng"
                            if co else "Kỳ này không có dòng nào thuộc diện")
            r.la_thong_ke = co
            ra.append(r)
        return ra

    m511 = bat_dau(sbh["CreditAccount2"], "511") & bat_dau(sbh["DebitAccount2"], "131")
    m521 = bat_dau(sbh["DebitAccount2"], "521") & bat_dau(sbh["CreditAccount2"], "131")
    canh_bao = _lech_voi_bang_ke(df, sbh, m511, m521)
    noi_bo = "Đã loại hàng tặng giá 0 và giao dịch chi nhánh (TransCode " + "/".join(TRANSCODE_NOI_BO) + ")"

    def _kq(mat_na, ma, ten, ly_do):
        ct = sbh.loc[_dong_thue_0(sbh, mat_na), [c for c in COT_SBH if c in sbh.columns]].copy()
        ct["ly_do"] = ly_do
        return CheckResult(ma, ten, NHOM, VANG, ct.reset_index(drop=True),
                           " ".join(x for x in (canh_bao, noi_bo) if x))

    return [
        _kq(m511, "C3.2", ten32, "Bán hàng Nợ 131/Có 511 mà thuế GTGT của dòng hàng = 0"),
        _kq(m521, "C3.4", ten34, "Trả lại Nợ 521/Có 131 mà thuế GTGT của dòng hàng = 0"),
    ]


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    kq = []
    tax = df["TaxCode"].fillna("").astype(str).str.strip().str.upper()
    co_thue = tax.ne("") & tax.ne("V00")
    dong_tk_thue = bat_dau(df["DebitAccount"], *TK_THUE) | bat_dau(df["CreditAccount"], *TK_THUE)
    ct = khoa_chung_tu(df)

    docs_thieu = set(ct[co_thue]) - set(ct[dong_tk_thue])
    r31 = tao_ket_qua(df[co_thue & ct.isin(docs_thieu)], "C3.1",
                      "Có mã thuế nhưng chứng từ thiếu TK thuế", NHOM, VANG,
                      "TaxCode chịu thuế nhưng cả chứng từ không có dòng 1331/33311 — Bravo hay"
                      " gắn TaxCode cả dòng giá vốn/kho; chỉ để soát, không kéo kết luận")
    r31.la_thong_ke = True
    kq.append(r31)

    r32, r34 = _c32_c34(df, ctx.so_ban_hang if ctx is not None else None)
    kq.append(r32)

    vao = df[bat_dau(df["DebitAccount"], "1331")].groupby(tax[bat_dau(df["DebitAccount"], "1331")])["Amount"].sum()
    ra = df[bat_dau(df["CreditAccount"], "33311")].groupby(tax[bat_dau(df["CreditAccount"], "33311")])["Amount"].sum()
    dem = df.groupby(tax)["Amount"].size()
    bang = pd.concat([vao.rename("thue_vao_1331"), ra.rename("thue_ra_33311"),
                      dem.rename("so_dong")], axis=1).fillna(0)
    bang.index.name = "TaxCode"
    kq.append(CheckResult("C3.3", "Tổng hợp thuế GTGT theo mã thuế", NHOM, XANH,
                          bang.reset_index(), la_thong_ke=True))
    kq.append(r34)
    return kq
