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
    c31 = _kq(df, ctx)["C3.1"]
    assert c31.la_thong_ke is True and len(c31.chi_tiet) == 1   # thống kê, vẫn liệt kê


def test_c32_doanh_thu_thieu_thue_dau_ra(ctx):
    df = tao_df([
        {"DocNo": "S1", "DebitAccount": "1311", "CreditAccount": "5111", "TaxCode": "R10A"},   # thiếu 33311
        {"DocNo": "S2", "DebitAccount": "1311", "CreditAccount": "5111", "TaxCode": "R10A"},
        {"DocNo": "S2", "DebitAccount": "1311", "CreditAccount": "33311", "TaxCode": "R10A"},
    ])
    assert _kq(df, ctx)["C3.2"].so_loi == 1


def test_c31_c32_gom_theo_ca_loai_va_so_chung_tu(ctx):
    """C1: hai quyển khác nhau trùng số CT — phiếu thiếu TK thuế không được núp bóng phiếu kia."""
    df = tao_df([
        {"DocCode": "PN", "DocNo": "001", "DebitAccount": "1521", "CreditAccount": "3311", "TaxCode": "V10"},
        {"DocCode": "PC", "DocNo": "001", "DebitAccount": "6421", "CreditAccount": "1111", "TaxCode": "V10"},
        {"DocCode": "PC", "DocNo": "001", "DebitAccount": "1331", "CreditAccount": "1111", "TaxCode": "V10"},
    ])
    kq = _kq(df, ctx)["C3.1"]
    assert len(kq.chi_tiet) == 1                           # chỉ PN/001 thiếu
    assert kq.chi_tiet["DebitAccount"].tolist() == ["1521"]

    dt = tao_df([
        {"DocCode": "HD", "DocNo": "77", "DebitAccount": "1311", "CreditAccount": "5111", "TaxCode": "R10A"},
        {"DocCode": "PX", "DocNo": "77", "DebitAccount": "1311", "CreditAccount": "5111", "TaxCode": "R10A"},
        {"DocCode": "PX", "DocNo": "77", "DebitAccount": "1311", "CreditAccount": "33311", "TaxCode": "R10A"},
    ])
    assert _kq(dt, ctx)["C3.2"].so_loi == 1                # chỉ HD/77 thiếu 33311


def test_c33_bang_tong_hop_thue(ctx):
    df = tao_df([
        {"DebitAccount": "1331", "CreditAccount": "3311", "TaxCode": "V10", "Amount": 100},
        {"DebitAccount": "1311", "CreditAccount": "33311", "TaxCode": "R10A", "Amount": 200},
    ])
    kq = _kq(df, ctx)["C3.3"]
    assert kq.la_thong_ke and kq.so_loi == 0 and kq.muc_do_thuc == "xanh"
    b = kq.chi_tiet.set_index("TaxCode")
    assert b.loc["V10", "thue_vao_1331"] == 100 and b.loc["R10A", "thue_ra_33311"] == 200
