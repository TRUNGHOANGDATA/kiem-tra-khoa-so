"""Nhóm 8 — sẵn sàng cho Báo cáo quản trị (khoản mục chi phí & bộ phận).

Đúng luật "đừng cảnh báo từ sự vắng mặt": C8.1/C8.2 chỉ bật khi công ty THẬT SỰ
dùng khoản mục/bộ phận (có dòng đã điền). C8.2 tự suy theo TỪNG nhóm TK cấp 1 nên
621 (NVL trực tiếp, không phân bổ bộ phận) tự động không bị bắt.
"""
from app.checks import g8_bao_cao_quan_tri as g8
from tests.conftest import tao_df


def _kq(df, ctx):
    return {r.ma: r for r in g8.kiem_tra(df, ctx)}


# ------------------------------------------------ C8.1 thiếu khoản mục
def test_c81_bat_dong_chi_phi_thieu_khoan_muc(ctx):
    df = tao_df([
        {"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 100, "ExpenseCatgCode": "2001"},
        {"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 50, "ExpenseCatgCode": None, "DocNo": "X"},
    ])
    r = _kq(df, ctx)["C8.1"]
    assert r.so_loi == 1 and r.muc_do_thuc == "vang"
    assert r.chi_tiet.iloc[0]["DocNo"] == "X"


def test_c81_khong_bat_khi_nhom_tk_khong_dung_khoan_muc(ctx):
    """Nhóm 642 kỳ này không dòng nào có khoản mục -> không suy ra thiếu sót (tự suy)."""
    df = tao_df([{"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 100, "ExpenseCatgCode": None}])
    assert _kq(df, ctx)["C8.1"].so_loi == 0


def test_c81_bo_qua_dong_khong_phai_chi_phi(ctx):
    df = tao_df([{"DebitAccount": "1111", "CreditAccount": "1121", "Amount": 100, "ExpenseCatgCode": None},
                 {"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 100, "ExpenseCatgCode": "2001"}])
    assert _kq(df, ctx)["C8.1"].so_loi == 0


# ------------------------------------------------ C8.2 thiếu bộ phận (tự suy)
def test_c82_tu_suy_bo_phan_theo_nhom_tk(ctx):
    df = tao_df([
        # nhóm 642 CÓ dùng bộ phận -> dòng trống bộ phận của 642 bị bắt
        {"DebitAccount": "6421", "CreditAccount": "1111", "DeptName": "P.Kế toán", "Amount": 10},
        {"DebitAccount": "6422", "CreditAccount": "1111", "DeptName": None, "Amount": 20, "DocNo": "Y"},
        # nhóm 621 KHÔNG dùng bộ phận (toàn trống) -> không bắt (NVL trực tiếp)
        {"DebitAccount": "621", "CreditAccount": "1521", "DeptName": None, "Amount": 30},
        {"DebitAccount": "621", "CreditAccount": "1521", "DeptName": None, "Amount": 40},
    ])
    r = _kq(df, ctx)["C8.2"]
    assert r.so_loi == 1 and r.chi_tiet.iloc[0]["DocNo"] == "Y"


def test_c82_khong_bat_khi_ca_ky_khong_dung_bo_phan(ctx):
    df = tao_df([{"DebitAccount": "6421", "CreditAccount": "1111", "DeptName": None, "Amount": 10}])
    assert _kq(df, ctx)["C8.2"].so_loi == 0


# ------------------------------------------------ C8.3 thống kê khoản mục × TK
def test_c83_tong_hop_theo_khoan_muc_tk(ctx):
    df = tao_df([
        {"DebitAccount": "6421", "CreditAccount": "1111", "ExpenseCatgCode": "2001",
         "ExpenseCatgName": "Thuê mặt bằng", "Amount": 100},
        {"DebitAccount": "6421", "CreditAccount": "1111", "ExpenseCatgCode": "2001",
         "ExpenseCatgName": "Thuê mặt bằng", "Amount": 50},
        {"DebitAccount": "627", "CreditAccount": "1111", "ExpenseCatgCode": "6233",
         "ExpenseCatgName": "Vật tư", "Amount": 30},
    ])
    r = _kq(df, ctx)["C8.3"]
    assert r.la_thong_ke
    hang = {(x["TK"], x["ma_khoan_muc"]): x for x in r.chi_tiet.to_dict("records")}
    assert hang[("642", "2001")]["tong"] == 150 and hang[("642", "2001")]["so_dong"] == 2
    assert hang[("627", "6233")]["tong"] == 30


def test_c83_frame_khong_chi_phi_khong_no(ctx):
    df = tao_df([{"DebitAccount": "1111", "CreditAccount": "1121", "Amount": 100}])
    r = _kq(df, ctx)["C8.3"]
    assert r.la_thong_ke and len(r.chi_tiet) == 0


def test_c81_khong_bat_ket_chuyen_doanh_thu(ctx):
    """Nợ 515/711 chỉ là bút toán kết chuyển doanh thu, không mang khoản mục —
    không được coi là 'chi phí thiếu khoản mục' (hồi quy từ file BC quản trị thật)."""
    df = tao_df([{"DebitAccount": "5154", "CreditAccount": "911", "Amount": 211_503_625, "ExpenseCatgCode": None},
                 {"DebitAccount": "71181", "CreditAccount": "911", "Amount": 2_419_910_979, "ExpenseCatgCode": None}])
    assert _kq(df, ctx)["C8.1"].so_loi == 0


def test_du_3_ma(ctx):
    assert [r.ma for r in g8.kiem_tra(tao_df([{}]), ctx)] == ["C8.1", "C8.2", "C8.3"]
