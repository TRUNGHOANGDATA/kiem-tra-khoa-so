"""api v5: nạp sổ chi tiết bán hàng, bảng kê tự vào kho, chặn cứng khi thiếu sổ, kiểm tra từ kho."""
import pandas as pd

from app.api import JsApi
from app.kho import BANG_KE
from tests.conftest import MAC_DINH_SBH, tao_df


def _bang_ke(tmp_path, rows, ten="bk.xlsx"):
    p = tmp_path / ten
    tao_df(rows).to_excel(p, sheet_name="Table1", index=False)
    return str(p)


def _so(thu_muc, rows, ten="So chi tiet ban hang A01 082026.xlsx"):
    thu_muc.mkdir(exist_ok=True)
    pd.DataFrame([{**MAC_DINH_SBH, **r} for r in rows]).to_excel(
        thu_muc / ten, sheet_name="Table1", index=False)


BAN = {"BranchCode": "A01", "DocCode": "HD", "DocNo": "0051998",
       "DebitAccount": "1311", "CreditAccount": "51111", "Amount": 1_000_000}
CHI = {"BranchCode": "A00", "DebitAccount": "6421", "CreditAccount": "1111"}


def test_nap_so_ban_hang_thu_muc_moi_giong_va_bo_qua(tmp_path):
    tm = tmp_path / "sbh"
    _so(tm, [{}])
    _so(tm, [{}], ten="Ghi chu linh tinh.xlsx")
    api = JsApi()
    r = api.nap_so_ban_hang_thu_muc(str(tm))
    assert [(x["chi_nhanh"], x["ky"], x["ket_qua"]) for x in r["nap"]] == [("A01", "08/2026", "moi")]
    assert [x["file"] for x in r["bo_qua"]] == ["Ghi chu linh tinh.xlsx"]
    assert api.nap_so_ban_hang_thu_muc(str(tm))["nap"][0]["ket_qua"] == "giong"
    assert api.trang_thai_so_ban_hang()[0]["chi_nhanh"] == "A01"


def test_nap_bang_ke_tu_ghi_vao_kho(tmp_path):
    api = JsApi()
    api._nap_nhieu([_bang_ke(tmp_path, [BAN])])
    kho = api._kho()
    try:
        assert [r["chi_nhanh"] for r in kho.trang_thai_nguon(BANG_KE)] == ["A01"]
        ra = kho.doc_nguon(BANG_KE, "A01", 2026, 8)
        assert ra["DocNo"].tolist() == api._dv[0].df["DocNo"].tolist()   # y hệt bản trong bộ nhớ
    finally:
        kho.dong()


def test_chan_cung_khi_co_ban_hang_ma_thieu_so(tmp_path):
    api = JsApi()
    api._nap_nhieu([_bang_ke(tmp_path, [BAN, CHI])])
    assert [x["chi_nhanh"] for x in api.thieu_so_ban_hang()] == ["A01"]
    assert api.khong_can_so_ban_hang() == ["A00"]          # không bán hàng -> không đòi
    _so(tmp_path / "sbh", [{}])
    api.nap_so_ban_hang_thu_muc(str(tmp_path / "sbh"))
    assert api.thieu_so_ban_hang() == []


def test_tra_lai_131_cung_doi_so_ban_hang(tmp_path):
    api = JsApi()
    api._nap_nhieu([_bang_ke(tmp_path, [{**CHI, "BranchCode": "A02", "DebitAccount": "52131",
                                         "CreditAccount": "1311"}])])
    assert [x["chi_nhanh"] for x in api.thieu_so_ban_hang()] == ["A02"]


def test_c32_chay_tren_so_ban_hang_trong_kho(tmp_path):
    _so(tmp_path / "sbh", [{"Amount3": 0}])
    api = JsApi()
    api.nap_so_ban_hang_thu_muc(str(tmp_path / "sbh"))
    p = _bang_ke(tmp_path, [BAN])
    api._nap_nhieu([p])
    kq = api.chay_kiem_tra([p])
    c32 = next(c for n in kq["nhom"] for c in n["checks"] if c["ma"] == "C3.2")
    assert c32["so_loi"] == 1 and not c32["la_thong_ke"]


def test_kiem_tra_tu_kho_khong_can_file(tmp_path):
    p = _bang_ke(tmp_path, [BAN])
    JsApi()._nap_nhieu([p])
    api = JsApi()                                          # phiên mới, chưa chọn file nào
    ky = api.ky_trong_kho()
    assert [(k["chi_nhanh"], k["ky"], k["co_so_ban_hang"]) for k in ky] == [("A01", "08/2026", False)]
    r = api.nap_tu_kho([ky[0]["khoa"]])
    assert r["cac_path"] == [] and r["so_dong"] == 1
    kq = api.chay_kiem_tra(r["cac_path"])
    assert "loi" not in kq and kq["tomtat"]["chi_nhanh"] == "A01"


def test_nap_tu_kho_ky_khong_co_bao_loi(tmp_path):
    assert "loi" in JsApi().nap_tu_kho(["A09|01/2026"])


def test_chon_nham_so_ban_hang_lam_bang_ke_bao_ro(tmp_path):
    _so(tmp_path, [{}])
    r = JsApi().nap_nhieu_file([str(tmp_path / "So chi tiet ban hang A01 082026.xlsx")])
    assert "SỔ CHI TIẾT BÁN HÀNG" in r["loi"]
