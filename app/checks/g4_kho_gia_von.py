"""Nhóm 4 — Kho & giá vốn (đặc thù sản xuất)."""
import pandas as pd

from .base import (DO, VANG, NGUONG_CON_LAI, TK_KHO, BoiCanh, CheckResult, bat_dau, co_dong,
                    fmt_so, phat_sinh_theo_prefix, tao_ket_qua)

NHOM = "G4"
TK_CO_HOP_LE_GIA_VON = ("152", "153", "154", "155", "156", "157", "627", "2294", "1381")
TK_CHI_PHI_SX = ("621", "622", "627")
GHI_CHU_THIEU_SL = "File không có dữ liệu số lượng/đơn giá — không kiểm tra được giá xuất kho"
GHI_CHU_CHUA_TINH_GIA = ("Nghi chưa chạy tính giá xuất kho bình quân cuối kỳ "
                         "— toàn bộ dòng xuất kho đều không có đơn giá")


def _bang_tong_hop(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["TK", "ps_no", "ps_co", "ly_do"])


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    kq = []
    dong_kho = bat_dau(df["DebitAccount"], *TK_KHO) | bat_dau(df["CreditAccount"], *TK_KHO)
    co_sl = dong_kho & (df["Quantity9"] > 0)
    khong_co_du_lieu_sl = not bool((df["Quantity9"] > 0).any())
    ghi_chu_sl = GHI_CHU_THIEU_SL if khong_co_du_lieu_sl else ""

    # Cả kỳ có dòng kho kèm số lượng nhưng không một dòng nào có đơn giá dương
    # -> nghi chưa chạy tính giá xuất kho bình quân cuối kỳ (một việc phải làm,
    #    không phải hàng chục nghìn lỗi rời rạc).
    chua_tinh_gia = bool(co_sl.any()) and not bool((co_sl & (df["UnitCost"] > 0)).any())
    ghi_chu_c41 = GHI_CHU_CHUA_TINH_GIA if chua_tinh_gia else ghi_chu_sl

    gia_0 = co_sl & ((df["UnitCost"] <= 0) | (df["Amount"] <= 0))
    ly_do_c41 = ("Có SL " + df["Quantity9"].map(fmt_so) + ", đơn giá " + df["UnitCost"].map(fmt_so) +
                 ", tiền " + df["Amount"].map(fmt_so) +
                 " — có số lượng nhưng đơn giá hoặc tiền = 0 (chưa tính giá xuất kho)")
    kq.append(tao_ket_qua(df[gia_0], "C4.1", "Xuất/nhập kho giá = 0", NHOM, DO, ly_do_c41[gia_0],
                          ghi_chu=ghi_chu_c41))

    co_gia = co_sl & (df["UnitCost"] > 0)
    tien_tinh = df["Quantity9"] * df["UnitCost"]
    lech = (df["Amount"] - tien_tinh).abs() > (df["Amount"].abs() * 0.001 + 1)
    ly_do_c42 = ("SL " + df["Quantity9"].map(fmt_so) + " × đơn giá " + df["UnitCost"].map(fmt_so) +
                 " = " + tien_tinh.map(fmt_so) + " nhưng Amount ghi " + df["Amount"].map(fmt_so) +
                 " — lệch vượt ngưỡng làm tròn 0,1% + 1đ")
    kq.append(tao_ket_qua(df[co_gia & lech], "C4.2", "Tiền ≠ Số lượng × Đơn giá", NHOM, VANG,
                          ly_do_c42[co_gia & lech], ghi_chu=ghi_chu_sl))

    gv_sai = bat_dau(df["DebitAccount"], "632") & ~bat_dau(df["CreditAccount"], *TK_CO_HOP_LE_GIA_VON)
    kq.append(tao_ket_qua(df[gv_sai], "C4.3", "Giá vốn không đối ứng TK kho", NHOM, VANG,
                          f"Nợ 632 nhưng TK Có không thuộc {'/'.join(TK_CO_HOP_LE_GIA_VON)}"))

    rows = []
    for tk in TK_CHI_PHI_SX:
        ps_no, ps_co = phat_sinh_theo_prefix(df, tk)
        if ps_no <= 0:
            continue
        if not co_dong(df, no=("154",), co=(tk,)):
            rows.append({"TK": tk, "ps_no": ps_no, "ps_co": ps_co,
                         "ly_do": f"Có phát sinh Nợ {tk} nhưng không có bút toán Nợ 154 / Có {tk}"})
        elif ps_no - ps_co > NGUONG_CON_LAI:
            rows.append({"TK": tk, "ps_no": ps_no, "ps_co": ps_co,
                         "ly_do": f"Mới kết chuyển một phần — còn {fmt_so(ps_no - ps_co)} chưa đưa về 154"})
    kq.append(CheckResult("C4.4", "Chưa tập hợp chi phí SX về 154", NHOM, DO, _bang_tong_hop(rows)))

    rows = []
    if co_dong(df, no=("154",)) and not co_dong(df, no=("155", "157", "632"), co=("154",)):
        ps_no, ps_co = phat_sinh_theo_prefix(df, "154")
        rows.append({"TK": "154", "ps_no": ps_no, "ps_co": ps_co,
                     "ly_do": "Đã tập hợp vào 154 nhưng không có bút toán Nợ 155/157/632 / Có 154"
                              " (nhập kho thành phẩm / gửi bán / bán thẳng không qua kho)"})
    kq.append(CheckResult("C4.5", "Chưa nhập kho thành phẩm 154 → 155", NHOM, VANG, _bang_tong_hop(rows)))
    return kq
