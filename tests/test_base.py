import pandas as pd

from app.checks import base
from tests.conftest import tao_df


def test_bat_dau_theo_prefix():
    s = pd.Series(["6214", "632211", "1551", None])
    assert base.bat_dau(s, "621", "632").tolist() == [True, True, False, False]


def test_loc_dong_va_co_dong():
    df = tao_df([
        {"DebitAccount": "154", "CreditAccount": "6214"},
        {"DebitAccount": "911", "CreditAccount": "632111"},
    ])
    assert len(base.loc_dong(df, no=("154",), co=("621",))) == 1
    assert base.co_dong(df, no=("911",), co=("632",)) is True
    assert base.co_dong(df, no=("155",), co=("154",)) is False


def test_phat_sinh_theo_prefix():
    df = tao_df([
        {"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100},
        {"DebitAccount": "154", "CreditAccount": "6214", "Amount": 100},
    ])
    assert base.phat_sinh_theo_prefix(df, "621") == (100.0, 100.0)


def test_so_phat_sinh_tai_khoan_co_net():
    df = tao_df([
        {"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 300},
        {"DebitAccount": "911", "CreditAccount": "6421", "Amount": 200},
    ])
    bang = base.so_phat_sinh_tai_khoan(df).set_index("TK")
    assert bang.loc["6421", "ps_no"] == 300
    assert bang.loc["6421", "ps_co"] == 200
    assert bang.loc["6421", "net"] == 100


def test_tao_ket_qua_them_ly_do_va_dem_loi():
    df = tao_df([{"Description": ""}, {"Description": ""}])
    kq = base.tao_ket_qua(df, "C1.1", "Thiếu diễn giải", "G1", base.VANG, "Diễn giải trống")
    assert kq.so_loi == 2
    assert list(kq.chi_tiet.columns) == base.COT_CHUAN
    assert kq.chi_tiet["ly_do"].iloc[0] == "Diễn giải trống"
    assert kq.muc_do_thuc == base.VANG


def test_muc_do_thuc_xanh_khi_khong_loi():
    df = tao_df([]) if False else tao_df([{"Amount": 1}]).iloc[0:0]
    kq = base.tao_ket_qua(df, "C1.5", "Số tiền ≤ 0", "G1", base.DO, "x")
    assert kq.so_loi == 0 and kq.muc_do_thuc == base.XANH


def test_fmt_so():
    assert base.fmt_so(1234567.4) == "1.234.567"


def test_fmt_sl_giu_phan_thap_phan():
    """Số lượng lẻ phải in ra đúng: fmt_so(0.16) = "0" đọc thành "không có số lượng"."""
    assert base.fmt_sl(0.16) == "0,16"
    assert base.fmt_sl(2.429) == "2,429"
    assert base.fmt_sl(0.334) == "0,334"
    # số nguyên vẫn gọn, không đuôi 0 thừa; ngăn cách nghìn kiểu Việt Nam
    assert base.fmt_sl(10) == "10"
    assert base.fmt_sl(0) == "0"
    assert base.fmt_sl(1234.5) == "1.234,5"
    assert base.fmt_sl(-0.27) == "-0,27"
    assert base.fmt_sl(float("nan")) == ""


def test_khong_cau_chu_nao_lap_tu():
    """Câu hiển thị cho kế toán không được dính lỗi lặp từ ("Có Có 511 với TaxCode…").

    Quét thẳng chuỗi trong mã nguồn vì dữ liệu test không kích hoạt hết mọi check —
    bản thân lỗi này lọt tới người dùng đúng vì fixture không chạm C3.2.
    """
    import ast
    from pathlib import Path

    goc = Path(__file__).resolve().parents[1] / "app"
    xau = []
    for f in goc.rglob("*.py"):
        cay = ast.parse(f.read_text(encoding="utf-8"))
        for nut in ast.walk(cay):
            if isinstance(nut, ast.Constant) and isinstance(nut.value, str):
                tu = nut.value.split()
                lap = [a for a, b in zip(tu, tu[1:]) if a == b and any(k.isalpha() for k in a)]
                if lap:
                    xau.append(f"{f.name}:{nut.lineno} lặp {lap} — {nut.value[:60]}")
    assert xau == [], "\n".join(xau)
