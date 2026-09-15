from app.checks import g2_dinh_khoan as g2
from tests.conftest import tao_df


def _kq(df, ctx):
    return {r.ma: r for r in g2.kiem_tra(df, ctx)}


def test_du_4_ma(ctx):
    assert [r.ma for r in g2.kiem_tra(tao_df([{}]), ctx)] == ["C2.1", "C2.2", "C2.3", "C2.4"]


def test_c21_thieu_doi_tuong_cong_no(ctx):
    df = tao_df([
        {"DebitAccount": "1311", "CustomerCode": None},
        {"CreditAccount": "3311", "CustomerCode": "NCC"},
        {"DebitAccount": "6421", "CustomerCode": None},
    ])
    assert _kq(df, ctx)["C2.1"].so_loi == 1


def test_c22_tk_sai_dinh_dang(ctx):
    df = tao_df([{"DebitAccount": "11"}, {"CreditAccount": "ABC"}, {}])
    assert _kq(df, ctx)["C2.2"].so_loi == 2


def test_c23_cung_nhom_tien(ctx):
    df = tao_df([{"DebitAccount": "1111", "CreditAccount": "1112"},
                 {"DebitAccount": "1121", "CreditAccount": "1122"},
                 {"DebitAccount": "1121", "CreditAccount": "1111"}])
    assert _kq(df, ctx)["C2.3"].so_loi == 2


def test_c24_lech_quy_doi_ngoai_te(ctx):
    df = tao_df([
        {"CurrencyCode": "USD", "OriginalAmount": 100, "ExchangeRate": 26000, "Amount": 2_600_000},
        {"CurrencyCode": "USD", "OriginalAmount": 100, "ExchangeRate": 26000, "Amount": 2_600_500},
        {"CurrencyCode": "VND", "OriginalAmount": 0, "ExchangeRate": 1, "Amount": 5},
    ])
    assert _kq(df, ctx)["C2.4"].so_loi == 1
