"""Lưu/đọc CĐPS trong kho SQLite + trạng thái đã nhập theo (chi nhánh × kỳ)."""
import pandas as pd

from app.kho import KhoChotSo, ket_noi

COLS = ["account", "ten", "du_dau_no", "du_dau_co", "ps_no", "ps_co",
        "du_cuoi_no", "du_cuoi_co", "is_group", "level"]


def _df(rows):
    return pd.DataFrame(rows, columns=COLS)


def test_mo_kho_co_bang_cdps(tmp_path):
    con = ket_noi.mo_kho(str(tmp_path / "k.sqlite"))
    ten = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "cdps" in ten
    con.close()


def test_luu_doc_cdps(tmp_path):
    kho = KhoChotSo(str(tmp_path / "k.sqlite"))
    kho.luu_cdps("A08", 2026, 8, _df([
        ["421", "LN", 2981950998, 0, 0, 1571960518, 1409990480, 0, True, 0],
        ["4212", "LN chua pp", 2981950998, 0, 0, 1571960518, 1409990480, 0, False, 1],
        ["911", "XDKQ", 0, 0, 11403455364, 11403455364, 0, 0, False, 0],
    ]))
    got = kho.doc_cdps("A08", 2026, 8)
    assert len(got) == 3
    assert kho.doc_cdps("A08", 2026, 9).empty          # kỳ chưa nhập -> rỗng
    kho.dong()


def test_du_dau_theo_prefix_chi_cong_dong_la(tmp_path):
    kho = KhoChotSo(str(tmp_path / "k.sqlite"))
    kho.luu_cdps("A08", 2026, 8, _df([
        ["421", "LN", 2981950998, 0, 0, 0, 0, 0, True, 0],    # nhóm -> KHÔNG cộng
        ["4212", "LN", 2981950998, 0, 0, 0, 0, 0, False, 1],  # lá -> cộng
    ]))
    no, co = kho.du_dau_theo_prefix("A08", 2026, 8, "421")
    assert no == 2981950998.0 and co == 0.0
    kho.dong()


def test_nap_lai_ky_ghi_de_sach(tmp_path):
    kho = KhoChotSo(str(tmp_path / "k.sqlite"))
    kho.luu_cdps("A08", 2026, 8, _df([["911", "x", 0, 0, 1, 1, 0, 0, False, 0]]))
    kho.luu_cdps("A08", 2026, 8, _df([["133", "y", 5, 0, 2, 2, 3, 0, False, 0]]))
    got = kho.doc_cdps("A08", 2026, 8)
    assert list(got["account"]) == ["133"]
    kho.dong()


def test_co_cdps(tmp_path):
    kho = KhoChotSo(str(tmp_path / "k.sqlite"))
    assert kho.co_cdps("A08", 2026, 8) is False
    kho.luu_cdps("A08", 2026, 8, _df([["911", "x", 0, 0, 1, 1, 0, 0, False, 0]]))
    assert kho.co_cdps("A08", 2026, 8) is True
    kho.dong()


def test_trang_thai_cdps(tmp_path):
    kho = KhoChotSo(str(tmp_path / "k.sqlite"))
    kho.luu_cdps("A08", 2026, 8, _df([["911", "x", 0, 0, 1, 1, 0, 0, False, 0]]))
    kho.luu_cdps("A07", 2026, 8, _df([["911", "x", 0, 0, 1, 1, 0, 0, False, 0]]))
    ds = kho.trang_thai_cdps()
    assert {(r["chi_nhanh"], r["ky_nam"], r["ky_thang"]) for r in ds} == {("A08", 2026, 8), ("A07", 2026, 8)}
    kho.dong()
