from app.checks import g3_thue_gtgt as g3
from dataclasses import replace

from tests.conftest import tao_df, tao_sbh


def _kq(df, ctx, sbh=None):
    if sbh is not None:
        ctx = replace(ctx, so_ban_hang=sbh)
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


def test_c33_bang_tong_hop_thue(ctx):
    df = tao_df([
        {"DebitAccount": "1331", "CreditAccount": "3311", "TaxCode": "V10", "Amount": 100},
        {"DebitAccount": "1311", "CreditAccount": "33311", "TaxCode": "R10A", "Amount": 200},
    ])
    kq = _kq(df, ctx)["C3.3"]
    assert kq.la_thong_ke and kq.so_loi == 0 and kq.muc_do_thuc == "xanh"
    b = kq.chi_tiet.set_index("TaxCode")
    assert b.loc["V10", "thue_vao_1331"] == 100 and b.loc["R10A", "thue_ra_33311"] == 200


# ---------------- C3.2 / C3.4: đọc SỔ CHI TIẾT BÁN HÀNG, từng dòng hàng ----------------

def test_c32_bat_dong_thue_0_trong_chung_tu_co_thue_mot_phan(ctx):
    """Nguyên nhân gốc #1 của check cũ: hóa đơn CÓ dòng 33311 nhưng một dòng hàng thuế 0
    (A01 09/2026 `0051998`). Mức chứng từ cho qua; mức dòng hàng phải bắt đúng dòng đó."""
    sbh = tao_sbh([
        {"ItemCode": "H101PK0000072", "Amount2": 1_386_000, "Amount3": 0},
        {"ItemCode": "H205ON0005001", "Amount2": 36_634_630, "Amount3": 2_930_770},
    ])
    c = _kq(tao_df([]), ctx, sbh)["C3.2"]
    assert c.so_loi == 1 and c.chi_tiet.iloc[0]["ItemCode"] == "H101PK0000072"
    assert c.muc_do_thuc == "vang" and not c.la_thong_ke


def test_c32_khong_xet_taxcode_dong_trong_ma_thue_van_bi_bat(ctx):
    """Nguyên nhân gốc #2: dòng không gắn mã thuế (khách FOD, 74,4 tr) bị check cũ loại vì
    đòi TaxCode chịu thuế. Sổ bán hàng không có TaxCode — thuế 0 là đủ để bắt."""
    sbh = tao_sbh([{"TransCode": "2304", "CustomerName": "Công ty cổ phần FOD", "Amount3": 0}])
    assert _kq(tao_df([]), ctx, sbh)["C3.2"].so_loi == 1


def test_c32_hang_tang_gia_0_khong_bat(ctx):
    sbh = tao_sbh([{"UnitPrice": 0, "Amount2": 0, "Amount3": 0}])
    assert _kq(tao_df([]), ctx, sbh)["C3.2"].so_loi == 0


def test_c32_chi_xet_doi_ung_131(ctx):
    """Bán chi nhánh Nợ 1368/Có 511 không thuộc diện — chỉ Nợ 131."""
    sbh = tao_sbh([{"DebitAccount2": "1368", "CreditAccount2": "51113", "Amount3": 0}])
    assert _kq(tao_df([]), ctx, sbh)["C3.2"].so_loi == 0


def test_c32_bo_qua_giao_dich_chi_nhanh_theo_transcode(ctx):
    """Nội bộ nhận theo TransCode, kể cả khi hạch toán qua 1311 (chốt 21/09). 2304 là
    'Công ty nội bộ' = pháp nhân khác → VẪN bị bắt."""
    sbh = tao_sbh([
        {"DocNo": "NB1", "TransCode": "2303", "Amount3": 0},
        {"DocNo": "NB2", "TransCode": "2110", "Amount3": 0},
        {"DocNo": "CTY", "TransCode": "2304", "Amount3": 0},
    ])
    c = _kq(tao_df([]), ctx, sbh)["C3.2"]
    assert c.chi_tiet["DocNo"].tolist() == ["CTY"]


def test_c32_giu_ma_2110_du_hien_chua_khop_dong_nao():
    """2110 phải nằm trong danh sách dù sổ 08/2026 chưa có dòng nào lọt vào diện C3.2.
    Người dùng chốt 2026-09-21: "2110 chưa có nhưng tương lai sẽ có" — không phải code chết."""
    assert "2110" in g3.TRANSCODE_NOI_BO


