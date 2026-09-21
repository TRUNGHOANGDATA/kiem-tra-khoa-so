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


# ------------------------------------------------------------------ drift CĐPS
def _cdps(rows):
    mac = {"account": "1111", "ten": "", "du_dau_no": 0.0, "du_dau_co": 0.0, "ps_no": 0.0,
           "ps_co": 0.0, "du_cuoi_no": 0.0, "du_cuoi_co": 0.0, "is_group": 0, "level": 1}
    return pd.DataFrame([{**mac, **r} for r in rows], columns=COLS)


def test_so_sanh_cdps_lan_dau_thi_khong_co_gi_de_so(tmp_path):
    k = KhoChotSo(str(tmp_path / "k.sqlite"))
    assert k.so_sanh_cdps("A08", 2026, 8, _cdps([{"account": "1111", "ps_no": 100}])) is None
    k.dong()


def test_so_sanh_cdps_y_het_thi_khong_bao(tmp_path):
    df = _cdps([{"account": "1111", "ps_no": 100}, {"account": "5111", "ps_co": 100}])
    k = KhoChotSo(str(tmp_path / "k.sqlite"))
    k.luu_cdps("A08", 2026, 8, df)
    assert k.so_sanh_cdps("A08", 2026, 8, df) is None
    k.dong()


def test_so_sanh_cdps_bat_tk_doi_so(tmp_path):
    cu = _cdps([{"account": "1111", "ps_no": 100}, {"account": "5111", "ps_co": 100}])
    moi = _cdps([{"account": "1111", "ps_no": 150}, {"account": "5111", "ps_co": 100}])
    k = KhoChotSo(str(tmp_path / "k.sqlite"))
    k.luu_cdps("A08", 2026, 8, cu)
    d = k.so_sanh_cdps("A08", 2026, 8, moi)
    k.dong()
    assert d["so_doi"] == 1 and d["so_them"] == 0 and d["so_bot"] == 0
    assert d["dong"][0]["account"] == "1111" and d["dong"][0]["ps_no_cu"] == 100


def test_so_sanh_cdps_bat_tk_them_va_bot(tmp_path):
    cu = _cdps([{"account": "1111", "ps_no": 100}, {"account": "5111", "ps_co": 100}])
    moi = _cdps([{"account": "1111", "ps_no": 100}, {"account": "6421", "ps_no": 7}])
    k = KhoChotSo(str(tmp_path / "k.sqlite"))
    k.luu_cdps("A08", 2026, 8, cu)
    d = k.so_sanh_cdps("A08", 2026, 8, moi)
    k.dong()
    assert (d["so_them"], d["so_bot"], d["so_doi"]) == (1, 1, 0)


# ------------------------------------------------------- CĐPS của kỳ liền trước
def test_doc_cdps_ky_truoc_lui_mot_thang(tmp_path):
    k = KhoChotSo(str(tmp_path / "k.sqlite"))
    k.luu_cdps("A08", 2026, 7, _cdps([{"account": "1111", "du_cuoi_no": 500}]))
    assert k.doc_cdps_ky_truoc("A08", 2026, 8)["account"].tolist() == ["1111"]
    assert k.doc_cdps_ky_truoc("A08", 2026, 7).empty        # kỳ 06 chưa nạp -> rỗng
    assert k.doc_cdps_ky_truoc("A07", 2026, 8).empty        # chi nhánh khác -> rỗng
    k.dong()


def test_doc_cdps_ky_truoc_thang_1_lui_ve_thang_12_nam_truoc(tmp_path):
    k = KhoChotSo(str(tmp_path / "k.sqlite"))
    k.luu_cdps("A08", 2025, 12, _cdps([{"account": "1111", "du_cuoi_no": 500}]))
    assert k.doc_cdps_ky_truoc("A08", 2026, 1)["account"].tolist() == ["1111"]
    k.dong()


def test_so_sanh_cdps_chiu_duoc_ma_tk_lap(tmp_path):
    """CĐPS thật có mã lặp (A01: 6222 và 8118 mỗi mã 2 dòng) — `.loc` trả Series
    làm cả nút "Nạp lại CĐPS" chết với 'float() argument ... not Series'."""
    cu = _cdps([{"account": "6222", "ps_no": 100}, {"account": "6222", "ps_no": 50},
                {"account": "1111", "ps_no": 10}])
    moi = _cdps([{"account": "6222", "ps_no": 100}, {"account": "6222", "ps_no": 50},
                 {"account": "1111", "ps_no": 70}])
    k = KhoChotSo(str(tmp_path / "k.sqlite"))
    k.luu_cdps("A01", 2026, 8, cu)
    d = k.so_sanh_cdps("A01", 2026, 8, moi)
    k.dong()
    assert d["so_doi"] == 1 and d["dong"][0]["account"] == "1111"


def test_so_sanh_cdps_ma_lap_doi_so_thi_van_bat(tmp_path):
    cu = _cdps([{"account": "8118", "ps_no": 100}, {"account": "8118", "ps_no": 50}])
    moi = _cdps([{"account": "8118", "ps_no": 100}, {"account": "8118", "ps_no": 900}])
    k = KhoChotSo(str(tmp_path / "k.sqlite"))
    k.luu_cdps("A01", 2026, 8, cu)
    d = k.so_sanh_cdps("A01", 2026, 8, moi)
    k.dong()
    assert d["so_doi"] == 1 and d["dong"][0]["account"] == "8118"


def test_xac_nhan_cdps_cham_dau_thoi_gian_khong_doi_du_lieu(tmp_path):
    """Nạp lại mà số liệu y hệt thì không ghi đè, nhưng vẫn phải ghi nhận "đã đối chiếu
    lúc này" — nếu không, dấu thời gian mãi là lần nạp đầu và cảnh báo "CĐPS cũ hơn
    bảng kê" kêu oan sau mỗi lần người dùng nạp lại để kiểm chứng."""
    kho = KhoChotSo(str(tmp_path / "k.sqlite"))
    rows = [["632", "GVHB", 0, 0, 15_944, 0, 0, 0, False, 0]]
    kho.luu_cdps("A02", 2026, 8, _df(rows), thoi_diem="2026-09-19T11:16:00")
    assert kho.thoi_diem_nap_cdps("A02", 2026, 8) == "2026-09-19T11:16:00"

    kho.xac_nhan_cdps("A02", 2026, 8, thoi_diem="2026-09-21T10:30:00")
    assert kho.thoi_diem_nap_cdps("A02", 2026, 8) == "2026-09-21T10:30:00"
    got = kho.doc_cdps("A02", 2026, 8)
    assert len(got) == 1 and float(got.iloc[0]["ps_no"]) == 15_944   # dữ liệu nguyên vẹn
    kho.dong()


def test_xac_nhan_cdps_ky_chua_co_thi_khong_tao_gi(tmp_path):
    kho = KhoChotSo(str(tmp_path / "k.sqlite"))
    kho.xac_nhan_cdps("A09", 2026, 8)
    assert kho.doc_cdps("A09", 2026, 8).empty
    assert kho.thoi_diem_nap_cdps("A09", 2026, 8) is None
    kho.dong()
