"""C2.6 — hàng hóa chuyển giao sang khay C: doanh thu (Có 511/521) phải bằng giá vốn (Nợ 632)."""
from app.checks import g2_dinh_khoan as g2
from tests.conftest import tao_df

KHACH = "Công ty X thành phố Hồ Chí Minh"
TSCD = {"DocCode": "TD", "DebitAccount": "8111", "CreditAccount": "2112", "Amount": 1.0,
        "Description": "Chuyển bán HCM - Khay C (TS01)", "Id": 900}


def _dt(so, id_=1, **kw):
    return {"DocCode": "HD", "DebitAccount": "1311", "CreditAccount": "51111", "Amount": so,
            "CustomerName": KHACH, "Id": id_, **kw}


def _gv(so, id_=1, **kw):
    return {"DocCode": "HD", "DebitAccount": "6321", "CreditAccount": "1561", "Amount": so,
            "Id": id_, **kw}


def _c26(rows):
    df = tao_df(rows).assign(Id=[r.get("Id") for r in rows])
    return next(r for r in g2.kiem_tra(df, None) if r.ma == "C2.6")


def test_khop_thi_dat():
    r = _c26([TSCD, _dt(1_000_000), _gv(1_000_000)])
    assert not r.la_thong_ke and r.muc_do_thuc == "xanh" and "chênh 0" in r.ghi_chu


def test_lech_mot_dong_cung_la_vang():
    r = _c26([TSCD, _dt(1_000_001), _gv(1_000_000)])
    assert r.muc_do_thuc == "vang" and r.so_loi == 1
    assert r.chi_tiet.loc[0, "chenh"] == 1


def test_khong_chuyen_giao_tscd_thi_dung_ngoai():
    """Bán hàng thường có lãi cho chi nhánh pháp nhân nhận (khay không chuyển giao) — không xét."""
    r = _c26([_dt(1_200_000), _gv(1_000_000)])
    assert r.la_thong_ke and "không xét" in r.ghi_chu


def test_gia_von_khong_so_chung_tu_tu_mang_ten_khach_duoc_tinh():
    """Hình dạng thật A07: giá vốn ở chứng từ KHÔNG SỐ, Id riêng, mỗi dòng mang tên khách nhận."""
    r = _c26([TSCD, _dt(1_000_000, id_=7, DocNo="PK1"), _gv(1_000_000, id_=8, DocNo=None, CustomerName=KHACH)])
    assert r.so_loi == 0


def test_khong_cot_id_gia_von_khong_so_mang_ten_khach_van_tinh():
    rows = [TSCD, _dt(1_000_000, DocNo="PK1"), _gv(1_000_000, DocNo=None, CustomerName=KHACH)]
    r = next(x for x in g2.kiem_tra(tao_df(rows), None) if x.ma == "C2.6")
    assert r.so_loi == 0


def test_doanh_thu_dich_vu_5113_khong_vao_chenh():
    r = _c26([TSCD, _dt(1_000_000), _gv(1_000_000), _dt(64_000_000, id_=3, CreditAccount="51131")])
    assert r.so_loi == 0 and "(5113/5118) 64.000.000" in r.ghi_chu


def test_dieu_chinh_so_am_tinh_rong_ca_hai_chieu():
    """Nợ 131/Có 511 âm (giảm) và Nợ 511/Có 131 âm (tăng) đều phải về cùng một phía."""
    r = _c26([TSCD, _dt(1_300_000), _gv(1_000_000), _dt(-300_000)])
    assert r.so_loi == 0
    r = _c26([TSCD, _dt(700_000), _gv(1_000_000),
              {"DebitAccount": "51111", "CreditAccount": "1311", "Amount": -300_000, "CustomerName": KHACH, "Id": 1}])
    assert r.so_loi == 0


def test_ket_chuyen_511_521_khong_tinh():
    r = _c26([TSCD, _dt(1_000_000), _gv(1_000_000),
              {"DebitAccount": "51111", "CreditAccount": "52111", "Amount": 30_000, "CustomerName": KHACH, "Id": 1}])
    assert r.so_loi == 0


def test_no_133_co_511_duoc_danh_dau():
    r = _c26([TSCD, _dt(1_000_000), _gv(1_000_000),
              {"DebitAccount": "1331", "CreditAccount": "51132", "Amount": 9_000, "CustomerName": KHACH, "Id": 1}])
    assert "Nợ 133/Có 511" in r.ghi_chu


def test_dt_va_gv_hai_chung_tu_khac_nhau_bu_tru_theo_tong_khay():
    """A07: doanh thu ở một phiếu, giá vốn ở chứng từ khác mà cũng có khách pháp nhân nhận."""
    r = _c26([TSCD, _dt(1_000_000, id_=1), _gv(1_000_000, id_=2, CustomerName=KHACH)])
    assert r.so_loi == 0 and "chênh 0" in r.ghi_chu


def test_tra_lai_521_tru_vao_doanh_thu_va_911_bi_bo():
    r = _c26([TSCD, _dt(1_050_000), _gv(1_000_000),
              {"DebitAccount": "52131", "CreditAccount": "1311", "Amount": 50_000, "CustomerName": KHACH, "Id": 1},
              {"DebitAccount": "51111", "CreditAccount": "911", "Amount": 1_000_000, "Id": 1}])
    assert r.so_loi == 0


def test_khong_cot_id_lui_ve_so_chung_tu():
    rows = [TSCD, _dt(1_000_000, DocNo="HD1"), _gv(900_000, DocNo="HD1")]
    df = tao_df(rows)                                   # không gắn cột Id
    r = next(x for x in g2.kiem_tra(df, None) if x.ma == "C2.6")
    assert r.muc_do_thuc == "vang" and "chênh 100.000" in r.ghi_chu
