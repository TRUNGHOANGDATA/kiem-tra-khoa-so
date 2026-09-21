"""Nhóm 3 — Thuế GTGT."""
import pandas as pd

from .base import VANG, XANH, BoiCanh, CheckResult, bat_dau, khoa_chung_tu, tao_ket_qua

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

    # Loại dòng doanh thu NỘI BỘ khỏi diện bắt, nhưng vẫn xét "chứng từ có 33311 chưa"
    # trên toàn bộ chứng từ: chứng từ lẫn cả bán nội bộ lẫn bán khách ngoài thì dòng
    # khách ngoài vẫn phải bị bắt.
    dt = bat_dau(df["CreditAccount"], "511") & co_thue & ~_noi_bo(df)
    dong_33311 = bat_dau(df["DebitAccount"], "33311") | bat_dau(df["CreditAccount"], "33311")
    docs_dt_thieu = set(ct[dt]) - set(ct[dong_33311])
    kq.append(tao_ket_qua(df[dt & ct.isin(docs_dt_thieu)], "C3.2",
                          "Doanh thu thiếu thuế đầu ra", NHOM, VANG,
                          "Ghi Có 511 với mã thuế chịu thuế nhưng cả chứng từ"
                          " không có dòng 33311 (thuế GTGT đầu ra)",
                          ghi_chu="Đã loại giao dịch nội bộ (TransCode "
                                  + "/".join(TRANSCODE_NOI_BO) + ") — bán & điều chuyển"
                                  " trong cùng pháp nhân không phát sinh thuế GTGT đầu ra"))

    vao = df[bat_dau(df["DebitAccount"], "1331")].groupby(tax[bat_dau(df["DebitAccount"], "1331")])["Amount"].sum()
    ra = df[bat_dau(df["CreditAccount"], "33311")].groupby(tax[bat_dau(df["CreditAccount"], "33311")])["Amount"].sum()
    dem = df.groupby(tax)["Amount"].size()
    bang = pd.concat([vao.rename("thue_vao_1331"), ra.rename("thue_ra_33311"),
                      dem.rename("so_dong")], axis=1).fillna(0)
    bang.index.name = "TaxCode"
    kq.append(CheckResult("C3.3", "Tổng hợp thuế GTGT theo mã thuế", NHOM, XANH,
                          bang.reset_index(), la_thong_ke=True))
    return kq
