"""Nhóm 4 — Kho & giá vốn (đặc thù sản xuất)."""
import pandas as pd

from .base import (DO, VANG, NGUONG_CON_LAI, TK_KHO, BoiCanh, CheckResult, bat_dau, co_dong,
                    fmt_sl, fmt_so, phat_sinh_theo_prefix, tao_ket_qua)

NHOM = "G4"
TK_CO_HOP_LE_GIA_VON = ("152", "153", "154", "155", "156", "157", "627", "2294", "1381")
TK_CHI_PHI_SX = ("621", "622", "627")
GHI_CHU_THIEU_SL = "File không có dữ liệu số lượng/đơn giá — không kiểm tra được giá xuất kho"
GHI_CHU_CHUA_TINH_GIA = ("Nghi chưa chạy tính giá xuất kho bình quân cuối kỳ "
                         "— phần lớn dòng xuất kho chưa có giá trị")
TY_LE_NGHI_CHUA_TINH_GIA = 0.8   # tỷ lệ dòng xuất kho không có giá trị đủ để nghi chưa chạy tính giá
SO_DONG_XUAT_TOI_THIEU = 100     # dưới mức này tỷ lệ không nói lên điều gì

# --- C4.6: đơn giá xuất kho lệch hẳn khỏi mặt bằng của chính mã hàng đó ---
LAN_LECH_DON_GIA = 10      # gấp/kém từng này lần so với trung vị của mã hàng thì nêu ra
SO_LAN_XUAT_TOI_THIEU = 3  # dưới 3 lần xuất thì "trung vị của mã hàng" chưa phải mặt bằng
COT_C46 = ["DocNo", "DocDate", "ItemCode", "ItemName", "WarehouseName",
           "Quantity9", "Amount", "don_gia", "don_gia_pho_bien", "so_lan_xuat", "ly_do"]


def _so(s: pd.Series) -> pd.Series:
    """Chuỗi số đã định dạng. astype("string") là bắt buộc: trên frame rỗng, .map()
    giữ nguyên dtype float64 và phép nối "chuỗi" + Series float sẽ nổ _UFuncNoLoopError."""
    return s.map(fmt_so).astype("string")


def _sl(s: pd.Series) -> pd.Series:
    """Chuỗi số lượng đã định dạng (giữ phần thập phân) — xem fmt_sl."""
    return s.map(fmt_sl).astype("string")


def _bang_tong_hop(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["TK", "ps_no", "ps_co", "ly_do"])


def thong_ke_xuat_kho(df: pd.DataFrame) -> tuple[int, int]:
    """(số dòng xuất kho có SL mà chưa có giá trị, tổng số dòng xuất kho có SL).

    Dùng Amount, không dùng UnitCost: Bravo không ghi đơn giá trên dòng xuất kho —
    giá vốn bình quân cuối kỳ được ghi thẳng vào Amount, không restated thành đơn
    giá/dòng. UnitCost = 0 trên dòng xuất không có nghĩa gì; Amount mới là cột
    mang câu trả lời "giá xuất kho đã được xác định hay chưa".

    Chỉ đếm dòng XUẤT (Có TK kho): dòng nhập mang giá mua nên luôn có giá trị,
    gộp chung vào mẫu số sẽ pha loãng tỷ lệ và che mất việc chưa chạy tính giá.

    "Chưa có giá trị" là Amount ĐÚNG BẰNG 0, không phải Amount <= 0 — xem C4.1.
    Tử số phải dùng cùng một vị từ với C4.1, nếu không tỷ lệ hệ thống lại đếm
    các dòng điều chỉnh âm mà bảng chứng minh của C4.1 không còn liệt kê.
    """
    xuat = bat_dau(df["CreditAccount"], *TK_KHO) & (df["Quantity9"] > 0)
    return int((xuat & (df["Amount"] == 0)).sum()), int(xuat.sum())


