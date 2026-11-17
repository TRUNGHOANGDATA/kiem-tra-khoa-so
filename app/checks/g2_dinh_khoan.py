"""Nhóm 2 — Định khoản bất thường."""
import pandas as pd

from .base import DO, VANG, BoiCanh, CheckResult, bat_dau, fmt_so, tao_ket_qua

NHOM = "G2"
# C2.4 — quy đổi ngoại tệ luôn có sai số làm tròn, nên ngưỡng phải THEO TỶ LỆ.
# Mốc 1đ tuyệt đối cũ bắt cả 7 dòng nhập khẩu của A01 với TỔNG lệch đúng 1.276đ
# (lớn nhất 818đ trên bút toán 2,26 tỷ = 0,00004%) — toàn bộ là làm tròn USD.
# Cùng dạng ngưỡng với C4.2: tỷ lệ cộng một đồng chống chia cho 0.
TY_LE_LECH_TY_GIA = 0.001          # 0,1%
NGUONG_LECH_TY_GIA = 1.0           # cộng thêm, cho bút toán nhỏ


def _hop_le(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.fullmatch(r"\d{3,}")


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    kq = []
    tk_cong_no = bat_dau(df["DebitAccount"], "131", "331") | bat_dau(df["CreditAccount"], "131", "331")
    thieu_dt = df["CustomerCode"].fillna("").astype(str).str.strip().eq("")
    kq.append(tao_ket_qua(df[tk_cong_no & thieu_dt], "C2.1", "Thiếu mã đối tượng ở TK công nợ",
                          NHOM, VANG, "Dùng TK 131/331 nhưng CustomerCode trống"))

    sai = ~_hop_le(df["DebitAccount"]) | ~_hop_le(df["CreditAccount"])
    kq.append(tao_ket_qua(df[sai], "C2.2", "Tài khoản sai định dạng", NHOM, VANG,
                          "TK phải toàn chữ số, tối thiểu 3 ký tự"))

    # C2.3 — chỉ là bút toán đáng ngờ khi tiền tự chuyển vào CHÍNH NÓ. Cùng nhóm 111/112
    # hai vế là chuyện thường ngày của ngân quỹ: chuyển giữa hai ngân hàng, giữa hai quỹ.
    # Khác biệt nằm ở SỐ HIỆU TK hoặc ở TÀI KHOẢN NGÂN HÀNG, không ở ba chữ số đầu —
    # đúng khuôn mẫu đã sửa cho C1.4. Đo trên sổ 08/2026: A01 ra 27 dòng thì cả 27 đều
    # khác tài khoản ngân hàng (BIDV -> ACB...), không dòng nào tự chuyển vào chính mình.
    cung_nhom = ((bat_dau(df["DebitAccount"], "111") & bat_dau(df["CreditAccount"], "111")) |
                 (bat_dau(df["DebitAccount"], "112") & bat_dau(df["CreditAccount"], "112")))
    trung_tk = df["DebitAccount"].fillna("").astype(str) == df["CreditAccount"].fillna("").astype(str)
    trung_nh = _bang_nhau(df, "BankAccId", "CrspBankAccId")
    kq.append(tao_ket_qua(df[cung_nhom & trung_tk & trung_nh], "C2.3",
                          "Tiền chuyển vào chính tài khoản đó", NHOM, VANG,
                          "Nợ/Có cùng một tài khoản tiền và cùng một tài khoản ngân hàng"
                          " — bút toán không làm tiền dịch chuyển",
                          ghi_chu="Đã loại chuyển tiền giữa hai ngân hàng/quỹ khác nhau"
                                  " (khác BankAccId hoặc khác số hiệu TK)"))

    ngoai_te = df["CurrencyCode"].fillna("VND").astype(str).str.upper().ne("VND")
    tinh = df["OriginalAmount"] * df["ExchangeRate"]
    lech = (df["Amount"] - tinh).abs() > (df["Amount"].abs() * TY_LE_LECH_TY_GIA + NGUONG_LECH_TY_GIA)
    kq.append(tao_ket_qua(df[ngoai_te & lech], "C2.4", "Lệch quy đổi ngoại tệ", NHOM, VANG,
                          "Amount ≠ OriginalAmount × ExchangeRate",
                          ghi_chu=f"Bỏ qua chênh dưới {TY_LE_LECH_TY_GIA:.1%} do làm tròn quy đổi"))
    kq.append(_c25(df))
    kq.append(_c26(df))
    return kq


# C2.5 — BÁN TSCĐ CHUYỂN GIAO SANG KHAY C: thu 711 phải BẰNG giá trị còn lại (GTCL).
# Người dùng chốt 16–17/11/2026: tách pháp nhân không phải giao dịch kinh tế, hóa đơn bán
# xuất đúng GTCL → Có 711 = Nợ 811/Có 21x, không được ghi chênh. Lệch là ✕ ĐỎ.
#
# Cách tính lấy NGUYÊN từ dự án Power BI (`giai_trinh_chuyen_giao_tscd.py`, sheet
# "TSCĐ - theo khay"); chạy trên file 15/11 ra đúng 5 số Power BI đã báo. Hai chỗ khác
# (red-team 17/11): thu chỉ lấy dòng Nợ 131 — tên khách khớp cả các chi nhánh của pháp nhân
# nhận (phạt trừ lương Nợ 334/Có 711…) sinh ĐỎ giả ở 6 khay; và tính RÒNG (trừ bút toán
# đảo Nợ 711/Có 131, Nợ 21x/Có 811) để kế toán sửa xong thì cảnh báo tắt được.
#
# Phần tất toán CCDC / chi phí chờ phân bổ (Nợ 811/Có 24x, 6xx, 15x) bán kèm KHÔNG vào
# GTCL — y như Power BI; chỉ nêu số trong ghi chú để kế toán đối chiếu.
KHACH_NHAN = "thành phố hồ chí minh"            # tên khách của pháp nhân nhận chuyển giao
TU_KHOA_NOI_BO = ("bán hà nội", "an giang")     # diễn giải: chuyển nội bộ pháp nhân cũ
TU_KHOA_NHAN = "hcm"                            # diễn giải KHÔNG có -> cũng là nội bộ
# Hóa đơn làm tròn NGHÌN ĐỒNG theo từng tài sản (ghép 1-1 đo được: lệch vài nghìn đồng/TS).
# A08 file 15/11: 53 TS lệch tổng 48đ — Power BI coi là khớp; ngưỡng 1đ sẽ báo ĐỎ giả.
NGUONG_C25_MOI_TS = 1_000.0
COT_C25 = ["DocCode", "DocNo", "DocDate", "Description", "CustomerName", "DebitAccount",
           "CreditAccount", "Amount"]


def _chua(s: pd.Series, *tu: str) -> pd.Series:
    t = s.fillna("").astype(str).str.lower()
    m = pd.Series(False, index=s.index)
    for x in tu:
        m |= t.str.contains(x, regex=False)
    return m


def _chuyen_giao(df: pd.DataFrame):
    """(df bỏ đối ứng 911, mặt nạ khách pháp nhân nhận, mặt nạ diễn giải nội bộ) — chung C2.5/C2.6."""
    df = df[~bat_dau(df["DebitAccount"], "911") & ~bat_dau(df["CreditAccount"], "911")]
    khach = (_chua(df["CustomerName"], KHACH_NHAN) if "CustomerName" in df.columns
             else pd.Series(False, index=df.index))
    mo_ta = df["Description"] if "Description" in df.columns else pd.Series("", index=df.index)
    noi_bo = _chua(mo_ta, *TU_KHOA_NOI_BO) | ~_chua(mo_ta, TU_KHOA_NHAN)
    return df, khach, noi_bo


def _c25(df: pd.DataFrame) -> CheckResult:
    ten = "Bán TSCĐ chuyển giao: thu 711 ≠ giá trị còn lại"
    df, khach, noi_bo = _chuyen_giao(df)
    no, co = df["DebitAccount"], df["CreditAccount"]

    thu = khach & bat_dau(no, "131") & bat_dau(co, "711")
    thu_dao = khach & bat_dau(no, "711") & bat_dau(co, "131")
    gt = bat_dau(no, "811") & bat_dau(co, "21") & ~noi_bo
    gt_dao = bat_dau(no, "21") & bat_dau(co, "811") & ~noi_bo
    thue_vao_711 = khach & bat_dau(no, "133") & bat_dau(co, "711")

    if not (thu | thu_dao | gt | gt_dao).any():
        r = CheckResult("C2.5", ten, NHOM, DO, pd.DataFrame(columns=COT_C25 + ["loai_but_toan", "ly_do"]),
                        "Kỳ này không có bán TSCĐ chuyển giao sang khay C — không xét")
        r.la_thong_ke = True
        return r

    tien = df["Amount"]
    so_thu = float(tien[thu].sum() - tien[thu_dao].sum())
    so_gt = float(tien[gt].sum() - tien[gt_dao].sum())
    chenh = so_thu - so_gt
    gt_nb = bat_dau(no, "811") & bat_dau(co, "21") & noi_bo
    tat_toan = bat_dau(no, "811") & (bat_dau(co, "24", "6", "15"))
    ghi_chu = (f"Thu 711 {fmt_so(so_thu)} − GTCL {fmt_so(so_gt)} = chênh {fmt_so(chenh)} (phải = 0)."
               f" Thông tin, không vào chênh: GTCL chuyển nội bộ {fmt_so(tien[gt_nb].sum())};"
               f" tất toán CCDC/chi phí chờ phân bổ (Nợ 811/Có 24x, 6xx, 15x) {fmt_so(tien[tat_toan].sum())}"
               f" → Thu − GTCL − tất toán = {fmt_so(chenh - tien[tat_toan].sum())}."
               f" Ngưỡng làm tròn 1.000đ × {max(1, int(gt.sum()))} tài sản.")
    if thue_vao_711.any():
        ghi_chu += f" ⚠ Có {int(thue_vao_711.sum())} dòng Nợ 133/Có 711 (thuế đầu vào ghi thu nhập khác)."
    nguong = NGUONG_C25_MOI_TS * max(1, int(gt.sum()))
    if abs(chenh) <= nguong:
        return CheckResult("C2.5", ten, NHOM, DO, pd.DataFrame(columns=COT_C25 + ["loai_but_toan", "ly_do"]),
                           ghi_chu)

    loai = pd.Series("", index=df.index, dtype="object")
    loai[thu], loai[thu_dao] = "Thu 711 (Nợ 131/Có 711)", "Đảo thu 711 (Nợ 711/Có 131)"
    loai[gt], loai[gt_dao] = "GTCL TSCĐ (Nợ 811/Có 21x)", "Đảo GTCL (Nợ 21x/Có 811)"
    loai[thue_vao_711] = "⚠ Nợ 133/Có 711 — bất thường"
    m = loai.ne("")
    ct = df.loc[m, [c for c in COT_C25 if c in df.columns]].copy()
    ct["loai_but_toan"] = loai[m]
    ct["ly_do"] = f"Thu 711 − GTCL = {fmt_so(chenh)} (luật: phải = 0)"
    return CheckResult("C2.5", ten, NHOM, DO, ct.reset_index(drop=True), ghi_chu)


def _bang_nhau(df: pd.DataFrame, cot_a: str, cot_b: str) -> pd.Series:
    """Hai cột chiều coi là TRÙNG nhau — thiếu cột hoặc cùng để trống cũng là trùng.

    File Bravo có `BankAccId`/`CrspBankAccId`, nhưng dòng tiền mặt để trống cả hai và
    bản kết xuất cũ có thể không có cột. Thiếu bằng chứng "khác nhau" thì không được
    suy là khác — nếu không, C2.3 im lặng bỏ sót đúng ca nó sinh ra để bắt.
    """
    if cot_a not in df.columns or cot_b not in df.columns:
        return pd.Series(True, index=df.index)
    a = df[cot_a].astype("string").fillna("")
    b = df[cot_b].astype("string").fillna("")
    return a == b


# C2.6 — HÀNG HÓA CHUYỂN GIAO SANG KHAY C: doanh thu hàng hóa/thành phẩm phải BẰNG giá vốn.
# Người dùng chốt 17/11/2026: lệch là ▲ VÀNG, ngưỡng 0đ. Gốc là sheet "Hàng hoá - theo khay"
# của Power BI; sửa theo red-team 17/11 (đo kỳ 10):
#   - PHẠM VI: chỉ khay × kỳ có chuyển giao TSCĐ (GTCL Nợ 811/Có 21x không nội bộ). Chạy theo
#     "chứng từ có khách pháp nhân nhận" trên mọi khay thì bắt cả bán hàng thường có lãi của khay
#     khác cho chi nhánh pháp nhân nhận, và khay C bán cho chính nó -> VÀNG giả 6 khay. Giới
#     hạn: tháng chỉ chuyển hàng mà không chuyển TSCĐ thì không xét (ghi rõ ở ghi chú).
#   - CHỈ 5111/5112 (hàng hóa, thành phẩm) + 521: chứng từ của khách pháp nhân nhận còn có 5113
#     (cho thuê xe, phần mềm — không có giá vốn) làm chênh sai dấu ở A04/A07; 5113/5118 chỉ ghi chú.
#   - RÒNG (Có − Nợ), như C2.5: điều chỉnh ghi số âm cả hai chiều (Nợ 131/Có 511 âm; Nợ 511/Có 131
#     âm) — tính gộp thì kế toán sửa xong ▲ không tắt. Bỏ dòng kết chuyển nội tại 511↔521.
#   - Nhóm chứng từ theo `Id` (không có thì DocCode·DocNo). Dòng giá vốn KHÔNG SỐ chứng từ (A07: 208
#     dòng Nợ 632) tự mang tên khách pháp nhân nhận nên vào diện theo chính nó.
TK_DT_HANG = ("5111", "5112", "521")
COT_C26 = ["DocCode", "DocNo", "Description", "doanh_thu", "gia_von", "chenh", "ly_do"]


def _c26(df: pd.DataFrame) -> CheckResult:
    ten = "Hàng hóa chuyển giao: doanh thu ≠ giá vốn"
    rong = pd.DataFrame(columns=COT_C26)
    df, khach, noi_bo = _chuyen_giao(df)
    no, co = df["DebitAccount"], df["CreditAccount"]
    co_tscd = (bat_dau(no, "811") & bat_dau(co, "21") & ~noi_bo).any()
    if not co_tscd or not khach.any():
        r = CheckResult("C2.6", ten, NHOM, VANG, rong,
                        "Khay × kỳ này không chuyển giao TSCĐ sang khay C — không xét"
                        " (C2.6 chỉ xét kỳ có chuyển giao TSCĐ)")
        r.la_thong_ke = True
        return r
    dp = df["DocCode"].fillna("").astype(str) + "·" + df["DocNo"].fillna("").astype(str)
    khoa = (df["Id"].astype("string").fillna(dp) if "Id" in df.columns else dp)
    ct = khoa.isin(set(khoa[khach]))
    noi_tai = bat_dau(no, "511", "521") & bat_dau(co, "511", "521")      # kết chuyển 511<->521
    tien = df["Amount"]
    dt_co, dt_no = ct & bat_dau(co, *TK_DT_HANG) & ~noi_tai, ct & bat_dau(no, *TK_DT_HANG) & ~noi_tai
    gv_no, gv_co = ct & bat_dau(no, "632"), ct & bat_dau(co, "632")
    dt_dong = tien.where(dt_co, 0.0) - tien.where(dt_no, 0.0)
    gv_dong = tien.where(gv_no, 0.0) - tien.where(gv_co, 0.0)
    so_dt, so_gv = float(dt_dong[ct].sum()), float(gv_dong[ct].sum())
    chenh = so_dt - so_gv
    dv = float(tien[ct & bat_dau(co, "5113", "5118")].sum() - tien[ct & bat_dau(no, "5113", "5118")].sum())
    thue_vao_dt = ct & bat_dau(no, "133") & bat_dau(co, "511")
    ghi_chu = (f"Doanh thu hàng (5111/5112, trừ 521, ròng) {fmt_so(so_dt)} − giá vốn (632 ròng) {fmt_so(so_gv)}"
               f" = chênh {fmt_so(chenh)} (phải = 0). Thông tin, không vào chênh: doanh thu dịch vụ/khác"
               f" (5113/5118) {fmt_so(dv)}.")
    if thue_vao_dt.any():
        ghi_chu += f" ⚠ Có {int(thue_vao_dt.sum())} dòng Nợ 133/Có 511 (thuế đầu vào ghi doanh thu)."
    if abs(chenh) < 1:
        return CheckResult("C2.6", ten, NHOM, VANG, rong, ghi_chu)
    g = pd.DataFrame({"khoa": khoa[ct], "dt": dt_dong[ct], "gv": gv_dong[ct]})
    tong = g.groupby("khoa", sort=False)[["dt", "gv"]].sum()
    tong = tong[(tong["dt"] - tong["gv"]).abs() >= 1]
    dau = df[ct].assign(khoa=khoa[ct]).drop_duplicates("khoa").set_index("khoa").reindex(tong.index)
    bang = pd.DataFrame({"DocCode": dau["DocCode"].values, "DocNo": dau["DocNo"].values,
                         "Description": dau["Description"].values,
                         "doanh_thu": tong["dt"].values, "gia_von": tong["gv"].values,
                         "chenh": (tong["dt"] - tong["gv"]).values})
    bang["ly_do"] = f"Tổng khay: doanh thu − giá vốn = {fmt_so(chenh)} (luật: phải = 0)"
    return CheckResult("C2.6", ten, NHOM, VANG, bang.reset_index(drop=True), ghi_chu)
