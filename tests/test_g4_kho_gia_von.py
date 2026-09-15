from app.checks import g4_kho_gia_von as g4
from tests.conftest import tao_df


def _kq(df, ctx):
    return {r.ma: r for r in g4.kiem_tra(df, ctx)}


def test_c41_xuat_kho_gia_0(ctx):
    df = tao_df([
        {"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 10, "UnitCost": 0, "Amount": 0},
        {"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 10, "UnitCost": 5, "Amount": 50},
        {"DebitAccount": "6421", "CreditAccount": "1111", "Quantity9": 0, "UnitCost": 0, "Amount": 9},
    ])
    kq = _kq(df, ctx)["C4.1"]
    assert kq.so_loi == 1 and kq.muc_do == "do"


def test_c42_lech_tien_sl_x_don_gia(ctx):
    df = tao_df([
        {"CreditAccount": "1551", "Quantity9": 10, "UnitCost": 100.4, "Amount": 1004},
        {"CreditAccount": "1551", "Quantity9": 10, "UnitCost": 100, "Amount": 1500},
    ])
    assert _kq(df, ctx)["C4.2"].so_loi == 1


def test_c43_gia_von_khong_di_kem_kho(ctx):
    df = tao_df([
        {"DebitAccount": "632111", "CreditAccount": "1551"},
        {"DebitAccount": "632111", "CreditAccount": "3311"},
    ])
    assert _kq(df, ctx)["C4.3"].so_loi == 1


def test_c44_chua_tap_hop_chi_phi_ve_154(ctx):
    df = tao_df([
        {"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100},
        {"DebitAccount": "154", "CreditAccount": "6214", "Amount": 100},
        {"DebitAccount": "6221", "CreditAccount": "3341", "Amount": 50},     # 622 chưa kết chuyển
    ])
    kq = _kq(df, ctx)["C4.4"]
    assert kq.so_loi == 1 and kq.chi_tiet["TK"].iloc[0] == "622" and kq.muc_do == "do"


def test_c44_khong_ap_dung_khi_khong_phat_sinh(ctx):
    assert _kq(tao_df([{}]), ctx)["C4.4"].so_loi == 0


def test_c45_chua_nhap_kho_thanh_pham(ctx):
    co = tao_df([{"DebitAccount": "154", "CreditAccount": "6214"},
                 {"DebitAccount": "1551", "CreditAccount": "154"}])
    thieu = tao_df([{"DebitAccount": "154", "CreditAccount": "6214"}])
    assert _kq(co, ctx)["C4.5"].so_loi == 0
    assert _kq(thieu, ctx)["C4.5"].so_loi == 1
