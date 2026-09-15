from app.checks import g5_ket_chuyen as g5
from tests.conftest import tao_df


def _kq(df, ctx):
    return {r.ma: r for r in g5.kiem_tra(df, ctx)}


def test_du_6_ma(ctx):
    assert [r.ma for r in g5.kiem_tra(tao_df([{}]), ctx)] == ["C5.1", "C5.2", "C5.3", "C5.4", "C5.5", "C5.6"]


def test_c51_tk_5678_chua_ve_0(ctx):
    df = tao_df([
        {"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 300},
        {"DebitAccount": "911", "CreditAccount": "6421", "Amount": 300},     # đã kết chuyển hết
        {"DebitAccount": "6418", "CreditAccount": "1111", "Amount": 50},     # chưa
        {"DebitAccount": "1311", "CreditAccount": "5111", "Amount": 1000},   # chưa
    ])
    kq = _kq(df, ctx)["C5.1"]
    assert sorted(kq.chi_tiet["TK"]) == ["5111", "6418"] and kq.muc_do_thuc == "vang"


def test_c52_thieu_ket_chuyen_gia_von(ctx):
    thieu = tao_df([{"DebitAccount": "632111", "CreditAccount": "1551"}])
    du = tao_df([{"DebitAccount": "632111", "CreditAccount": "1551"},
                 {"DebitAccount": "911", "CreditAccount": "632111"}])
    assert _kq(thieu, ctx)["C5.2"].so_loi == 1 and _kq(thieu, ctx)["C5.2"].muc_do_thuc == "do"
    assert _kq(du, ctx)["C5.2"].so_loi == 0


def test_c53_thieu_ket_chuyen_doanh_thu_theo_tk(ctx):
    df = tao_df([
        {"DebitAccount": "1311", "CreditAccount": "5111"},
        {"DebitAccount": "5111", "CreditAccount": "911"},
        {"DebitAccount": "1121", "CreditAccount": "5151"},      # 515 chưa kết chuyển
    ])
    kq = _kq(df, ctx)["C5.3"]
    assert kq.chi_tiet["TK"].tolist() == ["515"]


def test_c54_thieu_ket_chuyen_chi_phi(ctx):
    df = tao_df([{"DebitAccount": "6421", "CreditAccount": "1111"},
                 {"DebitAccount": "63541", "CreditAccount": "1121"},
                 {"DebitAccount": "911", "CreditAccount": "6421"}])
    assert _kq(df, ctx)["C5.4"].chi_tiet["TK"].tolist() == ["635"]


def test_c53_ket_chuyen_mot_phan_doanh_thu(ctx):
    """511 chỉ mới kết chuyển 600/1000 — còn dở 400, phải bị báo dù đã có Nợ 511 / Có 911."""
    df = tao_df([
        {"DebitAccount": "1311", "CreditAccount": "5111", "Amount": 1000},
        {"DebitAccount": "5111", "CreditAccount": "911", "Amount": 600},
    ])
    kq = _kq(df, ctx)["C5.3"]
    assert kq.chi_tiet["TK"].tolist() == ["511"]
    assert "400" in kq.chi_tiet["ly_do"].iloc[0]


def test_c54_ket_chuyen_mot_phan_chi_phi(ctx):
    """642 chỉ mới kết chuyển 200/500 — còn dở 300, phải bị báo dù đã có Nợ 911 / Có 642."""
    df = tao_df([
        {"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 500},
        {"DebitAccount": "911", "CreditAccount": "6421", "Amount": 200},
    ])
    kq = _kq(df, ctx)["C5.4"]
    assert kq.chi_tiet["TK"].tolist() == ["642"]
    assert "300" in kq.chi_tiet["ly_do"].iloc[0]


def test_c55_thieu_ket_chuyen_lai_lo(ctx):
    thieu = tao_df([{"DebitAccount": "911", "CreditAccount": "6421"}])
    du_lai = tao_df([{"DebitAccount": "911", "CreditAccount": "6421"},
                     {"DebitAccount": "911", "CreditAccount": "4212"}])
    du_lo = tao_df([{"DebitAccount": "911", "CreditAccount": "6421"},
                    {"DebitAccount": "4212", "CreditAccount": "911"}])
    assert _kq(thieu, ctx)["C5.5"].so_loi == 1
    assert _kq(du_lai, ctx)["C5.5"].so_loi == 0 and _kq(du_lo, ctx)["C5.5"].so_loi == 0


def test_c56_thieu_khau_tru_thue(ctx):
    thieu = tao_df([{"DebitAccount": "1331", "CreditAccount": "3311"},
                    {"DebitAccount": "1311", "CreditAccount": "33311"}])
    du = tao_df([*[{"DebitAccount": "1331", "CreditAccount": "3311"},
                   {"DebitAccount": "1311", "CreditAccount": "33311"}],
                 {"DebitAccount": "33311", "CreditAccount": "1331"}])
    assert _kq(thieu, ctx)["C5.6"].so_loi == 1 and _kq(du, ctx)["C5.6"].so_loi == 0


def test_c56_nhan_dien_tk_33312_bang_prefix_3331(ctx):
    """Bảng TK dùng 33312 (thuế GTGT hàng NK) thay vì 33311 vẫn phải được nhận diện qua prefix 3331."""
    df = tao_df([{"DebitAccount": "1331", "CreditAccount": "3311"},
                 {"DebitAccount": "1311", "CreditAccount": "33312"}])
    assert _kq(df, ctx)["C5.6"].so_loi == 1


def test_so_sach_sach_thi_xanh(ctx):
    df = tao_df([{"DebitAccount": "1111", "CreditAccount": "1121", "Amount": 100}])
    kq = _kq(df, ctx)
    assert all(kq[ma].muc_do_thuc == "xanh" for ma in ["C5.1", "C5.2", "C5.3", "C5.4", "C5.5", "C5.6"])
