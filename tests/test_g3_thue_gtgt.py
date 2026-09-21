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


def test_c32_bo_qua_doanh_thu_noi_bo_136_336(ctx):
    """Bán nội bộ (Nợ 1368/3368 / Có 511) KHÔNG phát sinh thuế GTGT đầu ra.

    Kế toán tổng hợp báo 2026-09-21. Đo trên sổ 08/2026: A05 có 104 dòng C3.2 thì 99
    là nội bộ, A03 4/4 và A06 14/14 đều nội bộ — cả ba chi nhánh này đã được xác nhận
    OK. Loại 136/336 thì A03 và A06 sạch hẳn, còn A01/A02/A08 giữ nguyên vì đối ứng là
    1311 (phải thu khách hàng thật) — đúng chỗ đáng rà.
    """
    df = tao_df([
        {"DocNo": "NB1", "DebitAccount": "1368", "CreditAccount": "51113", "TaxCode": "R10A"},
        {"DocNo": "NB2", "DebitAccount": "3368", "CreditAccount": "51123", "TaxCode": "R10A"},
        {"DocNo": "KH1", "DebitAccount": "1311", "CreditAccount": "5111", "TaxCode": "R10A"},
    ])
    c = _kq(df, ctx)["C3.2"]
    assert c.so_loi == 1, "chỉ còn dòng bán cho khách hàng ngoài"
    assert c.chi_tiet.iloc[0]["DocNo"] == "KH1"


def test_c32_van_bat_khi_chung_tu_co_ca_noi_bo_lan_khach_ngoai(ctx):
    """Chứng từ lẫn cả hai vế: dòng nội bộ im, dòng khách ngoài vẫn phải bị bắt."""
    df = tao_df([
        {"DocNo": "MIX", "DebitAccount": "1368", "CreditAccount": "5111", "TaxCode": "R10A"},
        {"DocNo": "MIX", "DebitAccount": "1311", "CreditAccount": "5111", "TaxCode": "R10A"},
    ])
    c = _kq(df, ctx)["C3.2"]
    assert c.so_loi == 1 and c.chi_tiet.iloc[0]["DebitAccount"] == "1311"
