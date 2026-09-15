from app.checks import g3_thue_gtgt as g3
from tests.conftest import tao_df


def _kq(df, ctx):
    return {r.ma: r for r in g3.kiem_tra(df, ctx)}


def test_c31_co_ma_thue_nhung_thieu_tk_thue(ctx):
    df = tao_df([
        {"DocNo": "A", "DebitAccount": "1521", "CreditAccount": "3311", "TaxCode": "V10"},   # thiếu
        {"DocNo": "B", "DebitAccount": "1521", "CreditAccount": "3311", "TaxCode": "V10"},
        {"DocNo": "B", "DebitAccount": "1331", "CreditAccount": "3311", "TaxCode": "V10"},   # đủ
        {"DocNo": "C", "DebitAccount": "6421", "CreditAccount": "1111", "TaxCode": "V00"},   # không chịu thuế
    ])
    assert _kq(df, ctx)["C3.1"].so_loi == 1


def test_c32_doanh_thu_thieu_thue_dau_ra(ctx):
    df = tao_df([
        {"DocNo": "S1", "DebitAccount": "1311", "CreditAccount": "5111", "TaxCode": "R10A"},   # thiếu 33311
        {"DocNo": "S2", "DebitAccount": "1311", "CreditAccount": "5111", "TaxCode": "R10A"},
        {"DocNo": "S2", "DebitAccount": "1311", "CreditAccount": "33311", "TaxCode": "R10A"},
    ])
    assert _kq(df, ctx)["C3.2"].so_loi == 1


def test_c33_bang_tong_hop_thue(ctx):
    df = tao_df([
        {"DebitAccount": "1331", "CreditAccount": "3311", "TaxCode": "V10", "Amount": 100},
        {"DebitAccount": "1311", "CreditAccount": "33311", "TaxCode": "R10A", "Amount": 200},
    ])
    kq = _kq(df, ctx)["C3.3"]
    assert kq.la_thong_ke and kq.so_loi == 0 and kq.muc_do_thuc == "xanh"
    b = kq.chi_tiet.set_index("TaxCode")
    assert b.loc["V10", "thue_vao_1331"] == 100 and b.loc["R10A", "thue_ra_33311"] == 200
