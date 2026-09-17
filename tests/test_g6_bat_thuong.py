"""Đợt 3 — bút toán bất thường trong sổ (C6.7 đột biến, C6.8 cặp định khoản hiếm).

Cả hai để mức THỐNG KÊ: chúng nêu chỗ ĐÁNG NHÌN chứ không chứng minh được sai.
Ngưỡng lấy từ file 8 chi nhánh thật (xem docstring trong g6_tong_quan.py).
"""
from app.checks import g6_tong_quan as g6
from tests.conftest import tao_df


def _kq(df, ctx):
    return {r.ma: r for r in g6.kiem_tra(df, ctx)}


def _nhom(tk, n, tien):
    return [{"DebitAccount": tk, "CreditAccount": "1111", "Amount": tien} for _ in range(n)]


# --------------------------------------------------------------- C6.7 đột biến
def test_c67_la_thong_ke(ctx):
    c = _kq(tao_df(_nhom("6421", 40, 1_000_000)), ctx)["C6.7"]
    assert c.la_thong_ke is True and c.so_loi == 0


def test_c67_bat_giao_dich_vuot_han_do_phan_tan_cua_tk(ctx):
    rows = [{"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 1_000_000 + i}
            for i in range(40)]
    rows.append({"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 500_000_000})
    c = _kq(tao_df(rows), ctx)["C6.7"]
    assert c.chi_tiet["Amount"].tolist() == [500_000_000]


def test_c67_mot_tai_khoan_khong_chiem_het_danh_sach(ctx):
    """1331 từng chiếm trọn 50 dòng của A08 — mỗi TK tối đa 5 dòng."""
    rows = [{"DebitAccount": "1331", "CreditAccount": "3311", "Amount": 10_000 + i}
            for i in range(60)]
    rows += [{"DebitAccount": "1331", "CreditAccount": "3311", "Amount": 900_000_000 + i}
             for i in range(20)]
    assert len(_kq(tao_df(rows), ctx)["C6.7"].chi_tiet) <= 5


def test_c67_bo_qua_but_toan_ket_chuyen(ctx):
    """Nợ 154 / Có 621 luôn là khoản lớn nhất của 154 — nhắc là nhắc chuyện đương nhiên."""
    rows = [{"DebitAccount": "154", "CreditAccount": "6214", "Amount": 1_000_000 + i}
            for i in range(40)]
    rows.append({"DebitAccount": "154", "CreditAccount": "6214", "Amount": 3_000_000_000})
    assert _kq(tao_df(rows), ctx)["C6.7"].chi_tiet.empty


def test_c67_bo_qua_nhom_qua_it_dong(ctx):
    """Độ phân tán của 5 dòng không phải 'mặt bằng' — suy từ đó là bịa."""
    rows = [{"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 1_000_000 + i}
            for i in range(5)]
    rows.append({"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 500_000_000})
    assert _kq(tao_df(rows), ctx)["C6.7"].chi_tiet.empty


def test_c67_nguong_co_gian_theo_do_phan_tan_cua_tk(ctx):
    """Cùng một số tiền: đột biến ở TK chi đều, bình thường ở TK vốn trải rộng.

    Đây là lý do bỏ "gấp N lần trung vị": 1331 (thuế đầu vào) có trung vị 19.704đ
    nên mọi hóa đơn lớn đều gấp hơn 1.000 lần — cả 50 dòng của A08 đều là 1331.
    """
    deu = [{"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 1_000_000 + i}
           for i in range(60)]
    rong = [{"DebitAccount": "1331", "CreditAccount": "3311", "Amount": 1_000_000 * (i + 1)}
            for i in range(60)]
    lon = {"Amount": 500_000_000}
    assert len(_kq(tao_df(deu + [{**deu[0], **lon}]), ctx)["C6.7"].chi_tiet) == 1
    assert _kq(tao_df(rong + [{**rong[0], **lon}]), ctx)["C6.7"].chi_tiet.empty


# ------------------------------------------------------ C6.8 cặp định khoản hiếm
def test_c68_la_thong_ke(ctx):
    assert _kq(tao_df(_nhom("6421", 10, 1)), ctx)["C6.8"].la_thong_ke is True


def test_c68_chi_neu_cap_xuat_hien_it(ctx):
    rows = _nhom("6421", 10, 1_000)                       # 642/111 — 10 lần, phổ biến
    rows.append({"DebitAccount": "1388", "CreditAccount": "3388", "Amount": 9_000})  # 1 lần
    rows += [{"DebitAccount": "2411", "CreditAccount": "3311", "Amount": 5_000}] * 2  # 2 lần
    rows.append({"DebitAccount": "911", "CreditAccount": "4212", "Amount": 7_000})   # kết chuyển
    c = _kq(tao_df(rows), ctx)["C6.8"]
    assert sorted(c.chi_tiet["cap_dinh_khoan"]) == ["138/338", "241/331"]
    d = dict(zip(c.chi_tiet["cap_dinh_khoan"], c.chi_tiet["so_lan"]))
    assert d == {"138/338": 1, "241/331": 2}


def test_c68_gop_theo_tai_khoan_cap_1(ctx):
    """13881/33881 và 13882/33882 là CÙNG một cặp 138/338 — không phải hai cặp hiếm."""
    rows = _nhom("6421", 10, 1_000)
    rows += [{"DebitAccount": f"1388{i}", "CreditAccount": f"3388{i}", "Amount": 1_000}
             for i in range(1, 4)]
    c = _kq(tao_df(rows), ctx)["C6.8"]
    assert c.chi_tiet.empty                  # 138/338 xuất hiện 3 lần -> không hiếm
