"""Nhóm 11 — Biến động kỳ (Đợt 4).

Test viết theo HẰNG SỐ của module (`g11.NGUONG_*`) chứ không chép cứng con số:
ngưỡng còn phải hiệu chỉnh trên dữ liệu thật, nhưng HÀNH VI thì không được đổi.
"""
import pandas as pd

from app.checks import g11_bien_dong as g11
from app.checks.base import BoiCanh
from tests.conftest import tao_cdps, tao_df


def _kq(cdps=None, cdps_truoc=None, df=None):
    ctx = BoiCanh(ky_thang=8, ky_nam=2026, cdps=cdps, cdps_truoc=cdps_truoc)
    return {r.ma: r for r in g11.kiem_tra(df if df is not None else tao_df([{}]), ctx)}


def test_du_3_ma_theo_thu_tu():
    assert list(_kq()) == ["C11.1", "C11.2", "C11.3", "C11.4"]


def test_chua_nap_cdps_thi_ca_nhom_dung_ngoai():
    for r in _kq().values():
        assert r.la_thong_ke is True and "Chưa nạp CĐPS" in r.ghi_chu


# ------------------------------------------------- C11.1 biến động số dư trong kỳ
def _du(account, dau, cuoi):
    """Dư net dương = dư Nợ, âm = dư Có."""
    return {"account": account,
            "du_dau_no": max(dau, 0), "du_dau_co": max(-dau, 0),
            "du_cuoi_no": max(cuoi, 0), "du_cuoi_co": max(-cuoi, 0)}


def test_c111_bat_tai_khoan_bien_dong_manh_va_lon():
    lon = g11.NGUONG_TUYET_DOI * 10
    cdps = tao_cdps([
        _du("1311", lon, lon * 5),       # tăng 400% và rất lớn -> bắt
        _du("1121", lon, int(lon * 1.05)),   # tăng 5% -> bỏ qua
    ])
    c = _kq(cdps)["C11.1"]
    assert c.la_thong_ke is True
    assert c.chi_tiet["Tài khoản"].tolist() == ["1311"]


def test_c111_bo_qua_bien_dong_ty_le_lon_nhung_so_tien_nho():
    """Tài khoản 2 nghìn thành 20 nghìn là tăng 900% nhưng không ai cần biết."""
    cdps = tao_cdps([_du("1311", 2_000, 20_000)])
    assert _kq(cdps)["C11.1"].chi_tiet.empty


def test_c111_du_dau_bang_0_thi_xet_theo_so_tuyet_doi():
    """35–51 trong 60–92 dòng lá của CĐPS thật có dư đầu = 0 — không tính được %.

    Tài khoản từ 0 lên vài tỷ chính là thứ đáng soi nhất (A01: 3331 lên 5,98 tỷ),
    bỏ qua cả nhánh này là mù đúng chỗ cần nhìn.
    """
    cdps = tao_cdps([_du("1311", 0, int(g11.NGUONG_DU_MOI * 2)),
                     _du("1121", 0, int(g11.NGUONG_DU_MOI * 0.5))])
    assert _kq(cdps)["C11.1"].chi_tiet["Tài khoản"].tolist() == ["1311"]


def test_c111_bo_qua_tk_loai_5_9():
    """TK 5–9 còn dư chỉ vì chưa kết chuyển — đó là việc của G5/C9.4, báo lại là trùng."""
    cdps = tao_cdps([_du("6421", 0, int(g11.NGUONG_DU_MOI * 5)),
                     _du("1541", 0, int(g11.NGUONG_DU_MOI * 5))])
    assert _kq(cdps)["C11.1"].chi_tiet["Tài khoản"].tolist() == ["1541"]


# ------------------------------------------------------ C11.2 biên lợi nhuận gộp
def _kd(doanh_thu, gia_von, giam_tru=0):
    return tao_cdps([
        {"account": "5111", "ps_co": doanh_thu},
        {"account": "5211", "ps_no": giam_tru},
        {"account": "6321", "ps_no": gia_von},
    ])


def test_c112_bien_binh_thuong_thi_khong_bao():
    assert _kq(_kd(10_000_000_000, 8_000_000_000))["C11.2"].so_loi == 0


def test_c112_bien_cao_bat_thuong_thi_canh_bao():
    """A02 thật: biên 71,1% trong khi 7 chi nhánh kia chỉ 0,3–20,6% — giá vốn
    thành phẩm chỉ 129 triệu đối ứng 12,7 tỷ doanh thu, tức thiếu ghi giá vốn."""
    c = _kq(_kd(17_792_259_966, 5_143_164_604))["C11.2"]
    assert c.muc_do == "vang" and c.so_loi == 1


def test_c112_chua_ket_chuyen_xong_thi_chi_thong_ke():
    """Giữa kỳ, chi nhánh chưa tính giá thành nào cũng biên cao — kết luận lúc đó
    là kết luận từ số chưa chốt, và trùng luôn với G5."""
    cdps = pd.concat([_kd(17_792_259_966, 5_143_164_604),
                      tao_cdps([_du("6421", 0, 900_000_000)])], ignore_index=True)
    c = _kq(cdps)["C11.2"]
    assert c.la_thong_ke is True and len(c.chi_tiet) == 1