def nghi_chua_tinh_gia(df: pd.DataFrame) -> bool:
    """Phần lớn dòng xuất kho không có giá trị -> nghi chưa chạy tính giá bình quân cuối kỳ.

    Là MỘT việc phải làm, không phải hàng chục nghìn lỗi rời rạc. Dùng tỷ lệ chứ không
    đòi tuyệt đối: trên sổ thật vẫn có một thiểu số dòng xuất mang giá trị đích danh.
    """
    chua_gia, tong = thong_ke_xuat_kho(df)
    return tong >= SO_DONG_XUAT_TOI_THIEU and chua_gia / tong >= TY_LE_NGHI_CHUA_TINH_GIA


def kiem_tra(df: pd.DataFrame, ctx: BoiCanh) -> list[CheckResult]:
    kq = []
    dong_kho = bat_dau(df["DebitAccount"], *TK_KHO) | bat_dau(df["CreditAccount"], *TK_KHO)
    co_sl = dong_kho & (df["Quantity9"] > 0)
    khong_co_du_lieu_sl = not bool((df["Quantity9"] > 0).any())
    ghi_chu_sl = GHI_CHU_THIEU_SL if khong_co_du_lieu_sl else ""

    ghi_chu_c41 = GHI_CHU_CHUA_TINH_GIA if nghi_chua_tinh_gia(df) else ghi_chu_sl

    # Amount, không phải UnitCost, là cột quyết định "đã xác định giá trị hay chưa":
    # Bravo ghi thẳng giá vốn bình quân cuối kỳ vào Amount trên dòng xuất, không
    # restated thành đơn giá/dòng — UnitCost = 0 trên dòng xuất là bình thường và
    # không nói lên điều gì. Chỉ dòng thật sự không có Amount mới là chưa định giá.
    #
    # ĐÚNG BẰNG 0, không phải <= 0. Số tiền ÂM là một giá trị — bút toán đảo/điều
    # chỉnh (trên sổ 08/2026: 10 dòng PX "TĐ từ phiếu TP số: TP…", Nợ 6214 / Có 1521,
    # từ -41.722 đến -2.748). Gọi chúng là "chưa xác định giá trị" là sai sự thật với
    # từng dòng một. Số tiền âm không mất khỏi báo cáo: C1.5 "Số tiền ≤ 0" đã liệt kê
    # toàn bộ 243 dòng như vậy của file để rà soát.
    gia_0 = co_sl & (df["Amount"] == 0)
    ly_do_c41 = ("Có SL " + _sl(df["Quantity9"]) + " nhưng tiền = " + _so(df["Amount"]) +
                 " — có số lượng nhưng chưa xác định giá trị (chưa tính giá xuất kho)")
    kq.append(tao_ket_qua(df[gia_0], "C4.1", "Xuất/nhập kho chưa có giá trị", NHOM, DO,
                          ly_do_c41[gia_0], ghi_chu=ghi_chu_c41))

    # Chỉ xét được dòng có đơn giá (UnitCost > 0) — thiểu số trong dữ liệu thật, vì
    # Bravo không ghi đơn giá trên phần lớn dòng xuất kho (xem C4.1). Tên check nêu
    # rõ phạm vi này để không bị hiểu nhầm là đã đối chiếu toàn bộ dòng kho.
    co_gia = co_sl & (df["UnitCost"] > 0)
    tien_tinh = df["Quantity9"] * df["UnitCost"]
    lech = (df["Amount"] - tien_tinh).abs() > (df["Amount"].abs() * 0.001 + 1)
    ly_do_c42 = ("SL " + _sl(df["Quantity9"]) + " × đơn giá " + _so(df["UnitCost"]) +
                 " = " + _so(tien_tinh) + " nhưng Amount ghi " + _so(df["Amount"]) +
                 " — lệch vượt ngưỡng làm tròn 0,1% + 1đ")
    r42 = tao_ket_qua(df[co_gia & lech], "C4.2",
                      "Tiền ≠ Số lượng × Đơn giá (chỉ dòng có đơn giá > 0)", NHOM, VANG,
                      ly_do_c42[co_gia & lech], ghi_chu=ghi_chu_sl)
    r42.la_thong_ke = True   # lệch có thể do đơn giá bình quân Bravo -> chỉ để soát
    kq.append(r42)

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
    kq.append(don_gia_bat_thuong(df))
    return kq


