from app.checks import g1_chung_tu as g1
from tests.conftest import tao_df


def _kq(df, ctx):
    return {r.ma: r for r in g1.kiem_tra(df, ctx)}


def test_du_6_ma_theo_thu_tu(ctx):
    assert [r.ma for r in g1.kiem_tra(tao_df([{}]), ctx)] == ["C1.1", "C1.2", "C1.3", "C1.4", "C1.5", "C1.6"]


def test_c11_thieu_dien_giai(ctx):
    df = tao_df([{"Description": None}, {"Description": "  "}, {"Description": "ok"}])
    assert _kq(df, ctx)["C1.1"].so_loi == 2


def test_c12_ngay_ngoai_ky(ctx):
    df = tao_df([{"DocDate": "2026-07-31"}, {"DocDate": "2026-08-31"}, {"DocDate": "2026-09-01"}])
    kq = _kq(df, ctx)["C1.2"]
    assert kq.so_loi == 2 and kq.muc_do == "do"


def test_c13_nghi_trung(ctx):
    r = {"DocNo": "X", "DebitAccount": "6421", "CreditAccount": "1111", "Amount": 5, "Description": "a"}
    df = tao_df([r, r, {**r, "Amount": 6}])
    assert _kq(df, ctx)["C1.3"].so_loi == 2


def test_c14_no_bang_co(ctx):
    df = tao_df([{"DebitAccount": "1111", "CreditAccount": "1111"}, {}])
    assert _kq(df, ctx)["C1.4"].so_loi == 1


def test_c15_so_tien_khong_duong(ctx):
    df = tao_df([{"Amount": 0}, {"Amount": -1}, {"Amount": 1}])
    assert _kq(df, ctx)["C1.5"].so_loi == 2


def test_c16_thieu_so_hoac_ngay(ctx):
    df = tao_df([{"DocNo": None}, {"DocDate": None}, {}])
    assert _kq(df, ctx)["C1.6"].so_loi == 2
