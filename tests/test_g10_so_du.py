"""Nhóm 10 — Tính chất số dư trên CĐPS (quỹ/kho âm, dư ngược chiều, treo chờ xử lý)."""
from app.checks import g10_so_du as g10
from app.checks.base import BoiCanh
from tests.conftest import tao_cdps, tao_df


def _kq(cdps):
    ctx = BoiCanh(ky_thang=8, ky_nam=2026, cdps=cdps)
    return {r.ma: r for r in g10.kiem_tra(tao_df([{}]), ctx)}


def test_du_8_ma_theo_thu_tu():
    ma = [r.ma for r in g10.kiem_tra(tao_df([{}]), BoiCanh(8, 2026))]
    assert ma == ["C10.1", "C10.2", "C10.3", "C10.4", "C10.5", "C10.6", "C10.7", "C10.8"]


def test_chua_nap_cdps_thi_dung_ngoai():
    for r in g10.kiem_tra(tao_df([{}]), BoiCanh(8, 2026)):
        assert r.la_thong_ke is True and "Chưa nạp CĐPS" in r.ghi_chu


# ------------------------------------------------ C10.1 quỹ/ngân hàng âm
def test_c101_tien_du_co_la_do():
    cdps = tao_cdps([{"account": "1111", "du_cuoi_co": 500}, {"account": "1121", "du_cuoi_no": 900}])
    c = _kq(cdps)["C10.1"]
    assert c.muc_do == "do" and c.so_loi == 1
    assert c.chi_tiet["Tài khoản"].tolist() == ["1111"]


# ------------------------------------------------ C10.2 âm kho
def test_c102_kho_du_co_la_do():
    cdps = tao_cdps([{"account": "1521", "du_cuoi_co": 300}, {"account": "1551", "du_cuoi_no": 100}])
    assert _kq(cdps)["C10.2"].so_loi == 1


# ------------------------------------------------ C10.3 TSCĐ / hao mòn ngược chiều
def test_c103_214_du_no_va_211_du_co():
    cdps = tao_cdps([
        {"account": "2141", "du_cuoi_no": 100},    # hao mòn dư Nợ -> sai
        {"account": "2111", "du_cuoi_co": 200},    # nguyên giá dư Có -> sai
        {"account": "2112", "du_cuoi_no": 900},    # bình thường
    ])
    assert _kq(cdps)["C10.3"].so_loi == 2


# ------------------------------------------------ C10.4 dư ngược chiều (ngoài lưỡng tính)
def test_c104_bat_du_nguoc_chieu_ngoai_luong_tinh():
    cdps = tao_cdps([
        {"account": "1288", "du_cuoi_co": 50},     # loại 1 dư Có, không lưỡng tính -> bắt
        {"account": "1311", "du_cuoi_co": 70},     # 131 lưỡng tính -> bỏ qua (C10.5 lo)
        {"account": "4111", "du_cuoi_no": 80},     # loại 4 dư Nợ, không lưỡng tính -> bắt
        {"account": "4212", "du_cuoi_no": 90},     # 421 lưỡng tính -> bỏ qua
    ])
    c = _kq(cdps)["C10.4"]
    assert c.muc_do == "vang"
    assert sorted(c.chi_tiet["Tài khoản"].tolist()) == ["1288", "4111"]


def test_c104_khong_bat_tk_dieu_chinh_giam_du_co():
    """229 (dự phòng) như 214 (hao mòn): TK loại 2 điều chỉnh giảm tài sản, dư Có là
    ĐÚNG bản chất. Bắt là dương tính giả — đã thấy ở A03/A04 với 2293."""
    cdps = tao_cdps([{"account": "2293", "du_cuoi_co": 517_071_287}])
    assert _kq(cdps)["C10.4"].so_loi == 0


def test_c104_khong_bat_lai_tk_da_co_check_rieng():
    """1111/1521/2141 đã có C10.1–C10.3 -> C10.4 không báo trùng."""
    cdps = tao_cdps([{"account": "1111", "du_cuoi_co": 5}, {"account": "1521", "du_cuoi_co": 5},
                     {"account": "2141", "du_cuoi_no": 5}])
    assert _kq(cdps)["C10.4"].so_loi == 0


# ------------------------------------------------ C10.5 ứng trước 131/331
def test_c105_131_du_co_va_331_du_no():
    cdps = tao_cdps([
        {"account": "1311", "du_cuoi_co": 100},    # khách ứng trước
        {"account": "3311", "du_cuoi_no": 200},    # trả trước người bán
        {"account": "1312", "du_cuoi_no": 300},    # bình thường
    ])
    c = _kq(cdps)["C10.5"]
    assert c.muc_do == "vang" and c.so_loi == 2


# ------------------------------------------------ C10.6 / C10.8 treo chờ xử lý
# Tách theo sức mạnh bằng chứng: khoản MỚI phát sinh trong kỳ là việc của kỳ đang khóa
# (VÀNG); khoản TỒN từ kỳ trước là tồn đọng đã biết, TT200 đòi xử lý trước BCTC năm chứ
# không phải trước mỗi lần khóa sổ tháng -> chỉ thống kê. Đo trên CĐPS thật 08/2026:
# cả 8 chi nhánh đều chỉ có khoản tồn cũ (0 khoản mới), kể cả 5 chi nhánh kế toán tổng
# hợp đã xác nhận OK -> để VÀNG là kéo cả 8 xuống "cần rà soát" một cách vô lý.
def test_c106_chi_bat_khoan_moi_phat_sinh_trong_ky():
    cdps = tao_cdps([
        {"account": "1381", "du_dau_no": 0, "du_cuoi_no": 10},     # mới -> C10.6
        {"account": "3381", "du_dau_co": 500, "du_cuoi_co": 480},  # tồn cũ -> C10.8
        {"account": "1388", "du_cuoi_no": 30},                     # không phải chờ xử lý
    ])
    c = _kq(cdps)["C10.6"]
    assert c.muc_do == "vang" and c.la_thong_ke is False
    assert c.chi_tiet["Tài khoản"].tolist() == ["1381"]


def test_c108_khoan_ton_cu_chi_thong_ke_khong_keo_ket_luan():
    cdps = tao_cdps([
        {"account": "3381", "du_dau_co": 500, "du_cuoi_co": 480},
        {"account": "1381", "du_dau_no": 0, "du_cuoi_no": 10},
    ])
    c = _kq(cdps)["C10.8"]
    assert c.la_thong_ke is True and c.so_loi == 0
    assert c.chi_tiet["Tài khoản"].tolist() == ["3381"]


def test_c106_khoan_ton_cu_da_tat_toan_thi_khong_bat_o_dau_ca():
    """Dư đầu có, dư cuối về 0 = đã xử lý xong trong kỳ -> sạch cả hai check."""
    cdps = tao_cdps([{"account": "3381", "du_dau_co": 500, "du_cuoi_co": 0}])
    k = _kq(cdps)
    assert k["C10.6"].so_loi == 0 and len(k["C10.8"].chi_tiet) == 0


# ------------------------------------------------ C10.7 phải thu/trả khác lớn
def test_c107_la_thong_ke_khong_keo_ket_luan():
    cdps = tao_cdps([{"account": "1111", "du_cuoi_no": 100}, {"account": "3388", "du_cuoi_co": 90}])
    c = _kq(cdps)["C10.7"]
    assert c.la_thong_ke is True and c.so_loi == 0
