"""Nhóm 7 — Bút toán phân bổ & trích lập cuối kỳ (nhóm hay quên nhất).

Chỉ dùng phát sinh TRONG KỲ, so khớp ở TÀI KHOẢN CẤP 1 (prefix 3 chữ số).

Vì sao phần lớn nhóm này là CHECKLIST (la_thong_ke) chứ không phải cảnh báo:
không có số dư đầu kỳ nên tool chỉ biết "kỳ này không thấy bút toán", KHÔNG biết
DN có TSCĐ / khoản trả trước / lao động hay không. Biến "không thấy" thành cảnh
báo vàng là khẳng định dựa trên sự vắng mặt của bằng chứng — đúng bẫy đã làm C4.1
sinh 30.492 dương tính giả. Lần này hậu quả còn nặng hơn: mọi bộ sổ đều kẹt ở
"CÒN N MỤC CẦN RÀ SOÁT" và băng "SẴN SÀNG KHÓA SỔ" thành bất khả thi (đã dựng thử
và thấy test_ket_luan đỏ).

Chỉ C7.6 là cảnh báo thật kéo kết luận, vì bằng chứng nằm ngay trong file: có kết
chuyển lãi (911 → 421) mà không có 8211. C7.5 (413 tỷ giá) tuy cũng có bằng chứng
trong file nhưng là nghiệp vụ không trọng yếu, hiếm phát sinh — nên chỉ là nhắc nhẹ
(la_thong_ke=True), không kéo kết luận khóa sổ.
"""
import pandas as pd

from .base import VANG, BoiCanh, CheckResult, bat_dau, co_dong, loc_dong, phat_sinh_theo_prefix

NHOM = "G7"
TK_CHI_PHI = ("622", "627", "641", "642")
# TK gốc ngoại tệ có số dư phải đánh giá lại cuối kỳ (TT200). Ngoại tệ chạy qua TK
# vật tư/hàng hoá (152/153/156…) ghi theo tỷ giá lúc phát sinh, KHÔNG đánh giá lại.
TK_TIEN_TE = ("111", "112", "113", "131", "136", "138", "331", "341")


def _checklist(ma: str, ten: str, co: bool, khi_co: str, khi_khong: str) -> CheckResult:
    """Một dòng checklist: luôn hiện tình trạng, KHÔNG bao giờ đổi kết luận khóa sổ."""
    bang = pd.DataFrame([{"co_phat_sinh": bool(co),
                          "ket_luan": khi_co if co else khi_khong}])
    return CheckResult(ma, ten, NHOM, VANG, bang, la_thong_ke=True)


def _thong_ke_ps(ma: str, ten: str, prefix: str, df: pd.DataFrame) -> CheckResult:
    """Bảng thống kê phát sinh Nợ/Có ở cấp 1 — không phải lỗi, chỉ để soát."""
    no, co = phat_sinh_theo_prefix(df, prefix)
    bang = pd.DataFrame([{"TK": prefix, "ps_no": no, "ps_co": co}])
    return CheckResult(ma, ten, NHOM, VANG, bang, la_thong_ke=True)