def test_c112_ban_duoi_gia_von_thi_canh_bao():
    c = _kq(_kd(10_000_000_000, 12_000_000_000))["C11.2"]
    assert c.muc_do == "vang" and c.so_loi == 1
    assert "âm" in " ".join(c.chi_tiet["ly_do"]).lower()


def test_c112_co_doanh_thu_ma_khong_co_gia_von_thi_canh_bao():
    c = _kq(_kd(10_000_000_000, 0))["C11.2"]
    assert c.so_loi == 1


def test_c112_khong_co_doanh_thu_thi_khong_ket_luan():
    """Chi nhánh không bán hàng trong kỳ — không có gốc để tính biên."""
    assert _kq(_kd(0, 0))["C11.2"].so_loi == 0


def test_c112_tru_giam_tru_doanh_thu():
    """Biên tính trên doanh thu THUẦN (511 − 521), không phải doanh thu gộp."""
    c = _kq(_kd(10_000_000_000, 9_500_000_000, giam_tru=1_000_000_000))["C11.2"]
    assert c.so_loi == 1          # thuần 9 tỷ < giá vốn 9,5 tỷ -> biên âm


# --------------------------------------------------- C11.3 so với kỳ trước
def test_c113_chua_co_ky_truoc_thi_dung_ngoai():
    r = _kq(tao_cdps([_du("1311", 100, 100)]))["C11.3"]
    assert r.la_thong_ke is True and "kỳ trước" in r.ghi_chu


def test_c113_bat_phat_sinh_lech_manh_so_ky_truoc():
    truoc = tao_cdps([{"account": "6421", "ps_no": 1_000_000_000}])
    nay = tao_cdps([{"account": "6421", "ps_no": 5_000_000_000}])
    c = _kq(nay, cdps_truoc=truoc)["C11.3"]
    assert c.la_thong_ke is True
    assert c.chi_tiet["Tài khoản"].tolist() == ["642"]


def test_c113_gop_theo_cap_1_nhu_c95():
    """Cây tài khoản không theo tiền tố mã (xem C9.5) — chỉ cấp 1 là chắc chắn đúng."""
    truoc = tao_cdps([{"account": "6277", "ps_no": 1_000_000_000}])
    nay = tao_cdps([{"account": "62781", "ps_no": 1_000_000_000}])
    assert _kq(nay, cdps_truoc=truoc)["C11.3"].chi_tiet.empty


# ------------------------- C11.4 dư đầu kỳ này = dư cuối kỳ trước
def test_c114_chua_co_ky_truoc_thi_dung_ngoai():
    r = _kq(tao_cdps([_du("1311", 100, 100)]))["C11.4"]
    assert r.la_thong_ke is True and "kỳ trước" in r.ghi_chu


def test_c114_noi_khop_thi_khong_bao():
    truoc = tao_cdps([_du("1311", 0, 5_000_000_000), _du("3311", 0, -5_000_000_000)])
    nay = tao_cdps([_du("1311", 5_000_000_000, 0), _du("3311", -5_000_000_000, 0)])
    assert _kq(nay, cdps_truoc=truoc)["C11.4"].so_loi == 0


def test_c114_du_dau_khac_du_cuoi_ky_truoc_la_do():
    """Sổ kỳ trước đã bị sửa SAU khi chốt — đẳng thức kế toán, không phải nghi ngờ."""
    truoc = tao_cdps([_du("1311", 0, 5_000_000_000)])
    nay = tao_cdps([_du("1311", 4_000_000_000, 0)])
    c = _kq(nay, cdps_truoc=truoc)["C11.4"]
    assert c.muc_do == "do" and c.la_thong_ke is False and c.so_loi == 1
    assert c.chi_tiet["Tài khoản"].tolist() == ["131"]
    assert "1.000.000.000" in " ".join(c.chi_tiet["ly_do"])


def test_c114_bo_qua_chenh_lech_lam_tron():
    truoc = tao_cdps([_du("1311", 0, 5_000_000_000)])
    nay = tao_cdps([_du("1311", 5_000_000_900, 0)])       # lệch 900đ
    assert _kq(nay, cdps_truoc=truoc)["C11.4"].so_loi == 0


def test_c114_tach_tieu_khoan_giua_hai_ky_van_khop():
    """Kỳ trước để ở 6277, kỳ này tách ra 62771/62772 — cùng cấp 1 thì không phải lệch."""
    truoc = tao_cdps([_du("6277", 0, 1_000_000_000)])
    nay = tao_cdps([_du("62771", 600_000_000, 0), _du("62772", 400_000_000, 0)])
    assert _kq(nay, cdps_truoc=truoc)["C11.4"].so_loi == 0
