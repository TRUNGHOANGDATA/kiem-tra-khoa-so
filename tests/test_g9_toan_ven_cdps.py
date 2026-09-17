"""Nhóm 9 — Toàn vẹn Bảng cân đối số phát sinh (CĐPS).

Đây là lớp bằng chứng TRỰC TIẾP: sai các đẳng thức này là sổ sai chắc chắn, nên ĐỎ.
Chưa nạp CĐPS thì phải ĐỨNG NGOÀI (la_thong_ke), không được báo "đạt" giả.
"""
from app.checks import g9_toan_ven_cdps as g9
from app.checks.base import BoiCanh
from tests.conftest import tao_cdps, tao_df


def _kq(cdps, df=None):
    ctx = BoiCanh(ky_thang=8, ky_nam=2026, cdps=cdps)
    return {r.ma: r for r in g9.kiem_tra(df if df is not None else tao_df([{}]), ctx)}


def test_du_5_ma_theo_thu_tu():
    assert [r.ma for r in g9.kiem_tra(tao_df([{}]), BoiCanh(8, 2026))] == ["C9.1", "C9.2", "C9.3", "C9.4", "C9.5"]


def test_chua_nap_cdps_thi_dung_ngoai_khong_bao_dat():
    for r in g9.kiem_tra(tao_df([{}]), BoiCanh(8, 2026)):
        assert r.la_thong_ke is True and "Chưa nạp CĐPS" in r.ghi_chu


# ------------------------------------------------ C9.1 tổng Nợ = tổng Có
def test_c91_can_thi_khong_bao():
    cdps = tao_cdps([
        {"account": "1111", "du_dau_no": 100, "ps_no": 50, "du_cuoi_no": 150},
        {"account": "3311", "du_dau_co": 100, "ps_co": 50, "du_cuoi_co": 150},
    ])
    assert _kq(cdps)["C9.1"].so_loi == 0


def test_c91_nhom_long_nhau_khong_co_dong_con_van_duoc_cong():
    """Bẫy đã gặp trên CĐPS thật: 1388 mang is_group=True nhưng KHÔNG có dòng con nào
    trong file. Nếu lọc lá bằng cờ is_group thì mất 222 triệu -> báo nhầm 'không cân'.
    Dòng lá phải định nghĩa theo dữ liệu: tài khoản không có con nào trong bảng."""
    cdps = tao_cdps([
        {"account": "138", "du_cuoi_no": 100, "is_group": True, "level": 0},
        {"account": "1388", "du_cuoi_no": 100, "is_group": True, "level": 1},   # nhóm, không con
        {"account": "3311", "du_cuoi_co": 100},
    ])
    assert _kq(cdps)["C9.1"].so_loi == 0


def test_c91_tk_vua_co_phat_sinh_rieng_vua_co_con_van_duoc_cong():
    """Bẫy thứ hai trên CĐPS thật (A03/A04): 6272 là DÒNG PHÁT SINH (is_group=False)
    nhưng lại có con 62721. Hai dòng là hai khoản RIÊNG, cộng cả hai mới ra cha 627.
    Loại 6272 chỉ vì 'có con' sẽ hụt 150.394.609 -> C9.3 báo nhầm cha ≠ tổng con."""
    cdps = tao_cdps([
        {"account": "627", "ps_no": 300, "is_group": True, "level": 0},
        {"account": "6272", "ps_no": 200, "level": 1},       # dòng phát sinh, có con
        {"account": "62721", "ps_no": 100, "level": 1},
        {"account": "3311", "ps_co": 300},
    ])
    kq = _kq(cdps)
    assert kq["C9.1"].so_loi == 0 and kq["C9.3"].so_loi == 0


def test_c91_bo_qua_dong_tong_cong_khong_phai_tai_khoan():
    """CĐPS thật có dòng 'Tổng cộng:' với số hiệu TK rỗng — không phải tài khoản,
    không được tính vào tổng lẫn coi là TK cha."""
    cdps = tao_cdps([
        {"account": "1111", "du_cuoi_no": 100},
        {"account": "3311", "du_cuoi_co": 100},
        {"account": "", "ten": "Tổng cộng:", "du_cuoi_no": 100, "du_cuoi_co": 100, "is_group": True},
    ])
    kq = _kq(cdps)
    assert kq["C9.1"].so_loi == 0 and kq["C9.3"].so_loi == 0


def test_c91_lech_tong_thi_do():
    cdps = tao_cdps([
        {"account": "1111", "du_dau_no": 100, "du_cuoi_no": 100},
        {"account": "3311", "du_dau_co": 90, "du_cuoi_co": 90},   # lệch 10
    ])
    c91 = _kq(cdps)["C9.1"]
    assert c91.muc_do == "do" and c91.so_loi > 0


# ------------------------------------------------ C9.2 dư đầu + PS = dư cuối
def test_c92_bat_tk_khong_khop_dong_tien():
    cdps = tao_cdps([
        {"account": "1111", "du_dau_no": 100, "ps_no": 50, "ps_co": 20, "du_cuoi_no": 130},  # đúng
        {"account": "1121", "du_dau_no": 100, "ps_no": 50, "ps_co": 20, "du_cuoi_no": 999},  # sai
    ])
    c92 = _kq(cdps)["C9.2"]
    assert c92.muc_do == "do" and c92.so_loi == 1
    assert c92.chi_tiet["Tài khoản"].tolist() == ["1121"]


def test_c92_bo_qua_lech_duoi_1_dong():
    cdps = tao_cdps([{"account": "1111", "du_dau_no": 100, "du_cuoi_no": 100.4}])
    assert _kq(cdps)["C9.2"].so_loi == 0


# ------------------------------------------------ C9.3 TK cha = tổng TK con
def test_c93_cha_khac_tong_con():
    cdps = tao_cdps([
        {"account": "421", "du_cuoi_no": 500, "is_group": True, "level": 0},
        {"account": "4212", "du_cuoi_no": 300},                     # con chỉ 300
    ])
    c93 = _kq(cdps)["C9.3"]
    assert c93.muc_do == "do" and c93.so_loi == 1


def test_c93_cha_bang_tong_con_thi_im():
    cdps = tao_cdps([
        {"account": "421", "du_cuoi_no": 500, "is_group": True, "level": 0},
        {"account": "4211", "du_cuoi_no": 200},
        {"account": "4212", "du_cuoi_no": 300},
    ])
    assert _kq(cdps)["C9.3"].so_loi == 0


# ------------------------------------------------ C9.4 TK 5-9 phải về 0
def test_c94_tk_doanh_thu_chi_phi_con_du_thi_do():
    cdps = tao_cdps([
        {"account": "5111", "du_cuoi_co": 1000},      # chưa kết chuyển
        {"account": "6421", "du_cuoi_no": 0},         # sạch
        {"account": "1111", "du_cuoi_no": 5000},      # loại 1, không xét
    ])
    c94 = _kq(cdps)["C9.4"]
    assert c94.muc_do == "do" and c94.so_loi == 1
    assert c94.chi_tiet["Tài khoản"].tolist() == ["5111"]


def test_c94_tat_ca_ve_0_thi_im():
    cdps = tao_cdps([{"account": "5111"}, {"account": "911"}, {"account": "1111", "du_cuoi_no": 5000}])
    assert _kq(cdps)["C9.4"].so_loi == 0