def _canh_bao(ma: str, ten: str, thieu: bool, ly_do: str, ghi_chu: str = "",
              la_thong_ke: bool = False) -> CheckResult:
    """Cảnh báo: chỉ bắn khi có bằng chứng đối ứng trong chính file.

    la_thong_ke=True → chỉ nhắc, KHÔNG kéo kết luận khóa sổ (dùng cho các mục
    không trọng yếu như đánh giá tỷ giá 413, hiếm khi phát sinh)."""
    ct = pd.DataFrame([{"ket_luan": ly_do}] if thieu else [], columns=["ket_luan"])
    return CheckResult(ma, ten, NHOM, VANG, ct, ghi_chu, la_thong_ke=la_thong_ke)


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    kq = []

    # --- C7.1–C7.3: checklist (không kéo kết luận) ---
    _, co_214 = phat_sinh_theo_prefix(df, "214")
    kq.append(_checklist("C7.1", "Khấu hao TSCĐ", co_214 > 0,
                         "Đã có bút toán Có 214 trong kỳ",
                         "Kỳ này KHÔNG thấy bút toán Có 214 — xác nhận lại nếu DN có TSCĐ đang dùng"))

    _, co_242 = phat_sinh_theo_prefix(df, "242")
    kq.append(_checklist("C7.2", "Phân bổ chi phí trả trước / CCDC", co_242 > 0,
                         "Đã có bút toán Có 242 trong kỳ",
                         "Kỳ này KHÔNG thấy bút toán Có 242 — xác nhận lại nếu DN có chi phí trả trước/CCDC đang phân bổ"))

    luong = any(co_dong(df, no=TK_CHI_PHI, co=(tk,)) for tk in ("334", "338"))
    kq.append(_checklist("C7.3", "Trích lương & các khoản theo lương", luong,
                         "Đã có bút toán đưa 334/338 vào chi phí 622/627/641/642",
                         "KHÔNG thấy bút toán đưa lương/BHXH (334/338) vào chi phí trong kỳ"))

    # --- C7.4: thống kê trích trước 335 ---
    kq.append(_thong_ke_ps("C7.4", "Trích trước chi phí (335)", "335", df))

    # --- C7.5: đánh giá tỷ giá cuối kỳ (nhắc nhẹ, không kéo kết luận) ---
    # Chỉ suy "còn số dư gốc ngoại tệ" khi ngoại tệ chạm TK TIỀN TỆ.
    cc = (df["CurrencyCode"].astype("string").str.strip()
          if "CurrencyCode" in df.columns else pd.Series("", dtype="string", index=df.index))
    la_ngoai_te = cc.notna() & ~cc.isin(["", "VND"])
    cham_tien_te = bat_dau(df["DebitAccount"], *TK_TIEN_TE) | bat_dau(df["CreditAccount"], *TK_TIEN_TE)
    co_du_ngoai_te = bool((la_ngoai_te & cham_tien_te).any())
    no_413, co_413 = phat_sinh_theo_prefix(df, "413")
    kq.append(_canh_bao("C7.5", "Chưa đánh giá chênh lệch tỷ giá cuối kỳ",
                        co_du_ngoai_te and no_413 == 0 and co_413 == 0,
                        "Có phát sinh ngoại tệ trên tài khoản tiền tệ nhưng không thấy bút toán 413"
                        " — kiểm tra đánh giá lại số dư gốc ngoại tệ cuối kỳ",
                        ghi_chu="Chỉ xét dòng ngoại tệ chạm TK " + "/".join(TK_TIEN_TE),
                        la_thong_ke=True))

    # --- C7.6: chi phí thuế TNDN (cảnh báo thật) ---
    # "Có lãi" phải xét theo NET cả kỳ, không phải "tồn tại một dòng kết chuyển lãi":
    # kỳ khóa theo tháng có thể vừa có tháng lãi (Nợ 911/Có 421) vừa có tháng lỗ
    # (Nợ 421/Có 911); nếu net là LỖ thì không phát sinh 8211 là đúng, không cảnh báo.
    kc_lai = loc_dong(df, no=("911",), co=("421",))["Amount"].sum()   # kết chuyển lãi
    kc_lo = loc_dong(df, no=("421",), co=("911",))["Amount"].sum()    # kết chuyển lỗ
    lai_ky = float(kc_lai) - float(kc_lo)                             # net lãi kỳ (âm = lỗ kỳ)
    no_821, _ = phat_sinh_theo_prefix(df, "821")
    # Có CĐPS thì trừ lỗ lũy kế đầu kỳ (421x): chỉ đòi 8211 khi còn thu nhập tính thuế.
    # Chưa nhập CĐPS (None) thì giữ hành vi cũ (đòi khi kỳ có lãi) + nhắc nạp CĐPS.
    lo_luy_ke = getattr(ctx, "lo_luy_ke_dau", None)
    if lo_luy_ke is None:
        con_thue = lai_ky > 0
        gc = "Chưa có CĐPS: chưa trừ được lỗ lũy kế — nạp CĐPS để loại trừ chính xác"
    else:
        con_thue = lai_ky > max(0.0, float(lo_luy_ke))
        gc = "Đã trừ lỗ lũy kế đầu kỳ (421) từ CĐPS"
    kq.append(_canh_bao("C7.6", "Chưa trích/kết chuyển chi phí thuế TNDN",
                        con_thue and no_821 == 0,
                        "KQKD có lãi (911 → 421) nhưng không thấy phát sinh 8211"
                        " — kiểm tra thuế TNDN tạm tính",
                        ghi_chu=gc))

    # --- C7.7: thống kê dự phòng 229 ---
    kq.append(_thong_ke_ps("C7.7", "Dự phòng tổn thất tài sản (229)", "229", df))
    return kq