def don_gia_bat_thuong(df: pd.DataFrame) -> CheckResult:
    """C4.6 — đơn giá xuất kho lệch hẳn khỏi mặt bằng của chính mã hàng đó.

    Bravo không ghi đơn giá trên dòng xuất (xem C4.1), nên đơn giá phải suy ra bằng
    tiền ÷ số lượng. Không có ngưỡng tuyệt đối nào dùng được: trên sổ 08/2026 dòng
    đắt nhất là 2.347.789.345đ/đơn vị, và nó hoàn toàn hợp lệ — một TSCĐ (mã
    TSCCDC129) xuất 1 đơn vị. Mốc so sánh duy nhất có nghĩa là TRUNG VỊ CỦA CHÍNH
    MÃ HÀNG ĐÓ trong kỳ; sai đơn vị tính hay gõ nhầm số lượng lộ ra ở đó chứ không
    lộ ra ở con số tuyệt đối.

    Trung vị, không phải trung bình: một dòng sai lệch 251 lần kéo trung bình lên
    theo mình rồi tự che mất. Mã hàng xuất dưới 3 lần thì chưa có mặt bằng để so —
    bỏ qua và nói rõ trong ghi chú, không im lặng coi như đã soi.
    """
    xuat = (bat_dau(df["CreditAccount"], *TK_KHO) & (df["Quantity9"] > 0)
            & (df["Amount"] > 0) & df["ItemCode"].notna())
    s = df[xuat]
    bo_qua = 0
    if len(s):
        don_gia = s["Amount"] / s["Quantity9"]
        nhom = don_gia.groupby(s["ItemCode"])
        pho_bien = nhom.transform("median")
        so_lan = nhom.transform("size")
        du_mau = so_lan >= SO_LAN_XUAT_TOI_THIEU
        bo_qua = int((~du_mau).sum())
        ty_le = don_gia / pho_bien.where(pho_bien > 0)
        lech = du_mau & ((ty_le >= LAN_LECH_DON_GIA) | (ty_le <= 1 / LAN_LECH_DON_GIA))
        ct = s.loc[lech, ["DocNo", "DocDate", "ItemCode", "ItemName", "WarehouseName",
                          "Quantity9", "Amount"]].copy()
        ct["don_gia"] = don_gia[lech]
        ct["don_gia_pho_bien"] = pho_bien[lech]
        ct["so_lan_xuat"] = so_lan[lech].astype(int)
        ct["ly_do"] = ("Đơn giá suy ra " + _so(don_gia[lech]) +
                       " — " + ty_le[lech].map(_gap_may_lan).astype("string") +
                       " đơn giá phổ biến " + _so(pho_bien[lech]) +
                       " của mã hàng này (" + so_lan[lech].astype(int).astype("string") +
                       " lần xuất trong kỳ). Kiểm tra lại số lượng và đơn vị tính.")
        ct = ct.reset_index(drop=True)
    else:
        ct = pd.DataFrame(columns=COT_C46)
    ghi_chu = (f"Chỉ so được mã hàng xuất từ {SO_LAN_XUAT_TOI_THIEU} lần trở lên trong kỳ"
               f" — {bo_qua} dòng chưa đủ cơ sở so sánh" if bo_qua else "")
    return CheckResult("C4.6", "Đơn giá xuất kho lệch mặt bằng mã hàng", NHOM, VANG, ct, ghi_chu)


def _gap_may_lan(ty_le: float) -> str:
    """"gấp 251 lần" / "chỉ bằng 1/12" — nói theo chiều lệch, không bắt người đọc
    tự nghịch đảo một tỉ số 0,0039."""
    if ty_le >= 1:
        return f"gấp {ty_le:,.0f} lần".replace(",", ".")
    return f"chỉ bằng 1/{1 / ty_le:,.0f}".replace(",", ".")
