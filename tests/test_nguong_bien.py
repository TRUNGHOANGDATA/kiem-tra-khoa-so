"""D4 — cặp biên cho các phép so sánh: đổi ">" thành ">=" phải làm suite đỏ.

Mỗi test khẳng định tại ĐÚNG giá trị ngưỡng (không bị bắt) và ngay sát trên
ngưỡng (bị bắt), nên cả hai chiều lệch của toán tử đều lộ ra.
"""
from app.checks import g2_dinh_khoan as g2, g4_kho_gia_von as g4, g6_tong_quan as g6
from tests.conftest import tao_df


def _kq(mod, df, ctx):
    return {r.ma: r for r in mod.kiem_tra(df, ctx)}


def test_c42_dung_tai_nguong_lam_tron_khong_bi_bat(ctx):
    """Ngưỡng = |Amount| × 0,1% + 1đ. Amount 1.000 -> ngưỡng đúng 2đ."""
    tai_nguong = tao_df([{"CreditAccount": "1551", "Quantity9": 1, "UnitCost": 998, "Amount": 1000}])
    tren_nguong = tao_df([{"CreditAccount": "1551", "Quantity9": 1, "UnitCost": 997, "Amount": 1000}])
    assert len(_kq(g4, tai_nguong, ctx)["C4.2"].chi_tiet) == 0   # lệch đúng 2 = ngưỡng -> bỏ qua
    assert len(_kq(g4, tren_nguong, ctx)["C4.2"].chi_tiet) == 1  # lệch 3 > ngưỡng -> liệt kê


def test_c42_nguong_ty_le_theo_so_tien_lon(ctx):
    """Phần 0,1% phải thực sự có tác dụng: Amount 1.000.000 -> ngưỡng 1.001đ."""
    tai_nguong = tao_df([{"CreditAccount": "1551", "Quantity9": 1, "UnitCost": 998_999,
                          "Amount": 1_000_000}])
    tren_nguong = tao_df([{"CreditAccount": "1551", "Quantity9": 1, "UnitCost": 998_998,
                           "Amount": 1_000_000}])
    assert len(_kq(g4, tai_nguong, ctx)["C4.2"].chi_tiet) == 0   # lệch đúng 1.001
    assert len(_kq(g4, tren_nguong, ctx)["C4.2"].chi_tiet) == 1  # lệch 1.002


def _biet_so_c24(tinh: float, am: bool = False) -> float:
    """Lệch LỚN NHẤT vẫn được coi là làm tròn, giải từ chính bất đẳng thức của C2.4.

    Điều kiện bắt: |Amount − tính| > |Amount|·r + c, mà Amount = tính ± d nên ngưỡng
    phụ thuộc vào chính d — phải giải xuôi thay vì cộng thẳng hằng số.
        d > (tính·r + c) / (1 ∓ r)
    """
    r, c = g2.TY_LE_LECH_TY_GIA, g2.NGUONG_LECH_TY_GIA
    return (tinh * r + c) / (1 + r if am else 1 - r)


def test_c24_dung_tai_nguong_lech_ty_gia_khong_bi_bat(ctx):
    """Ngưỡng theo TỶ LỆ: lệch đúng ngưỡng là làm tròn, hơn một đồng là sai quy đổi."""
    chung = {"CurrencyCode": "USD", "OriginalAmount": 100.0, "ExchangeRate": 26_000.0}
    d = _biet_so_c24(2_600_000)
    # Kẹp hai bên thay vì đặt ĐÚNG điểm biên: ngưỡng là số lẻ (2.603,6đ) nên so sánh
    # dấu phẩy động ngay tại biên phụ thuộc bit cuối, không phải thứ đáng khóa vào test.
    tai_nguong = tao_df([{**chung, "Amount": 2_600_000 + d - 1}])
    tren_nguong = tao_df([{**chung, "Amount": 2_600_000 + d + 1}])
    assert _kq(g2, tai_nguong, ctx)["C2.4"].so_loi == 0
    assert _kq(g2, tren_nguong, ctx)["C2.4"].so_loi == 1


def test_c24_lech_am_dung_tai_nguong(ctx):
    """Ngưỡng áp cho trị tuyệt đối — chiều âm phải đối xứng."""
    chung = {"CurrencyCode": "USD", "OriginalAmount": 100.0, "ExchangeRate": 26_000.0}
    d = _biet_so_c24(2_600_000, am=True)
    tai_nguong = tao_df([{**chung, "Amount": 2_600_000 - d + 1}])
    tren_nguong = tao_df([{**chung, "Amount": 2_600_000 - d - 1}])
    assert _kq(g2, tai_nguong, ctx)["C2.4"].so_loi == 0
    assert _kq(g2, tren_nguong, ctx)["C2.4"].so_loi == 1


def test_c65_so_dong_dung_bang_m_cong_2s_khong_bi_danh_dau(ctx):
    """Mọi ngày bằng nhau -> s = 0, số dòng mỗi ngày ĐÚNG BẰNG m + 2s.

    Với ">" không ngày nào bất thường; đổi thành ">=" thì mọi ngày đều bất thường.
    """
    rows = [{"DocDate": "2026-08-10"}] * 3 + [{"DocDate": "2026-08-11"}] * 3
    bang = _kq(g6, tao_df(rows), ctx)["C6.5"].chi_tiet
    assert len(bang) == 2 and bang["so_dong"].tolist() == [3, 3]
    assert bang["bat_thuong"].tolist() == [False, False]


def test_c65_ngay_vuot_hon_m_cong_2s_bi_danh_dau(ctx):
    """Chiều còn lại: có ngày thực sự vượt m + 2s thì phải được đánh dấu."""
    rows = [{"DocDate": f"2026-08-{d:02d}"} for d in range(1, 10)] + [{"DocDate": "2026-08-20"}] * 10
    bang = _kq(g6, tao_df(rows), ctx)["C6.5"].chi_tiet
    assert bang["bat_thuong"].sum() == 1
    assert bang.loc[bang["bat_thuong"], "so_dong"].iloc[0] == 10


def test_c65_mot_ngay_duy_nhat_khong_danh_dau(ctx):
    """len(theo_ngay) == 1: std không xác định -> không được kết luận bất thường."""
    bang = _kq(g6, tao_df([{"DocDate": "2026-08-10"}] * 5), ctx)["C6.5"].chi_tiet
    assert len(bang) == 1 and bang["bat_thuong"].tolist() == [False]


def test_nguong_con_lai_ap_dung_dung_tai_bien(ctx):
    """C4.4: còn đúng NGUONG_CON_LAI thì thôi, hơn một chút là báo."""
    from app.checks.base import NGUONG_CON_LAI
    tai_nguong = tao_df([{"DebitAccount": "6211", "CreditAccount": "1521", "Amount": 100.0},
                         {"DebitAccount": "154", "CreditAccount": "6211", "Amount": 100.0 - NGUONG_CON_LAI}])
    tren_nguong = tao_df([{"DebitAccount": "6211", "CreditAccount": "1521", "Amount": 100.0},
                          {"DebitAccount": "154", "CreditAccount": "6211", "Amount": 100.0 - NGUONG_CON_LAI - 0.1}])
    assert _kq(g4, tai_nguong, ctx)["C4.4"].so_loi == 0
    assert _kq(g4, tren_nguong, ctx)["C4.4"].so_loi == 1
