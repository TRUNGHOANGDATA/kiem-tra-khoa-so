"""Nhóm 1 — Hình thức chứng từ."""
import pandas as pd

from .base import DO, VANG, BoiCanh, CheckResult, khoa_chung_tu, tao_ket_qua

NHOM = "G1"
DOC_DIEU_CHUYEN = ("DC", "LR", "BN", "BT")   # điều chuyển kho / xử lý / chuyển tiền nội bộ
GHI_CHU_C11 = ("Tên vật tư (ItemName) được tính là diễn giải hợp lệ; chỉ báo khi CẢ"
               " chứng từ không có dòng nào có diễn giải")
GHI_CHU_C14 = f"Đã loại trừ chứng từ điều chuyển nội bộ: {'/'.join(DOC_DIEU_CHUYEN)}"


def _trong(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip().eq("")


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    kq = []
    # Đơn vị xét là CHỨNG TỪ, không phải dòng. Bravo để diễn giải ở ItemName với dòng
    # vật tư, và không điền gì cho dòng thuế — trên file thật 10.308 dòng bị bắt ở
    # A01/A02/A03 đều là cặp 1311/33311 (dòng thuế GTGT của hóa đơn bán hàng), trong khi
    # KHÔNG chứng từ nào của cả 8 chi nhánh thiếu diễn giải hoàn toàn. Một chứng từ đã
    # được mô tả ở dòng doanh thu thì dòng thuế của nó không phải "thiếu diễn giải".
    thieu_mo_ta = _trong(df["Description"]) & _trong(df["ItemName"])
    ct = khoa_chung_tu(df)
    ct_da_mo_ta = set(ct[~thieu_mo_ta])
    kq.append(tao_ket_qua(df[thieu_mo_ta & ~ct.isin(ct_da_mo_ta)], "C1.1", "Thiếu diễn giải",
                          NHOM, VANG, "Cả chứng từ không có dòng nào ghi diễn giải",
                          ghi_chu=GHI_CHU_C11))

    d = df["DocDate"]
    ngoai_ky = d.notna() & ((d.dt.month != ctx.ky_thang) | (d.dt.year != ctx.ky_nam))
    kq.append(tao_ket_qua(df[ngoai_ky], "C1.2", "Ngày chứng từ ngoài kỳ", NHOM, DO,
                          f"Ngày không thuộc kỳ {ctx.ky_thang:02d}/{ctx.ky_nam}"))

    keys = ["DocNo", "DebitAccount", "CreditAccount", "Amount", "Description"]
    trung = df.duplicated(subset=keys, keep=False)
    r13 = tao_ket_qua(df[trung].sort_values(keys), "C1.3", "Nghi trùng bút toán", NHOM, VANG,
                      "Trùng số CT + TK Nợ/Có + số tiền + diễn giải — bút toán lặp trong cùng"
                      " chứng từ là bình thường; chỉ để soát, không kéo kết luận")
    r13.la_thong_ke = True
    kq.append(r13)

    # Chứng từ điều chuyển nội bộ (kho ↔ kho, ngân hàng ↔ ngân hàng) vốn dĩ cùng TK trên
    # sổ cái — phân biệt nằm ở cột chiều/kho, nên loại trừ để không báo động giả.
    la_dieu_chuyen = df["DocCode"].isin(DOC_DIEU_CHUYEN)
    cung_tk = (df["DebitAccount"].notna() & df["CreditAccount"].notna()
               & (df["DebitAccount"] == df["CreditAccount"]) & ~la_dieu_chuyen)
    kq.append(tao_ket_qua(df[cung_tk], "C1.4", "TK Nợ = TK Có", NHOM, DO,
                          f"Định khoản cùng một tài khoản (không tính chứng từ điều chuyển"
                          f" {'/'.join(DOC_DIEU_CHUYEN)})", ghi_chu=GHI_CHU_C14))

    # Số tiền = 0 là dòng định khoản không có giá trị -> ĐỎ. Số âm KHÔNG tính ở đây:
    # trong Bravo, Amount < 0 thường là bút toán điều chỉnh/kiểm kê hợp lệ (xem C1.7).
    kq.append(tao_ket_qua(df[df["Amount"] == 0], "C1.5", "Số tiền = 0", NHOM, DO,
                          "Số tiền bằng 0 — dòng định khoản không có giá trị"))

    thieu = _trong(df["DocNo"]) | df["DocDate"].isna()
    kq.append(tao_ket_qua(df[thieu], "C1.6", "Thiếu số chứng từ / ngày", NHOM, DO,
                          "Thiếu DocNo hoặc DocDate"))

    # Số tiền âm — điều chỉnh/kiểm kê hợp lệ; chỉ THỐNG KÊ để soát, không kéo kết luận.
    am = tao_ket_qua(df[df["Amount"] < 0], "C1.7", "Số tiền âm (điều chỉnh/kiểm kê)", NHOM, VANG,
                     "Số tiền âm — thường là bút toán điều chỉnh/kiểm kê; chỉ để soát, không chặn khóa sổ")
    am.la_thong_ke = True
    kq.append(am)
    return kq
