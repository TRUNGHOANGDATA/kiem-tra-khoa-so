from app.checks import g6_tong_quan as g6
from tests.conftest import tao_df


def test_tat_ca_la_thong_ke(ctx):
    kq = g6.kiem_tra(tao_df([{}]), ctx)
    assert [r.ma for r in kq] == ["C6.1", "C6.2", "C6.3", "C6.4", "C6.5", "C6.7", "C6.8"]
    assert all(r.la_thong_ke and r.so_loi == 0 for r in kq)


def test_c61_top_theo_amount_giam_dan(ctx):
    df = tao_df([{"Amount": 1}, {"Amount": 9}, {"Amount": 5}])
    top = {r.ma: r for r in g6.kiem_tra(df, ctx)}["C6.1"].chi_tiet
    assert top["Amount"].tolist() == [9, 5, 1] and "CreatedByName" in top.columns


def test_c63_c64_gom_nhom(ctx):
    df = tao_df([{"DocCode": "BT", "CreatedByName": "A", "Amount": 1},
                 {"DocCode": "BT", "CreatedByName": "B", "Amount": 2},
                 {"DocCode": "PN", "CreatedByName": "A", "Amount": 3}])
    kq = {r.ma: r for r in g6.kiem_tra(df, ctx)}
    assert kq["C6.3"].chi_tiet.set_index("DocCode").loc["BT", "so_dong"] == 2
    assert kq["C6.4"].chi_tiet.set_index("CreatedByName").loc["A", "tong"] == 4


def test_c65_danh_dau_ngay_don_but_toan(ctx):
    rows = [{"DocDate": f"2026-08-{d:02d}"} for d in range(1, 11)] + [{"DocDate": "2026-08-31"}] * 30
    kq = {r.ma: r for r in g6.kiem_tra(tao_df(rows), ctx)}["C6.5"].chi_tiet
    assert kq["bat_thuong"].sum() == 1
