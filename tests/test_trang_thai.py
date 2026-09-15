from app import checks, trang_thai as tt
from tests.conftest import tao_df


def _suy(df, ctx):
    kq = {r.ma: r for r in checks.chay_tat_ca(df, ctx)}
    return {b.buoc: b for b in tt.suy_trang_thai(df, kq)}, tt.suy_trang_thai(df, kq)


def test_du_11_buoc_dung_thu_tu(ctx):
    _, ds = _suy(tao_df([{}]), ctx)
    assert len(ds) == 11
    assert ds[0].buoc.startswith("Tập hợp CP NVL") and ds[-1].buoc.startswith("TK đầu 5/6/7/8")


def test_khong_phat_sinh_thi_khong_ap_dung(ctx):
    b, _ = _suy(tao_df([{"DebitAccount": "1111", "CreditAccount": "1121"}]), ctx)
    assert b["Tập hợp CP NVL trực tiếp 621 → 154"].trang_thai == tt.KHONG_AP_DUNG
    assert b["Kết chuyển giá vốn 632 → 911"].trang_thai == tt.KHONG_AP_DUNG


def test_621_da_lam_can_ra_chua_lam(ctx):
    da = tao_df([{"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100},
                 {"DebitAccount": "154", "CreditAccount": "6214", "Amount": 100}])
    ra = tao_df([{"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100},
                 {"DebitAccount": "154", "CreditAccount": "6214", "Amount": 60}])
    chua = tao_df([{"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100}])
    k = "Tập hợp CP NVL trực tiếp 621 → 154"
    assert _suy(da, ctx)[0][k].trang_thai == tt.DA_LAM
    assert _suy(ra, ctx)[0][k].trang_thai == tt.CAN_RA and "40" in _suy(ra, ctx)[0][k].tom_tat
    assert _suy(chua, ctx)[0][k].trang_thai == tt.CHUA_LAM and b_ma(_suy(chua, ctx)[0][k]) == "C4.4"


def b_ma(b):
    return b.ma_check


def test_xuat_kho_gia_va_tk_pl_ve_0(ctx):
    df = tao_df([{"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 1, "UnitCost": 0, "Amount": 0},
                 {"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 10}])
    b, _ = _suy(df, ctx)
    assert b["Xuất kho có đầy đủ giá"].trang_thai == tt.CAN_RA
    assert b["TK đầu 5/6/7/8 đã về 0 (kết chuyển hết)"].trang_thai == tt.CAN_RA


def test_lai_lo_va_thue(ctx):
    df = tao_df([{"DebitAccount": "911", "CreditAccount": "6421"},
                 {"DebitAccount": "911", "CreditAccount": "4212"},
                 {"DebitAccount": "1331", "CreditAccount": "3311"},
                 {"DebitAccount": "1311", "CreditAccount": "33311"}])
    b, _ = _suy(df, ctx)
    assert b["Kết chuyển lãi/lỗ 911 ↔ 421"].trang_thai == tt.DA_LAM
    assert b["Khấu trừ thuế GTGT 33311 ↔ 1331"].trang_thai == tt.CHUA_LAM
