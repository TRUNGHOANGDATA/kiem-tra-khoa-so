import pytest

from app import checks, trang_thai as tt
from tests.conftest import tao_df

# Mọi kịch bản dùng trong file này nằm ở một chỗ, để test bất biến D1 chạy được
# đúng trên tập kịch bản mà các test thường đang khẳng định.
KICH_BAN = {
    "mac_dinh": [{}],
    "khong_phat_sinh": [{"DebitAccount": "1111", "CreditAccount": "1121"}],
    "621_da_lam": [{"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100},
                   {"DebitAccount": "154", "CreditAccount": "6214", "Amount": 100}],
    "621_can_ra": [{"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100},
                   {"DebitAccount": "154", "CreditAccount": "6214", "Amount": 60}],
    "621_chua_lam": [{"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100}],
    "621_ket_chuyen_vuot": [{"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 200},
                            {"DebitAccount": "154", "CreditAccount": "6214", "Amount": 1000}],
    "621_thieu_800": [{"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 1000},
                      {"DebitAccount": "154", "CreditAccount": "6214", "Amount": 200}],
    "621_trong_nguong": [{"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 1000.0},
                         {"DebitAccount": "154", "CreditAccount": "6214", "Amount": 1000.4}],
    "kho_gia_0_va_pl_du": [
        {"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 1, "UnitCost": 0, "Amount": 0},
        # đã có dòng kho tính được giá -> không phải "cả kỳ chưa chạy tính giá" (A1)
        {"DebitAccount": "1521", "CreditAccount": "3311", "Quantity9": 2, "UnitCost": 5, "Amount": 10},
        {"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 10}],
    # 90/100 dòng xuất kho không có đơn giá -> trên ngưỡng tỷ lệ
    "chua_tinh_gia_xuat_kho": (
        [{"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 10, "UnitCost": 0, "Amount": 0}] * 90
        + [{"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 10, "UnitCost": 7, "Amount": 70}] * 10),
    # 70/100 -> dưới ngưỡng, chỉ là các dòng sót
    "sot_dong_xuat_chua_co_gia": (
        [{"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 10, "UnitCost": 0, "Amount": 0}] * 70
        + [{"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 10, "UnitCost": 7, "Amount": 70}] * 30),
    # Hồi quy gốc: Bravo không ghi đơn giá trên dòng xuất (UnitCost=0) nhưng Amount
    # đã mang giá trị thật -> KHÔNG được coi là "chưa tính giá xuất kho".
    "xuat_kho_amount_du_khong_don_gia": (
        [{"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 10, "UnitCost": 0, "Amount": 264_000}] * 100),
    # chỉ có phát sinh Có 621, không có Nợ 621 -> C4.4 không lập dòng nào
    "621_chi_co_ben_co": [{"DebitAccount": "1111", "CreditAccount": "6211", "Amount": 100}],
    # không có TK đầu 5/6/7/8 nào -> bước 11 không thể nói "đã về 0"
    "khong_co_tk_pl": [{"DebitAccount": "1111", "CreditAccount": "1121", "Amount": 100},
                       {"DebitAccount": "1311", "CreditAccount": "1111", "Amount": 50}],
    "lai_lo_va_thue": [{"DebitAccount": "911", "CreditAccount": "6421"},
                       {"DebitAccount": "911", "CreditAccount": "4212"},
                       {"DebitAccount": "1331", "CreditAccount": "3311"},
                       {"DebitAccount": "1311", "CreditAccount": "33311"}],
    "thue_co_bu_tru": [{"DebitAccount": "1331", "CreditAccount": "3311", "Amount": 500},
                       {"DebitAccount": "1311", "CreditAccount": "3331", "Amount": 500},
                       {"DebitAccount": "3331", "CreditAccount": "1331", "Amount": 500}],
    "thue_khong_bu_tru": [{"DebitAccount": "1331", "CreditAccount": "3311", "Amount": 500},
                          {"DebitAccount": "1311", "CreditAccount": "3331", "Amount": 500}],
    "622_627_da_lam": [{"DebitAccount": "6221", "CreditAccount": "3341", "Amount": 100},
                       {"DebitAccount": "154", "CreditAccount": "6221", "Amount": 100},
                       {"DebitAccount": "6271", "CreditAccount": "2141", "Amount": 50},
                       {"DebitAccount": "154", "CreditAccount": "6271", "Amount": 50}],
    "154_qua_632": [{"DebitAccount": "154", "CreditAccount": "621", "Amount": 100},
                    {"DebitAccount": "632", "CreditAccount": "154", "Amount": 100}],
    "154_qua_157": [{"DebitAccount": "154", "CreditAccount": "622", "Amount": 50},
                    {"DebitAccount": "157", "CreditAccount": "154", "Amount": 50}],
    "doanh_thu_du": [{"DebitAccount": "1311", "CreditAccount": "511", "Amount": 1_000_000_000},
                     {"DebitAccount": "511", "CreditAccount": "911", "Amount": 600_000_000}],
    "chi_phi_du": [{"DebitAccount": "642", "CreditAccount": "1111", "Amount": 1000},
                   {"DebitAccount": "911", "CreditAccount": "642", "Amount": 700}],
    "doanh_thu_het": [{"DebitAccount": "1311", "CreditAccount": "511", "Amount": 1000},
                      {"DebitAccount": "511", "CreditAccount": "911", "Amount": 1000}],
    "chi_phi_het": [{"DebitAccount": "642", "CreditAccount": "1111", "Amount": 500},
                    {"DebitAccount": "911", "CreditAccount": "642", "Amount": 500}],
    "chi_nhap_kho_155": [{"DebitAccount": "155", "CreditAccount": "154", "Amount": 100}],
}


def kb(ten: str):
    return tao_df(KICH_BAN[ten])


def _suy(df, ctx):
    kq = {r.ma: r for r in checks.chay_tat_ca(df, ctx)}
    return {b.buoc: b for b in tt.suy_trang_thai(df, kq)}, tt.suy_trang_thai(df, kq)


def b_ma(b):
    return b.ma_check


# --------------------------------------------------------------------------
# D1 — bất biến đã hỏng 5 lần trên nhánh này: Tab A nói "còn việc", bấm vào
#      thì bảng chứng minh trống rỗng, hoặc mã check được trích dẫn không tồn tại.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("ten", sorted(KICH_BAN))
def test_buoc_can_xu_ly_luon_tro_toi_bang_chung_co_that(ten, ctx):
    df = kb(ten)
    kq = {r.ma: r for r in checks.chay_tat_ca(df, ctx)}
    for b in tt.suy_trang_thai(df, kq):
        if b.trang_thai not in (tt.CHUA_LAM, tt.CAN_RA):
            continue
        assert b.ma_check in kq, f"[{ten}] bước '{b.buoc}' trích dẫn {b.ma_check} không có trong registry"
        so_dong = len(kq[b.ma_check].chi_tiet)
        if b.co_chung_cu:
            assert so_dong > 0, (
                f"[{ten}] bước '{b.buoc}' báo {b.trang_thai} và trỏ tới {b.ma_check},"
                f" nhưng {b.ma_check} không có dòng nào — kế toán bấm vào sẽ thấy bảng trống")
        else:
            # Hai ngoại lệ có chủ đích, đều vì C4.4 chỉ lập dòng khi ps_no > 0 và chỉ
            # bắt chiều thiếu (ps_no - ps_co > ngưỡng):
            #   1. kết chuyển vượt (net âm)      2. chỉ có phát sinh bên Có
            assert any(x in b.tom_tat for x in ("vượt", "bút toán bất thường")), (
                f"[{ten}] bước '{b.buoc}' bỏ chứng minh mà không thuộc hai ca đã khai báo:"
                f" {b.tom_tat!r}")
            assert so_dong == 0


def test_kich_ban_phu_du_nam_trang_thai(ctx):
    """Bất biến trên chỉ có giá trị nếu tập kịch bản thật sự chạm mọi trạng thái."""
    gap = set()
    for ten in KICH_BAN:
        df = kb(ten)
        kq = {r.ma: r for r in checks.chay_tat_ca(df, ctx)}
        gap |= {b.trang_thai for b in tt.suy_trang_thai(df, kq)}
    assert gap == {tt.DA_LAM, tt.CHUA_LAM, tt.CAN_RA, tt.KHONG_AP_DUNG, tt.TU_XAC_NHAN}


def test_co_kich_ban_ket_chuyen_vuot():
    """Chốt ca không-có-chứng-minh khỏi bị xóa mất khiến nhánh ngoại lệ thành vô nghĩa."""
    assert "621_ket_chuyen_vuot" in KICH_BAN


# --------------------------------------------------------------------------
def test_du_16_buoc_dung_thu_tu(ctx):
    _, ds = _suy(kb("mac_dinh"), ctx)
    assert len(ds) == 16
    assert ds[0].buoc.startswith("Khấu hao TSCĐ")
    assert ds[-1].buoc.startswith("TK đầu 5/6/7/8")
    assert [b.buoc for b in ds[3:6]] == [
        "Tập hợp CP NVL trực tiếp 621 → 154",
        "Tập hợp CP nhân công trực tiếp 622 → 154",
        "Tập hợp & phân bổ CP SXC 627 → 154"]
    assert any("thuế TNDN" in b.buoc for b in ds) and any("tỷ giá" in b.buoc for b in ds)


def test_buoc_nhac_dung_trang_thai_tu_xac_nhan(ctx):
    b, _ = _suy(kb("mac_dinh"), ctx)      # sổ mặc định không có 214
    assert b["Khấu hao TSCĐ (Có 214 → 627/641/642)"].trang_thai == tt.TU_XAC_NHAN


def test_buoc_moi_chiu_duoc_ket_qua_rong(ctx):
    ds = tt.suy_trang_thai(kb("mac_dinh"), {})     # chưa chạy kiểm tra -> khong KeyError
    assert len(ds) == 16
    assert all(b.trang_thai == tt.KHONG_AP_DUNG for b in ds if b.ma_check.startswith("C7."))


def test_khong_phat_sinh_thi_khong_ap_dung(ctx):
    b, _ = _suy(kb("khong_phat_sinh"), ctx)
    assert b["Tập hợp CP NVL trực tiếp 621 → 154"].trang_thai == tt.KHONG_AP_DUNG
    assert b["Kết chuyển giá vốn 632 → 911"].trang_thai == tt.KHONG_AP_DUNG


def test_621_da_lam_can_ra_chua_lam(ctx):
    k = "Tập hợp CP NVL trực tiếp 621 → 154"
    assert _suy(kb("621_da_lam"), ctx)[0][k].trang_thai == tt.DA_LAM
    ra = _suy(kb("621_can_ra"), ctx)[0][k]
    assert ra.trang_thai == tt.CAN_RA and "40" in ra.tom_tat
    chua = _suy(kb("621_chua_lam"), ctx)[0][k]
    assert chua.trang_thai == tt.CHUA_LAM and b_ma(chua) == "C4.4"


def test_xuat_kho_gia_va_tk_pl_ve_0(ctx):
    b, _ = _suy(kb("kho_gia_0_va_pl_du"), ctx)
    assert b[tt.BUOC_TINH_GIA_XUAT_KHO].trang_thai == tt.CAN_RA
    assert b["TK đầu 5/6/7/8 đã về 0 (kết chuyển hết)"].trang_thai == tt.CAN_RA


def test_lai_lo_va_thue(ctx):
    b, _ = _suy(kb("lai_lo_va_thue"), ctx)
    assert b["Kết chuyển lãi/lỗ 911 ↔ 421"].trang_thai == tt.DA_LAM
    assert b["Khấu trừ thuế GTGT 3331 ↔ 1331"].trang_thai == tt.CHUA_LAM


def test_vat_bare_3331_da_lam_va_chua_lam(ctx):
    """F3: check C5.6 dùng prefix '3331' (khớp cả sub-account 33311), step 9 phải khớp theo."""
    k = "Khấu trừ thuế GTGT 3331 ↔ 1331"
    assert _suy(kb("thue_co_bu_tru"), ctx)[0][k].trang_thai == tt.DA_LAM
    assert _suy(kb("thue_khong_bu_tru"), ctx)[0][k].trang_thai == tt.CHUA_LAM


def test_622_va_627_da_lam(ctx):
    """F7: bao phủ bước 2 (622 → 154) và bước 3 (627 → 154), trước đây không có assertion."""
    b, _ = _suy(kb("622_627_da_lam"), ctx)
    assert b["Tập hợp CP nhân công trực tiếp 622 → 154"].trang_thai == tt.DA_LAM
    assert b["Tập hợp & phân bổ CP SXC 627 → 154"].trang_thai == tt.DA_LAM


def test_154_dong_qua_632_va_157_da_lam(ctx):
    """F4/F7: bước 4 chấp nhận Nợ 632 hoặc Nợ 157 (không chỉ 155) đối ứng Có 154."""
    k = "Nhập kho thành phẩm 154 → 155 (tính giá thành)"
    assert _suy(kb("154_qua_632"), ctx)[0][k].trang_thai == tt.DA_LAM
    assert _suy(kb("154_qua_157"), ctx)[0][k].trang_thai == tt.DA_LAM


def test_nhom_ve_911_con_lai_thi_can_ra(ctx):
    """F1/F7: đóng một phần doanh thu/chi phí về 911 phải báo can_ra kèm số tiền còn lại."""
    b_dt, _ = _suy(kb("doanh_thu_du"), ctx)
    b_cp, _ = _suy(kb("chi_phi_du"), ctx)
    kdt = "Kết chuyển doanh thu 511/515/711 → 911"
    kcp = "Kết chuyển chi phí 635/641/642/811 → 911"
    assert b_dt[kdt].trang_thai == tt.CAN_RA and "400.000.000" in b_dt[kdt].tom_tat
    assert b_cp[kcp].trang_thai == tt.CAN_RA and "300" in b_cp[kcp].tom_tat


def test_nhom_ve_911_dong_het_thi_da_lam(ctx):
    """F1/F7: đảo ngược chiều kiểm tra (Nợ/Có) trong _nhom_ve_911 phải làm test này fail."""
    b_dt, _ = _suy(kb("doanh_thu_het"), ctx)
    b_cp, _ = _suy(kb("chi_phi_het"), ctx)
    assert b_dt["Kết chuyển doanh thu 511/515/711 → 911"].trang_thai == tt.DA_LAM
    assert b_cp["Kết chuyển chi phí 635/641/642/811 → 911"].trang_thai == tt.DA_LAM


def test_c41_co_ghi_chu_thi_khong_ap_dung(ctx):
    """F2/F7: C4.1 không kiểm tra được (thiếu dữ liệu số lượng) phải báo không_áp_dụng."""
    buoc = _suy(kb("chi_nhap_kho_155"), ctx)[0][tt.BUOC_TINH_GIA_XUAT_KHO]
    assert buoc.trang_thai == tt.KHONG_AP_DUNG
    assert "không kiểm tra được" in buoc.tom_tat


def test_ket_chuyen_vuot_noi_dung_dung_chieu(ctx):
    """B2: over-transfer — abs(net) báo "còn net -800", vô nghĩa và C4.4 lại rỗng."""
    buoc = _suy(kb("621_ket_chuyen_vuot"), ctx)[0]["Tập hợp CP NVL trực tiếp 621 → 154"]
    assert buoc.trang_thai == tt.CAN_RA
    assert "vượt 800" in buoc.tom_tat and "-800" not in buoc.tom_tat
    # C4.4 chỉ bắt chiều thiếu -> bước này không có bảng chứng minh, không cho bấm
    assert buoc.co_chung_cu is False


def test_ket_chuyen_thieu_van_bao_so_duong_va_co_chung_cu(ctx):
    buoc = _suy(kb("621_thieu_800"), ctx)[0]["Tập hợp CP NVL trực tiếp 621 → 154"]
    assert buoc.trang_thai == tt.CAN_RA and "còn 800" in buoc.tom_tat
    assert buoc.co_chung_cu is True


def test_ket_chuyen_trong_nguong_con_lai_thi_da_lam(ctx):
    """Dùng chung NGUONG_CON_LAI với các check, không phải 0.5 viết cứng."""
    assert _suy(kb("621_trong_nguong"), ctx)[0]["Tập hợp CP NVL trực tiếp 621 → 154"].trang_thai == tt.DA_LAM


def test_chua_tinh_gia_xuat_kho_thi_chua_lam(ctx):
    """A1: phần lớn dòng xuất chưa có giá -> MỘT việc phải làm, không phải N lỗi rời rạc."""
    buoc = _suy(kb("chua_tinh_gia_xuat_kho"), ctx)[0][tt.BUOC_TINH_GIA_XUAT_KHO]
    assert buoc.trang_thai == tt.CHUA_LAM
    assert buoc.tom_tat == ("Chưa tính giá xuất kho bình quân cuối kỳ"
                            " — 90/100 dòng xuất kho chưa có giá trị")
    assert buoc.ma_check == "C4.1" and buoc.co_chung_cu is True


def test_amount_du_khong_don_gia_thi_da_lam(ctx):
    """Hồi quy: UnitCost=0 trên toàn bộ dòng xuất không còn khiến bước 5 báo
    chưa_lam nếu Amount đã mang giá trị thật — đúng hình dạng dữ liệu Bravo thật."""
    buoc = _suy(kb("xuat_kho_amount_du_khong_don_gia"), ctx)[0][tt.BUOC_TINH_GIA_XUAT_KHO]
    assert buoc.trang_thai == tt.DA_LAM


def test_buoc_tinh_gia_dem_dong_xuat_khong_dem_ca_dong_nhap(ctx):
    """Bước này nói về giá XUẤT kho, nên con số đi kèm phải là số dòng xuất.
    Gộp cả dòng nhập vào mẫu số là nêu một con số không trả lời câu đang hỏi
    (trên sổ 08/2026: 46.522 dòng kho nhưng chỉ 32.519 dòng xuất)."""
    df = tao_df(
        [{"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 1, "Amount": 100}] * 3
        + [{"DebitAccount": "1521", "CreditAccount": "3311", "Quantity9": 5, "Amount": 500}] * 7)
    buoc = _suy(df, ctx)[0][tt.BUOC_TINH_GIA_XUAT_KHO]
    assert buoc.trang_thai == tt.DA_LAM
    assert buoc.tom_tat == "3 dòng xuất kho, mọi dòng đều đã có giá trị"


def test_duoi_nguong_ty_le_thi_van_la_can_ra(ctx):
    """A1 chiều còn lại: 70/100 chưa đủ để kết luận cả kỳ chưa chạy tính giá."""
    buoc = _suy(kb("sot_dong_xuat_chua_co_gia"), ctx)[0][tt.BUOC_TINH_GIA_XUAT_KHO]
    assert buoc.trang_thai == tt.CAN_RA
    assert "Còn 70 dòng kho" in buoc.tom_tat


def test_chi_co_phat_sinh_ben_co_thi_khong_goi_la_chua_ket_chuyen(ctx):
    """Latent 1: không có Nợ 621 thì không có gì để tập hợp — C4.4 cũng không lập dòng."""
    buoc = _suy(kb("621_chi_co_ben_co"), ctx)[0]["Tập hợp CP NVL trực tiếp 621 → 154"]
    assert buoc.trang_thai == tt.CAN_RA            # trước đây: chua_lam kèm bảng rỗng
    assert "Không có phát sinh Nợ 621" in buoc.tom_tat
    assert buoc.co_chung_cu is False


def test_khong_co_tk_5678_thi_buoc_11_khong_ap_dung(ctx):
    """Latent 2: không có TK doanh thu/chi phí nào thì không thể nói 'đã về 0'."""
    buoc = _suy(kb("khong_co_tk_pl"), ctx)[0]["TK đầu 5/6/7/8 đã về 0 (kết chuyển hết)"]
    assert buoc.trang_thai == tt.KHONG_AP_DUNG
    assert "không có phát sinh TK đầu 5/6/7/8" in buoc.tom_tat


def test_thieu_ket_qua_kiem_tra_thi_khong_ap_dung(ctx):
    """F5/F7: nếu ket_qua không có C4.1/C5.1 (chưa chạy kiểm tra), không được coi là đã làm."""
    df = kb("mac_dinh")
    b = {buoc.buoc: buoc for buoc in tt.suy_trang_thai(df, {})}
    assert b[tt.BUOC_TINH_GIA_XUAT_KHO].trang_thai == tt.KHONG_AP_DUNG
    assert b["TK đầu 5/6/7/8 đã về 0 (kết chuyển hết)"].trang_thai == tt.KHONG_AP_DUNG


def test_tu_xac_nhan_khong_tinh_vao_ket_luan(ctx):
    """Trạng thái nhắc không được kéo sổ sạch ra khỏi 'SẴN SÀNG KHÓA SỔ'."""
    b = tt.BuocKhoaSo("X", tt.TU_XAC_NHAN, "chưa thấy", "C7.1")
    kl = tt.tinh_ket_luan([], [b])
    assert kl["muc_do_ket_luan"] == tt.SAN_SANG and kl["con_viec"] == 0
