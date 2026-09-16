"""Nhóm 7 — bút toán phân bổ & trích lập cuối kỳ.

Bài học C4.1 lặp lại ở đây: KHÔNG được khẳng định dựa trên sự vắng mặt của bằng
chứng. Không có số dư đầu kỳ nên "kỳ này không thấy 214/242/334" không suy ra được
DN quên khấu hao/phân bổ/lương — nên các check đó là CHECKLIST (la_thong_ke), không
kéo kết luận khóa sổ. Chỉ C7.5/C7.6 là cảnh báo thật vì bằng chứng nằm ngay trong file.
"""
from app.checks import g7_phan_bo_trich_lap as g7
from tests.conftest import tao_df


def _kq(df, ctx):
    return {r.ma: r for r in g7.kiem_tra(df, ctx)}


# ------------------------------------------------ C7.1–C7.3 checklist
def test_c71_c72_c73_la_checklist_khong_doi_ket_luan(ctx):
    df = tao_df([{"DebitAccount": "1111", "CreditAccount": "1121", "Amount": 100}])
    kq = _kq(df, ctx)
    for ma in ("C7.1", "C7.2", "C7.3"):
        assert kq[ma].la_thong_ke, ma
        assert kq[ma].so_loi == 0 and kq[ma].muc_do_thuc == "xanh", ma
        assert len(kq[ma].chi_tiet) == 1        # vẫn có dòng để kế toán đọc


def test_c71_noi_ro_co_hay_khong_thay_khau_hao(ctx):
    thieu = _kq(tao_df([{"DebitAccount": "6421", "CreditAccount": "1111"}]), ctx)["C7.1"]
    du = _kq(tao_df([{"DebitAccount": "6274", "CreditAccount": "2141"}]), ctx)["C7.1"]
    assert thieu.chi_tiet.iloc[0]["co_phat_sinh"] == False
    assert du.chi_tiet.iloc[0]["co_phat_sinh"] == True


def test_c72_phan_bo_242(ctx):
    thieu = _kq(tao_df([{"DebitAccount": "6421", "CreditAccount": "1111"}]), ctx)["C7.2"]
    du = _kq(tao_df([{"DebitAccount": "6423", "CreditAccount": "242"}]), ctx)["C7.2"]
    assert thieu.chi_tiet.iloc[0]["co_phat_sinh"] == False
    assert du.chi_tiet.iloc[0]["co_phat_sinh"] == True


def test_c73_luong_vao_chi_phi(ctx):
    du = _kq(tao_df([{"DebitAccount": "6221", "CreditAccount": "3341"}]), ctx)["C7.3"]
    du338 = _kq(tao_df([{"DebitAccount": "6271", "CreditAccount": "3383"}]), ctx)["C7.3"]
    thieu = _kq(tao_df([{"DebitAccount": "6421", "CreditAccount": "1111"}]), ctx)["C7.3"]
    assert du.chi_tiet.iloc[0]["co_phat_sinh"] == True
    assert du338.chi_tiet.iloc[0]["co_phat_sinh"] == True
    assert thieu.chi_tiet.iloc[0]["co_phat_sinh"] == False


# ------------------------------------------------ C7.4, C7.7 thống kê
def test_c74_c77_la_thong_ke_ps(ctx):
    df = tao_df([{"DebitAccount": "6421", "CreditAccount": "335", "Amount": 50},
                 {"DebitAccount": "632111", "CreditAccount": "2294", "Amount": 30}])
    kq = _kq(df, ctx)
    assert kq["C7.4"].la_thong_ke and kq["C7.4"].chi_tiet.iloc[0]["ps_co"] == 50
    assert kq["C7.7"].la_thong_ke and kq["C7.7"].chi_tiet.iloc[0]["ps_co"] == 30


# ------------------------------------------------ C7.5 tỷ giá (cảnh báo thật)
def test_c75_chi_ban_khi_ngoai_te_nam_tren_tk_tien_te(ctx):
    tren_tk_tien_te = tao_df([{"CurrencyCode": "USD", "DebitAccount": "3311",
                               "CreditAccount": "1122", "Amount": 100}])
    tren_tk_vat_tu = tao_df([{"CurrencyCode": "USD", "DebitAccount": "1521",
                              "CreditAccount": "1521", "Amount": 100}])
    da_danh_gia = tao_df([{"CurrencyCode": "USD", "DebitAccount": "3311",
                           "CreditAccount": "1122", "Amount": 100},
                          {"CurrencyCode": "VND", "DebitAccount": "413",
                           "CreditAccount": "3311", "Amount": 5}])
    chi_vnd = tao_df([{"CurrencyCode": "VND", "DebitAccount": "1111",
                       "CreditAccount": "1121", "Amount": 100}])
    assert _kq(tren_tk_tien_te, ctx)["C7.5"].so_loi == 1
    assert _kq(tren_tk_vat_tu, ctx)["C7.5"].so_loi == 0
    assert _kq(da_danh_gia, ctx)["C7.5"].so_loi == 0
    assert _kq(chi_vnd, ctx)["C7.5"].so_loi == 0


# ------------------------------------------------ C7.6 thuế TNDN (cảnh báo thật)
def test_c76_co_lai_ma_khong_co_thue_tndn(ctx):
    lai_ko_thue = tao_df([{"DebitAccount": "911", "CreditAccount": "4212", "Amount": 100}])
    co_thue = tao_df([{"DebitAccount": "911", "CreditAccount": "4212", "Amount": 100},
                      {"DebitAccount": "8211", "CreditAccount": "3334", "Amount": 20}])
    lo = tao_df([{"DebitAccount": "4212", "CreditAccount": "911", "Amount": 100}])
    assert _kq(lai_ko_thue, ctx)["C7.6"].so_loi == 1
    assert _kq(co_thue, ctx)["C7.6"].so_loi == 0
    assert _kq(lo, ctx)["C7.6"].so_loi == 0


def test_du_7_ma(ctx):
    assert [r.ma for r in g7.kiem_tra(tao_df([{}]), ctx)] == [
        "C7.1", "C7.2", "C7.3", "C7.4", "C7.5", "C7.6", "C7.7"]
