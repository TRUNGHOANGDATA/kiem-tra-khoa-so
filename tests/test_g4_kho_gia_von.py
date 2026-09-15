from app.checks import g4_kho_gia_von as g4
from tests.conftest import tao_df


def _kq(df, ctx):
    return {r.ma: r for r in g4.kiem_tra(df, ctx)}


def test_du_5_ma(ctx):
    assert [r.ma for r in g4.kiem_tra(tao_df([{}]), ctx)] == ["C4.1", "C4.2", "C4.3", "C4.4", "C4.5"]


def test_c41_xuat_kho_gia_0(ctx):
    df = tao_df([
        {"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 10, "UnitCost": 0, "Amount": 0},
        {"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 10, "UnitCost": 5, "Amount": 50},
        {"DebitAccount": "6421", "CreditAccount": "1111", "Quantity9": 0, "UnitCost": 0, "Amount": 9},
    ])
    kq = _kq(df, ctx)["C4.1"]
    assert kq.so_loi == 1 and kq.muc_do_thuc == "do"
    assert kq.chi_tiet["Amount"].tolist() == [0]  # đúng dòng đầu tiên (giá 0) bị gắn cờ, không phải dòng thứ 2


def test_c42_lech_tien_sl_x_don_gia(ctx):
    df = tao_df([
        {"CreditAccount": "1551", "Quantity9": 10, "UnitCost": 100.4, "Amount": 1004},
        {"CreditAccount": "1551", "Quantity9": 10, "UnitCost": 100, "Amount": 1500},
    ])
    assert _kq(df, ctx)["C4.2"].so_loi == 1


def test_c41_c42_ghi_chu_khi_khong_co_du_lieu_sl(ctx):
    """File Bravo không có cột Quantity9/UnitCost — loader điền 0.0, không được báo xanh giả."""
    df = tao_df([{"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 100}])
    kq41 = _kq(df, ctx)["C4.1"]
    kq42 = _kq(df, ctx)["C4.2"]
    assert kq41.so_loi == 0 and kq41.ghi_chu == g4.GHI_CHU_THIEU_SL
    assert kq42.so_loi == 0 and kq42.ghi_chu == g4.GHI_CHU_THIEU_SL


def test_c41_ghi_chu_chua_tinh_gia_khi_khong_dong_kho_nao_co_don_gia(ctx):
    """A1: có dòng kho kèm số lượng nhưng không một dòng nào có đơn giá -> nghi chưa tính giá."""
    df = tao_df([
        {"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 10, "UnitCost": 0, "Amount": 0},
        {"DebitAccount": "6214", "CreditAccount": "1552", "Quantity9": 5, "UnitCost": 0, "Amount": 0},
        {"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 9},
    ])
    kq = _kq(df, ctx)["C4.1"]
    assert kq.so_loi == 2 and kq.muc_do_thuc == "do"
    assert kq.ghi_chu == g4.GHI_CHU_CHUA_TINH_GIA


def test_c41_khong_ghi_chu_chua_tinh_gia_khi_co_dong_co_don_gia(ctx):
    """Chỉ một dòng kho có đơn giá là đủ để bác giả thiết 'chưa chạy tính giá cả kỳ'."""
    df = tao_df([
        {"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 10, "UnitCost": 0, "Amount": 0},
        {"DebitAccount": "1521", "CreditAccount": "3311", "Quantity9": 10, "UnitCost": 7, "Amount": 70},
    ])
    kq = _kq(df, ctx)["C4.1"]
    assert kq.so_loi == 1 and kq.ghi_chu == ""


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
    assert kq.so_loi == 1 and kq.chi_tiet["TK"].iloc[0] == "622" and kq.muc_do_thuc == "do"


def test_c44_khong_ap_dung_khi_khong_phat_sinh(ctx):
    assert _kq(tao_df([{}]), ctx)["C4.4"].so_loi == 0


def test_c44_ket_chuyen_mot_phan_ve_154(ctx):
    """621 mới kết chuyển 40/100 — còn dở dang 60, phải bị báo dù đã có bút toán Nợ 154 / Có 621."""
    df = tao_df([
        {"DebitAccount": "6211", "CreditAccount": "1521", "Amount": 100},
        {"DebitAccount": "154", "CreditAccount": "6211", "Amount": 40},
    ])
    kq = _kq(df, ctx)["C4.4"]
    assert kq.so_loi == 1
    row = kq.chi_tiet.iloc[0]
    assert row["TK"] == "621" and "60" in row["ly_do"]


def test_c45_chua_nhap_kho_thanh_pham(ctx):
    co = tao_df([{"DebitAccount": "154", "CreditAccount": "6214"},
                 {"DebitAccount": "1551", "CreditAccount": "154"}])
    thieu = tao_df([{"DebitAccount": "154", "CreditAccount": "6214"}])
    assert _kq(co, ctx)["C4.5"].so_loi == 0
    assert _kq(thieu, ctx)["C4.5"].so_loi == 1


def test_c45_chap_nhan_ban_thang_va_gui_ban(ctx):
    """154 -> 632 (bán thẳng) và 154 -> 157 (gửi bán) cũng là hoàn tất, không chỉ 154 -> 155."""
    ban_thang = tao_df([{"DebitAccount": "154", "CreditAccount": "6214"},
                        {"DebitAccount": "632", "CreditAccount": "154"}])
    gui_ban = tao_df([{"DebitAccount": "154", "CreditAccount": "6214"},
                      {"DebitAccount": "157", "CreditAccount": "154"}])
    assert _kq(ban_thang, ctx)["C4.5"].so_loi == 0
    assert _kq(gui_ban, ctx)["C4.5"].so_loi == 0


def test_so_sach_sach_thi_xanh(ctx):
    df = tao_df([{}])
    kq = _kq(df, ctx)
    assert all(kq[ma].muc_do_thuc == "xanh" for ma in ["C4.1", "C4.2", "C4.3", "C4.4", "C4.5"])
