"""Suy trạng thái 11 bước khóa sổ từ dữ liệu phát sinh (Tab A)."""
from dataclasses import dataclass

import pandas as pd

from .checks.base import (NGUONG_CON_LAI, TK_KHO, CheckResult, bat_dau, co_dong, fmt_so,
                          phat_sinh_theo_prefix)
from .checks.g4_kho_gia_von import GHI_CHU_CHUA_TINH_GIA, GHI_CHU_THIEU_SL

BUOC_TINH_GIA_XUAT_KHO = "Tính giá xuất kho (mọi dòng xuất có đơn giá)"

DA_LAM, CHUA_LAM, CAN_RA, KHONG_AP_DUNG = "da_lam", "chua_lam", "can_ra", "khong_ap_dung"


@dataclass
class BuocKhoaSo:
    buoc: str
    trang_thai: str
    tom_tat: str
    ma_check: str


def _ket_chuyen(df, ten, tk, no, co, ma) -> BuocKhoaSo:
    """Bước dạng 'TK nguồn -> TK đích': dựa vào phát sinh & sự tồn tại bút toán."""
    ps_no, ps_co = phat_sinh_theo_prefix(df, tk)
    if ps_no == 0 and ps_co == 0:
        return BuocKhoaSo(ten, KHONG_AP_DUNG, f"Kỳ này không có phát sinh {tk}", ma)
    if not co_dong(df, no=no, co=co):
        return BuocKhoaSo(ten, CHUA_LAM, f"Phát sinh {tk}: Nợ {fmt_so(ps_no)} / Có {fmt_so(ps_co)} — chưa có bút toán kết chuyển", ma)
    net = ps_no - ps_co
    if abs(net) > 0.5:
        return BuocKhoaSo(ten, CAN_RA, f"Đã kết chuyển nhưng còn net {fmt_so(net)} chưa về 0", ma)
    return BuocKhoaSo(ten, DA_LAM, f"Nợ {fmt_so(ps_no)} / Có {fmt_so(ps_co)} — đã về 0", ma)


def _nhom_ve_911(df, ten, cac_tk, huong, ma) -> BuocKhoaSo:
    """huong='nguon->911' (doanh thu) hoặc '911->nguon' (chi phí)."""
    if huong not in ("nguon->911", "911->nguon"):
        raise ValueError(f"Hướng kết chuyển không hợp lệ: {huong}")
    co_ps = [tk for tk in cac_tk if any(phat_sinh_theo_prefix(df, tk))]
    if not co_ps:
        return BuocKhoaSo(ten, KHONG_AP_DUNG, "Không có phát sinh", ma)
    thieu, con_lai = [], []
    for tk in co_ps:
        da_kc = (co_dong(df, no=(tk,), co=("911",)) if huong == "nguon->911"
                 else co_dong(df, no=("911",), co=(tk,)))
        if not da_kc:
            thieu.append(tk)
            continue
        ps_no, ps_co = phat_sinh_theo_prefix(df, tk)
        du = (ps_co - ps_no) if huong == "nguon->911" else (ps_no - ps_co)
        if du > NGUONG_CON_LAI:
            con_lai.append(f"{tk} còn {fmt_so(du)}")
    if thieu:
        return BuocKhoaSo(ten, CHUA_LAM, f"Chưa kết chuyển: {', '.join(thieu)}", ma)
    if con_lai:
        return BuocKhoaSo(ten, CAN_RA, f"Kết chuyển chưa hết — {'; '.join(con_lai)}", ma)
    return BuocKhoaSo(ten, DA_LAM, f"Đã kết chuyển: {', '.join(co_ps)}", ma)


