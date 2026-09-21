"""Nhóm 2 — Định khoản bất thường."""
import pandas as pd

from .base import VANG, BoiCanh, CheckResult, bat_dau, tao_ket_qua

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
    return kq


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
