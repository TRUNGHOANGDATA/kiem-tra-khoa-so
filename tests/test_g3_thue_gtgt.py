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


def test_c32_bo_qua_giao_dich_noi_bo_theo_transcode(ctx):
    """Giao dịch nội bộ nhận theo MÃ LOẠI GIAO DỊCH (TransCode), không đoán theo số
    hiệu TK. Kế toán tổng hợp chốt 2026-09-21: 2303 = bán nội bộ, 2110 = điều chuyển
    nội bộ; ngoài hai mã đó mà thiếu 33311 là thiếu VAT THẬT.

    Đo trên sổ 08/2026, trong miền C3.2 xét: tiêu chí cũ (Nợ 136/336) bắt 639 dòng,
    TransCode bắt đúng 639 dòng ấy CỘNG 6 dòng nội bộ hạch toán qua 1311/1388 mà tiêu
    chí tài khoản bỏ lọt. Không dòng 136/336 nào nằm ngoài hai mã này.
    """
    df = tao_df([
        {"DocNo": "NB1", "DebitAccount": "1368", "CreditAccount": "51113",
         "TaxCode": "R10A", "TransCode": "2303"},
        {"DocNo": "NB2", "DebitAccount": "1388", "CreditAccount": "51123",
         "TaxCode": "R10A", "TransCode": "2110"},     # nội bộ nhưng KHÔNG phải 136/336
        {"DocNo": "KH1", "DebitAccount": "1311", "CreditAccount": "5111",
         "TaxCode": "R10A", "TransCode": "2301"},
    ])
    c = _kq(df, ctx)["C3.2"]
    assert c.so_loi == 1, "chỉ còn dòng bán cho khách hàng ngoài"
    assert c.chi_tiet.iloc[0]["DocNo"] == "KH1"


def test_c32_no_136_336_ma_khong_phai_ma_noi_bo_van_bi_bat(ctx):
    """Số hiệu TK KHÔNG còn là căn cứ: 1368 mà mã giao dịch là bán thường thì vẫn phải
    có thuế đầu ra. Đây là chỗ tiêu chí cũ sai chiều ngược lại."""
    df = tao_df([{"DocNo": "X", "DebitAccount": "1368", "CreditAccount": "5111",
                  "TaxCode": "R10A", "TransCode": "2301"}])
    assert _kq(df, ctx)["C3.2"].so_loi == 1


def test_c32_van_bat_khi_chung_tu_co_ca_noi_bo_lan_khach_ngoai(ctx):
    """Chứng từ lẫn cả hai vế: dòng nội bộ im, dòng khách ngoài vẫn phải bị bắt."""
    df = tao_df([
        {"DocNo": "MIX", "DebitAccount": "1368", "CreditAccount": "5111",
         "TaxCode": "R10A", "TransCode": "2303"},
        {"DocNo": "MIX", "DebitAccount": "1311", "CreditAccount": "5111",
         "TaxCode": "R10A", "TransCode": "2301"},
    ])
    c = _kq(df, ctx)["C3.2"]
    assert c.so_loi == 1 and c.chi_tiet.iloc[0]["DebitAccount"] == "1311"
