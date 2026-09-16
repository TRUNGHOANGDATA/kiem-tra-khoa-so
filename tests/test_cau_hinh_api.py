from app.api import JsApi
from app import cau_hinh


def test_thu_muc_doc_tu_cau_hinh(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)   # ep GOC ve tmp
    cau_hinh.ghi_cau_hinh(str(tmp_path), {"thu_muc_nguon": "Nguon", "thu_muc_xuat": "Xuat", "thu_muc_kho": "Kho"})
    api = JsApi()
    assert api.thu_muc_source == str(tmp_path / "Nguon")
    assert api.thu_muc_report == str(tmp_path / "Xuat")
    assert api._thu_muc_kho == str(tmp_path / "Kho")


def test_gan_de_van_thang_cau_hinh(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    api.thu_muc_source = str(tmp_path / "ghi_de")     # gan thang -> override
    assert api.thu_muc_source == str(tmp_path / "ghi_de")
    api._thu_muc_kho = str(tmp_path / "kho_de")
    assert api._thu_muc_kho == str(tmp_path / "kho_de")


def test_luu_roi_doc_lai_phan_anh_ngay(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    k = api.luu_cau_hinh({"thu_muc_nguon": "A", "thu_muc_xuat": "B", "thu_muc_kho": "C"})
    assert k["ok"] is True
    assert api.thu_muc_source == str(tmp_path / "A")   # doc lai moi lan dung -> thay ngay


def test_luu_gia_tri_trong_dung_mac_dinh(tmp_path, monkeypatch):
    # O trong/toan khoang trang khong duoc luu nguyen (se giai thanh GOC) -> phai
    # bi thay bang thu muc con mac dinh truoc khi ghi.
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    k = api.luu_cau_hinh({"thu_muc_nguon": "A", "thu_muc_xuat": "  ", "thu_muc_kho": ""})
    assert k["ok"] is True
    assert api.thu_muc_report == str(tmp_path / "2. Report")
    assert api._thu_muc_kho == str(tmp_path / "3. Chot so")