def suy_trang_thai(df: pd.DataFrame, ket_qua: dict[str, CheckResult]) -> list[BuocKhoaSo]:
    ds = [
        _ket_chuyen(df, "Tập hợp CP NVL trực tiếp 621 → 154", "621", ("154",), ("621",), "C4.4"),
        _ket_chuyen(df, "Tập hợp CP nhân công trực tiếp 622 → 154", "622", ("154",), ("622",), "C4.4"),
        _ket_chuyen(df, "Tập hợp & phân bổ CP SXC 627 → 154", "627", ("154",), ("627",), "C4.4"),
    ]

    if not co_dong(df, no=("154",)):
        ds.append(BuocKhoaSo("Nhập kho thành phẩm 154 → 155 (tính giá thành)", KHONG_AP_DUNG, "Không có phát sinh 154", "C4.5"))
    elif co_dong(df, no=("155", "157", "632"), co=("154",)):
        ps = loc_tong(df, ("155", "157", "632"), "154")
        ds.append(BuocKhoaSo("Nhập kho thành phẩm 154 → 155 (tính giá thành)", DA_LAM, f"Nợ 155/157/632 / Có 154: {fmt_so(ps)}", "C4.5"))
    else:
        ds.append(BuocKhoaSo("Nhập kho thành phẩm 154 → 155 (tính giá thành)", CHUA_LAM, "Có Nợ 154 nhưng chưa có Nợ 155/157/632 / Có 154", "C4.5"))

    ten_gia = BUOC_TINH_GIA_XUAT_KHO
    c41 = ket_qua.get("C4.1")
    if c41 is None:
        ds.append(BuocKhoaSo(ten_gia, KHONG_AP_DUNG, "Chưa chạy kiểm tra C4.1", "C4.1"))
    else:
        dong_kho = bat_dau(df["DebitAccount"], *TK_KHO) | bat_dau(df["CreditAccount"], *TK_KHO)
        if not dong_kho.any():
            ds.append(BuocKhoaSo(ten_gia, KHONG_AP_DUNG, "Không có bút toán kho", "C4.1"))
        elif c41.ghi_chu == GHI_CHU_THIEU_SL:
            ds.append(BuocKhoaSo(ten_gia, KHONG_AP_DUNG, c41.ghi_chu, "C4.1"))
        elif c41.ghi_chu == GHI_CHU_CHUA_TINH_GIA:
            ds.append(BuocKhoaSo(ten_gia, CHUA_LAM,
                                 f"Chưa tính giá xuất kho bình quân cuối kỳ — {c41.so_loi} dòng xuất kho chưa có đơn giá",
                                 "C4.1"))
        elif c41.so_loi == 0:
            ds.append(BuocKhoaSo(ten_gia, DA_LAM, f"{int(dong_kho.sum())} dòng kho, không dòng giá = 0", "C4.1"))
        else:
            ds.append(BuocKhoaSo(ten_gia, CAN_RA, f"Còn {c41.so_loi} dòng kho có số lượng nhưng giá = 0", "C4.1"))

    ds.append(_ket_chuyen(df, "Kết chuyển giá vốn 632 → 911", "632", ("911",), ("632",), "C5.2"))
    ds.append(_nhom_ve_911(df, "Kết chuyển doanh thu 511/515/711 → 911", ("511", "515", "711"), "nguon->911", "C5.3"))
    ds.append(_nhom_ve_911(df, "Kết chuyển chi phí 635/641/642/811 → 911", ("635", "641", "642", "811"), "911->nguon", "C5.4"))

    vao, _ = phat_sinh_theo_prefix(df, "1331")
    _, ra = phat_sinh_theo_prefix(df, "3331")
    if vao == 0 or ra == 0:
        ds.append(BuocKhoaSo("Khấu trừ thuế GTGT 3331 ↔ 1331", KHONG_AP_DUNG, "Thiếu thuế vào hoặc thuế ra", "C5.6"))
    elif co_dong(df, no=("3331",), co=("1331",)):
        ds.append(BuocKhoaSo("Khấu trừ thuế GTGT 3331 ↔ 1331", DA_LAM, f"Thuế vào {fmt_so(vao)} / thuế ra {fmt_so(ra)} — đã khấu trừ", "C5.6"))
    else:
        ds.append(BuocKhoaSo("Khấu trừ thuế GTGT 3331 ↔ 1331", CHUA_LAM, f"Thuế vào {fmt_so(vao)} / thuế ra {fmt_so(ra)} — chưa có bút toán khấu trừ", "C5.6"))

    if not (co_dong(df, no=("911",)) or co_dong(df, co=("911",))):
        ds.append(BuocKhoaSo("Kết chuyển lãi/lỗ 911 ↔ 421", KHONG_AP_DUNG, "Không có phát sinh 911", "C5.5"))
    elif co_dong(df, no=("911",), co=("421",)) or co_dong(df, no=("421",), co=("911",)):
        ds.append(BuocKhoaSo("Kết chuyển lãi/lỗ 911 ↔ 421", DA_LAM, "Đã có bút toán 911 ↔ 421", "C5.5"))
    else:
        ds.append(BuocKhoaSo("Kết chuyển lãi/lỗ 911 ↔ 421", CHUA_LAM, "Có 911 nhưng chưa kết chuyển sang 421", "C5.5"))

    c51 = ket_qua.get("C5.1")
    if c51 is None:
        ds.append(BuocKhoaSo("TK đầu 5/6/7/8 đã về 0 (kết chuyển hết)", KHONG_AP_DUNG, "Chưa chạy kiểm tra C5.1", "C5.1"))
    elif c51.so_loi == 0:
        ds.append(BuocKhoaSo("TK đầu 5/6/7/8 đã về 0 (kết chuyển hết)", DA_LAM, "Mọi TK doanh thu/chi phí đã về 0", "C5.1"))
    else:
        ds.append(BuocKhoaSo("TK đầu 5/6/7/8 đã về 0 (kết chuyển hết)", CAN_RA, f"Còn {c51.so_loi} tài khoản có net ≠ 0", "C5.1"))
    return ds


def loc_tong(df, no: tuple[str, ...], co: str) -> float:
    m = bat_dau(df["DebitAccount"], *no) & bat_dau(df["CreditAccount"], co)
    return float(df.loc[m, "Amount"].sum())
