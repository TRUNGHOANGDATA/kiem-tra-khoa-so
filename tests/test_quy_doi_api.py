"""Quy đổi chi nhánh lưu trong kho SQLite (không còn trong cau-hinh.json) + di trú."""
from pathlib import Path

from app import cau_hinh
from app.api import JsApi


def test_quy_doi_doc_tu_kho(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    kho = api._kho()
    try:
        kho.ghi_quy_doi({"A01": "Nhà máy Hải Phòng"})
    finally:
        kho.dong()
    assert api._quy_doi == {"A01": "Nhà máy Hải Phòng"}


def test_luu_cau_hinh_ghi_map_vao_kho_va_xoa_ma_vang(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    assert api.luu_cau_hinh({"quy_doi_chi_nhanh": {"A01": "Nhà máy", "A02": "Kho"}})["ok"]
    assert api._quy_doi == {"A01": "Nhà máy", "A02": "Kho"}
    assert api.luu_cau_hinh({"quy_doi_chi_nhanh": {"A01": "Nhà máy"}})["ok"]   # A02 vắng -> xóa
    assert api._quy_doi == {"A01": "Nhà máy"}


def test_map_khong_con_luu_trong_json(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    api.luu_cau_hinh({"quy_doi_chi_nhanh": {"A01": "Nhà máy"}})
    assert cau_hinh.doc_quy_doi(str(tmp_path)) == {}   # JSON không giữ bản đồ nữa


def test_di_tru_map_tu_json_sang_kho_mot_lan(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    cau_hinh.ghi_cau_hinh(str(tmp_path), {"quy_doi_chi_nhanh": {"A01": "Cũ trong JSON"}})
    api = JsApi()
    assert api._quy_doi == {"A01": "Cũ trong JSON"}       # đọc được (đã chép sang kho)
    assert cau_hinh.doc_quy_doi(str(tmp_path)) == {}      # JSON đã dọn sạch
    kho = api._kho()
    try:
        assert kho.doc_quy_doi() == {"A01": "Cũ trong JSON"}   # nằm trong kho
    finally:
        kho.dong()


def test_lay_cau_hinh_lay_map_tu_kho(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    api.luu_cau_hinh({"quy_doi_chi_nhanh": {"A01": "Nhà máy"}})
    r = api.lay_cau_hinh()
    assert r["quy_doi"] == {"A01": "Nhà máy"}
    assert "A01" in r["ma_goi_y"]


def test_doc_map_rong_khong_tao_file_kho(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    assert api._quy_doi == {}
    assert not Path(api._duong_dan_kho()).exists()   # đọc map rỗng KHÔNG tạo kho thừa
