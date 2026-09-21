from app.checks import g2_dinh_khoan as g2
from app.checks.base import BoiCanh
from tests.conftest import tao_df


def _kq(df, ctx):
    return {r.ma: r for r in g2.kiem_tra(df, ctx)}


def test_du_4_ma(ctx):
    assert [r.ma for r in g2.kiem_tra(tao_df([{}]), ctx)] == ["C2.1", "C2.2", "C2.3", "C2.4"]


def test_c21_thieu_doi_tuong_cong_no(ctx):
    df = tao_df([
        {"DebitAccount": "1311", "CustomerCode": None},
        {"CreditAccount": "3311", "CustomerCode": "NCC"},
        {"DebitAccount": "6421", "CustomerCode": None},
    ])
    assert _kq(df, ctx)["C2.1"].so_loi == 1


def test_c22_tk_sai_dinh_dang(ctx):
    df = tao_df([{"DebitAccount": "11"}, {"CreditAccount": "ABC"}, {}])
    assert _kq(df, ctx)["C2.2"].so_loi == 2


def test_c23_cung_nhom_nhung_khac_tai_khoan_la_binh_thuong(ctx):
    """Chuyển giữa hai quỹ / hai ngân hàng KHÁC nhau là nghiệp vụ ngân quỹ thường ngày.
    Chỉ tiền chuyển vào CHÍNH tài khoản đó mới là bút toán không làm tiền dịch chuyển."""
    df = tao_df([{"DebitAccount": "1111", "CreditAccount": "1112"},   # hai quỹ khác nhau
                 {"DebitAccount": "1121", "CreditAccount": "1122"},   # hai TK NH khác nhau
                 {"DebitAccount": "1121", "CreditAccount": "1111"},   # NH -> quỹ
                 {"DebitAccount": "1111", "CreditAccount": "1111"}])  # tự chuyển -> BẮT
    c = _kq(df, ctx)["C2.3"]
    assert c.so_loi == 1
    assert c.chi_tiet.iloc[0]["DebitAccount"] == "1111"


def test_c24_lech_quy_doi_ngoai_te(ctx):
    """Ngưỡng theo tỷ lệ: 0,5% là lệch thật, 0,019% là làm tròn quy đổi."""
    df = tao_df([
        {"CurrencyCode": "USD", "OriginalAmount": 100, "ExchangeRate": 26000, "Amount": 2_600_000},
        {"CurrencyCode": "USD", "OriginalAmount": 100, "ExchangeRate": 26000, "Amount": 2_613_000},
        {"CurrencyCode": "USD", "OriginalAmount": 100, "ExchangeRate": 26000, "Amount": 2_600_500},
        {"CurrencyCode": "VND", "OriginalAmount": 0, "ExchangeRate": 1, "Amount": 5},
    ])
    c = _kq(df, ctx)["C2.4"]
    assert c.so_loi == 1 and c.chi_tiet.iloc[0]["Amount"] == 2_613_000


# ---------------------------------------------- C2.3 chỉ bắt tự-chuyển THẬT
def test_c23_bo_qua_chuyen_tien_giua_hai_tai_khoan_ngan_hang():
    """Nợ 1121 / Có 1121 nhưng KHÁC tài khoản ngân hàng = chuyển tiền giữa hai ngân
    hàng của chính công ty — nghiệp vụ ngân quỹ bình thường, không phải bút toán trung
    gian đáng ngờ. Cùng khuôn mẫu đã sửa cho C1.4: khác biệt nằm ở cột chiều, không ở
    số hiệu TK. Đo trên sổ 08/2026: A01 có 27 dòng thì 27/27 khác tài khoản ngân hàng
    (BIDV -> ACB...), không dòng nào tự chuyển vào chính mình.
    """
    df = tao_df([
        {"DocNo": "BN1", "DebitAccount": "1121", "CreditAccount": "1121",
         "BankAccId": 130, "CrspBankAccId": 12, "Amount": 2_000_000_000},
        {"DocNo": "TU1", "DebitAccount": "1121", "CreditAccount": "1121",
         "BankAccId": 12, "CrspBankAccId": 12, "Amount": 5_000_000},
    ])
    c = _kq(df, BoiCanh(8, 2026))["C2.3"]
    assert c.so_loi == 1 and c.chi_tiet.iloc[0]["DocNo"] == "TU1"


def test_c23_thieu_thong_tin_ngan_hang_thi_van_bat_khi_trung_tk():
    """Tiền mặt không có tài khoản ngân hàng: cùng TK hai vế vẫn là tự chuyển."""
    df = tao_df([
        {"DocNo": "PC1", "DebitAccount": "1114", "CreditAccount": "1111", "Amount": 550_000_000},
        {"DocNo": "PC2", "DebitAccount": "1111", "CreditAccount": "1111", "Amount": 1_000},
    ])
    c = _kq(df, BoiCanh(8, 2026))["C2.3"]
    assert c.so_loi == 1 and c.chi_tiet.iloc[0]["DocNo"] == "PC2"


# ---------------------------------------------- C2.4 ngưỡng phải theo tỷ lệ
def test_c24_bo_qua_sai_so_lam_tron_quy_doi():
    """818đ trên bút toán 2,26 tỷ là làm tròn quy đổi USD, không phải lệch tỷ giá.

    Ngưỡng 1đ tuyệt đối bắt cả 7 dòng nhập khẩu của A01 với TỔNG lệch 1.276đ.
    """
    df = tao_df([
        {"DocNo": "NK1", "CurrencyCode": "USD", "OriginalAmount": 86011.46,
         "ExchangeRate": 26289.39, "Amount": 2_261_189_634},          # lệch 818đ -> làm tròn
        {"DocNo": "NK2", "CurrencyCode": "USD", "OriginalAmount": 1000,
         "ExchangeRate": 26000, "Amount": 27_000_000},                # lệch 1tr -> thật
    ])
    c = _kq(df, BoiCanh(8, 2026))["C2.4"]
    assert c.so_loi == 1 and c.chi_tiet.iloc[0]["DocNo"] == "NK2"
