from app.checks import g1_chung_tu as g1
from tests.conftest import tao_df


def _kq(df, ctx):
    return {r.ma: r for r in g1.kiem_tra(df, ctx)}


def test_du_6_ma_theo_thu_tu(ctx):
    assert [r.ma for r in g1.kiem_tra(tao_df([{}]), ctx)] == ["C1.1", "C1.2", "C1.3", "C1.4", "C1.5", "C1.6"]


def test_c11_thieu_dien_giai(ctx):
    df = tao_df([{"Description": None}, {"Description": "  "}, {"Description": "ok"}])
    assert _kq(df, ctx)["C1.1"].so_loi == 2


def test_c11_item_name_duoc_tinh_la_dien_giai(ctx):
    """A3: Bravo để diễn giải ở cột tên vật tư — chỉ báo thiếu khi cả hai cột đều trống."""
    df = tao_df([
        {"Description": None, "ItemName": "Trần nhựa nano P06 - 5.0kg"},   # có tên vật tư -> bỏ qua
        {"Description": "  ", "ItemName": "  "},                            # cả hai trống -> báo
        {"Description": None, "ItemName": None},                            # cả hai trống -> báo
        {"Description": "Thuế GTGT", "ItemName": None},                     # có diễn giải -> bỏ qua
    ])
    kq = _kq(df, ctx)["C1.1"]
    assert kq.so_loi == 2
    assert kq.ghi_chu == g1.GHI_CHU_C11


def test_c12_ngay_ngoai_ky(ctx):
    df = tao_df([{"DocDate": "2026-07-31"}, {"DocDate": "2026-08-31"}, {"DocDate": "2026-09-01"}])
    kq = _kq(df, ctx)["C1.2"]
    assert kq.so_loi == 2 and kq.muc_do == "do"


def test_c13_nghi_trung(ctx):
    r = {"DocNo": "X", "DebitAccount": "6421", "CreditAccount": "1111", "Amount": 5, "Description": "a"}
    df = tao_df([r, r, {**r, "Amount": 6}])
    assert _kq(df, ctx)["C1.3"].so_loi == 2


def test_c14_no_bang_co(ctx):
    df = tao_df([{"DebitAccount": "1111", "CreditAccount": "1111"}, {}])
    assert _kq(df, ctx)["C1.4"].so_loi == 1


def test_c14_loai_tru_chung_tu_dieu_chuyen(ctx):
    """A2: điều chuyển kho/nội bộ (DC/LR/BN/BT) cùng TK hai vế là đúng nghiệp vụ."""
    rows = [{"DocCode": ma, "DebitAccount": "1561", "CreditAccount": "1561"}
            for ma in g1.DOC_DIEU_CHUYEN]
    rows.append({"DocCode": "PC", "DebitAccount": "1561", "CreditAccount": "1561"})   # còn lại -> báo
    kq = _kq(tao_df(rows), ctx)["C1.4"]
    assert kq.so_loi == 1
    assert kq.chi_tiet["ly_do"].iloc[0].endswith("(không tính chứng từ điều chuyển DC/LR/BN/BT)")
    assert "DC/LR/BN/BT" in kq.ghi_chu


def test_c14_bo_qua_khi_ca_hai_tk_deu_trong(ctx):
    """Hai vế cùng NaN không phải 'cùng một tài khoản'."""
    df = tao_df([{"DebitAccount": None, "CreditAccount": None}])
    assert _kq(df, ctx)["C1.4"].so_loi == 0


def test_c15_so_tien_khong_duong(ctx):
    df = tao_df([{"Amount": 0}, {"Amount": -1}, {"Amount": 1}])
    assert _kq(df, ctx)["C1.5"].so_loi == 2


def test_c16_thieu_so_hoac_ngay(ctx):
    df = tao_df([{"DocNo": None}, {"DocDate": None}, {}])
    assert _kq(df, ctx)["C1.6"].so_loi == 2