def test_c34_tra_lai_131_thue_0_bi_bat(ctx):
    sbh = tao_sbh([
        {"DocCode": "TL", "DocNo": "NM2609-000806", "TransCode": "2107",
         "DebitAccount2": "52131", "CreditAccount2": "1311",
         "Quantity": -120, "Amount2": -1_320_000, "Amount3": 0},
        {"DocCode": "TL", "DocNo": "NM2609-000900", "TransCode": "2107",
         "DebitAccount2": "52131", "CreditAccount2": "1311",
         "Quantity": -10, "Amount2": -1_000_000, "Amount3": -80_000},       # có giảm thuế
    ])
    kq = _kq(tao_df([]), ctx, sbh)
    assert kq["C3.4"].chi_tiet["DocNo"].tolist() == ["NM2609-000806"]
    assert kq["C3.2"].so_loi == 0, "trả lại không được lọt sang C3.2"


def test_c34_tra_lai_chi_nhanh_doi_ung_1368_khong_bat(ctx):
    """Trả lại nội bộ Nợ 52133/Có 1368 (TransCode 2110) — không bao giờ có thuế."""
    sbh = tao_sbh([{"DocCode": "TL", "TransCode": "2110", "DebitAccount2": "52133",
                    "CreditAccount2": "1368", "Amount2": -5_000_000, "Amount3": 0}])
    assert _kq(tao_df([]), ctx, sbh)["C3.4"].so_loi == 0


def test_c34_ban_thue_0_khong_lot_sang_c34(ctx):
    sbh = tao_sbh([{"Amount3": 0}])
    kq = _kq(tao_df([]), ctx, sbh)
    assert kq["C3.2"].so_loi == 1 and kq["C3.4"].so_loi == 0


def test_lech_tong_voi_bang_ke_thi_canh_bao_khop_thi_im(ctx):
    sbh = tao_sbh([{"Amount2": 1_000_000, "Amount3": 80_000}])
    khop = tao_df([
        {"DocCode": "HD", "DebitAccount": "1311", "CreditAccount": "51111", "Amount": 1_000_000},
        {"DocCode": "HD", "DebitAccount": "1311", "CreditAccount": "33311", "Amount": 80_000},
    ])
    assert "KHÔNG khớp" not in _kq(khop, ctx, sbh)["C3.2"].ghi_chu
    lech = tao_df([
        {"DocCode": "HD", "DebitAccount": "1311", "CreditAccount": "51111", "Amount": 1_000_002},
        {"DocCode": "HD", "DebitAccount": "1311", "CreditAccount": "33311", "Amount": 80_000},
    ])
    gc = _kq(lech, ctx, sbh)["C3.2"].ghi_chu
    assert "KHÔNG khớp" in gc and "doanh thu" in gc


def test_phieu_ke_toan_131_511_khong_lam_lech_gia(ctx):
    """PK cũng ghi Nợ 131/Có 511 nhưng không lên sổ bán hàng (A01 08/2026: 540.000) —
    chỉ so cùng loại chứng từ, không thì cảnh báo "không cùng thời điểm" kêu oan."""
    sbh = tao_sbh([{"Amount2": 1_000_000, "Amount3": 80_000}])
    df = tao_df([
        {"DocCode": "HD", "DebitAccount": "1311", "CreditAccount": "51111", "Amount": 1_000_000},
        {"DocCode": "HD", "DebitAccount": "1311", "CreditAccount": "33311", "Amount": 80_000},
        {"DocCode": "PK", "DebitAccount": "1311", "CreditAccount": "51111", "Amount": 540_000},
    ])
    assert "KHÔNG khớp" not in _kq(df, ctx, sbh)["C3.2"].ghi_chu


def test_chua_nap_so_ban_hang_ma_co_ban_hang_thi_dung_ngoai(ctx):
    """Không có sổ thì không được nói "đạt": kỳ có bán hàng → thống kê + nói rõ chưa kiểm."""
    df = tao_df([{"DebitAccount": "1311", "CreditAccount": "51111"}])
    c = _kq(df, ctx)["C3.2"]
    assert c.la_thong_ke and "Chưa nạp sổ chi tiết bán hàng" in c.ghi_chu
    c34 = _kq(df, ctx)["C3.4"]
    assert not c34.la_thong_ke and c34.so_loi == 0          # kỳ không có trả lại
