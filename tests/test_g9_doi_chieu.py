"""C9.5 — đối chiếu phát sinh giữa BẢNG KÊ CHỨNG TỪ và CĐPS.

Bài học từ dữ liệu thật (file 8 chi nhánh 08/2026): so theo ĐÚNG mã tài khoản là
dương tính giả hàng loạt (50–70 TK/chi nhánh) vì hai nguồn khác độ chi tiết —
bảng kê ghi 33311/51111/13881 còn CĐPS chỉ có 3331/5111/1388.

Nặng hơn: cây tài khoản KHÔNG theo tiền tố mã. Ở A07/A08, tiểu khoản 62781 của
bảng kê nằm dưới 6277 trên CĐPS chứ không phải 6278 (62771 + 62781 = đúng số 6277).
Nên gộp theo tiền tố ở cấp sâu cũng sai. Chỉ **cấp 1 (3 chữ số)** là chắc chắn đúng.
"""
import pandas as pd

from app.checks import g9_toan_ven_cdps as g9
from app.checks.base import BoiCanh
from tests.conftest import tao_cdps, tao_df


def _c95(df, cdps):
    ctx = BoiCanh(ky_thang=8, ky_nam=2026, cdps=cdps)
    return {r.ma: r for r in g9.kiem_tra(df, ctx)}["C9.5"]


def test_chua_nap_cdps_thi_dung_ngoai():
    r = {x.ma: x for x in g9.kiem_tra(tao_df([{}]), BoiCanh(8, 2026))}["C9.5"]
    assert r.la_thong_ke is True and "Chưa nạp CĐPS" in r.ghi_chu


def test_cdps_cu_hon_bang_ke_thi_c95_chi_thong_ke():
    """Hai nguồn kết xuất lệch thời điểm thì chênh lệch KHÔNG chứng minh sổ sai.

    Đã dính thật 2026-09-21: kho có CĐPS nạp 17/09, bảng kê xuất 21/09 -> C9.5 nổ 5–26
    TK ở 7/8 chi nhánh. Kiểm chứng đó là lệch độ tươi chứ không phải sổ sai: PS 511 khớp
    TUYỆT ĐỐI 8/8 chi nhánh, chỉ 632 lệch đúng ở 3 chi nhánh vừa chạy lại giá vốn
    (A02 lệch 10,8 tỷ). Vẫn liệt kê để soi, nhưng không được kéo kết luận.
    """
    df = tao_df([{"DebitAccount": "1111", "CreditAccount": "5111", "Amount": 1_000_000}])
    cdps = tao_cdps([{"account": "1111", "ps_no": 400_000},
                     {"account": "5111", "ps_co": 400_000}])
    ctx = BoiCanh(ky_thang=8, ky_nam=2026, cdps=cdps, cdps_cu_hon=True)
    r = {x.ma: x for x in g9.kiem_tra(df, ctx)}["C9.5"]
    assert len(r.chi_tiet) > 0, "vẫn phải liệt kê để soi"
    assert r.la_thong_ke is True and r.so_loi == 0
    assert "cũ hơn" in r.ghi_chu.lower()


def test_khop_hoan_toan_thi_khong_bao():
    df = tao_df([{"DebitAccount": "1111", "CreditAccount": "5111", "Amount": 1_000_000}])
    cdps = tao_cdps([{"account": "1111", "ps_no": 1_000_000},
                     {"account": "5111", "ps_co": 1_000_000}])
    assert _c95(df, cdps).so_loi == 0


def test_hai_nguon_khac_do_chi_tiet_van_khop():
    """Bảng kê ghi 33311/51111, CĐPS chỉ có 3331/5111 — gộp cấp 1 là khớp."""
    df = tao_df([{"DebitAccount": "1311", "CreditAccount": "51111", "Amount": 1_000_000},
                 {"DebitAccount": "1311", "CreditAccount": "33311", "Amount": 100_000}])
    cdps = tao_cdps([{"account": "1311", "ps_no": 1_100_000},
                     {"account": "5111", "ps_co": 1_000_000},
                     {"account": "3331", "ps_co": 100_000}])
    assert _c95(df, cdps).so_loi == 0


def test_cay_tai_khoan_khong_theo_tien_to_van_khop():
    """A07/A08 thật: 62781 của bảng kê nằm dưới 6277 trên CĐPS, không phải 6278."""
    df = tao_df([{"DebitAccount": "62771", "CreditAccount": "1111", "Amount": 92_701_405},
                 {"DebitAccount": "62781", "CreditAccount": "1111", "Amount": 65_764_694}])
    cdps = tao_cdps([{"account": "6277", "ps_no": 158_466_099},
                     {"account": "1111", "ps_co": 158_466_099}])
    assert _c95(df, cdps).so_loi == 0


def test_bang_ke_thieu_but_toan_thi_do():
    """A04 thật: CĐPS có Nợ 1368 / Có 3368 480.618.249 mà bảng kê không có."""
    df = tao_df([{"DebitAccount": "1111", "CreditAccount": "5111", "Amount": 1_000_000}])
    cdps = tao_cdps([{"account": "1111", "ps_no": 1_000_000},
                     {"account": "5111", "ps_co": 1_000_000},
                     {"account": "1368", "ps_no": 480_618_249},
                     {"account": "3368", "ps_co": 480_618_249}])
    r = _c95(df, cdps)
    assert r.muc_do == "do" and r.so_loi == 2
    assert sorted(r.chi_tiet["Tài khoản"].tolist()) == ["136", "336"]
    assert "480.618.249" in " ".join(r.chi_tiet["ly_do"])


def test_bo_qua_chenh_lech_lam_tron():
    """A05 thật: lệch lớn nhất 980đ do đơn giá bình quân — không phải sai sổ."""
    df = tao_df([{"DebitAccount": "1551", "CreditAccount": "1111", "Amount": 9_036_944_030}])
    cdps = tao_cdps([{"account": "1551", "ps_no": 9_036_943_050},   # lệch 980đ
                     {"account": "1111", "ps_co": 9_036_944_030}])
    assert _c95(df, cdps).so_loi == 0


def test_tk_chi_co_o_mot_ben_van_bi_bat():
    df = tao_df([{"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 5_000_000}])
    cdps = tao_cdps([{"account": "1111", "ps_co": 5_000_000}])
    r = _c95(df, cdps)
    assert r.chi_tiet["Tài khoản"].tolist() == ["642"]
