"""C2.5 — bán TSCĐ chuyển giao sang khay C: thu 711 phải bằng giá trị còn lại (Nợ 811/Có 21x)."""
from app.checks import g2_dinh_khoan as g2
from tests.conftest import tao_df

KHACH = "Công ty X thành phố Hồ Chí Minh"      # tên giả, chỉ cần chứa chuỗi nhận diện
CHUYEN = "Chuyển bán HCM - Khay C (TS01): Máy cán"


def _thu(so, **kw):
    return {"DocCode": "DV", "DebitAccount": "1311", "CreditAccount": "7111", "Amount": so,
            "CustomerName": KHACH, **kw}


def _gtcl(so, mo_ta=CHUYEN, **kw):
    return {"DocCode": "TD", "DebitAccount": "8111", "CreditAccount": "2112", "Amount": so,
            "Description": mo_ta, **kw}


def _c25(rows):
    return next(r for r in g2.kiem_tra(tao_df(rows), None) if r.ma == "C2.5")


def test_khop_dung_thi_dat():
    r = _c25([_thu(1_000_000), _gtcl(1_000_000)])
    assert not r.la_thong_ke and r.so_loi == 0 and r.muc_do_thuc == "xanh"
    assert "chênh 0" in r.ghi_chu


def test_lech_lam_tron_trong_nguong_1000d_moi_tai_san():
    r = _c25([_thu(2_001_500), _gtcl(1_000_000), _gtcl(1_000_000)])     # 2 TS -> ngưỡng 2.000đ
    assert r.so_loi == 0
    assert _c25([_thu(1_002_000), _gtcl(1_000_000)]).muc_do_thuc == "do"   # 1 TS, lệch 2.000đ


def test_chenh_la_do_va_co_bang_chung_minh():
    r = _c25([_thu(1_200_000), _gtcl(1_000_000)])
    assert r.muc_do_thuc == "do" and r.so_loi == 2
    assert "chênh 200.000" in r.ghi_chu
    assert set(r.chi_tiet["loai_but_toan"]) == {"Thu 711 (Nợ 131/Có 711)", "GTCL TSCĐ (Nợ 811/Có 21x)"}


def test_khong_co_chuyen_giao_thi_dung_ngoai():
    r = _c25([{}])
    assert r.la_thong_ke and "không xét" in r.ghi_chu


def test_chi_nhanh_cua_phap_nhan_nhan_no_334_khong_xet():
    """Tên khách khớp cả chi nhánh của pháp nhân nhận: phạt trừ lương Nợ 334/Có 711 không
    phải bán TSCĐ — từng sinh ĐỎ giả ở 6 khay (red-team 17/11)."""
    r = _c25([{"DebitAccount": "3341", "CreditAccount": "71188", "Amount": 650_000, "CustomerName": KHACH}])
    assert r.la_thong_ke


def test_gtcl_noi_bo_va_tat_toan_khong_vao_chenh():
    r = _c25([_thu(1_000_000), _gtcl(1_000_000),
              _gtcl(500_000, "Chuyển bán HCM - Bán Hà Nội (TS02)"),       # nội bộ: từ khóa
              _gtcl(300_000, "Chuyển bán An Giang (TS03)"),                # nội bộ: từ khóa
              _gtcl(200_000, "Thanh lý máy cũ"),                           # không có HCM
              {"DebitAccount": "8111", "CreditAccount": "627", "Amount": 90_000}])
    assert r.so_loi == 0
    assert "GTCL chuyển nội bộ 1.000.000" in r.ghi_chu and "tất toán" in r.ghi_chu


def test_dong_doi_ung_911_bi_bo():
    r = _c25([_thu(1_000_000), _gtcl(1_000_000),
              {"DebitAccount": "7111", "CreditAccount": "911", "Amount": 1_000_000}])
    assert r.so_loi == 0


def test_khach_ngoai_khong_xet():
    r = _c25([_thu(5_000_000, CustomerName="Khách lẻ Hà Nội"), _gtcl(1_000_000)])
    assert r.muc_do_thuc == "do" and "Thu 711 0 −" in r.ghi_chu


def test_but_toan_dao_lam_tat_canh_bao():
    r = _c25([_thu(1_200_000), _gtcl(1_000_000),
              {"DebitAccount": "7111", "CreditAccount": "1311", "Amount": 200_000, "CustomerName": KHACH}])
    assert r.so_loi == 0


def test_no_133_co_711_duoc_danh_dau():
    r = _c25([_thu(1_000_000), _gtcl(900_000),
              {"DebitAccount": "1331", "CreditAccount": "7111", "Amount": 50_000, "CustomerName": KHACH}])
    assert "Nợ 133/Có 711" in r.ghi_chu
    assert "⚠ Nợ 133/Có 711 — bất thường" in set(r.chi_tiet["loai_but_toan"])


def test_tu_khoa_tim_nguyen_van_khong_regex():
    r = _c25([_thu(1_000_000), _gtcl(1_000_000, "Chuyển bán (TP.HCM) (TS9)")])
    assert r.so_loi == 0


def test_frame_rong_va_ten_khach_rong():
    r = _c25([{"CustomerName": None, "Description": None}])
    assert r.la_thong_ke
