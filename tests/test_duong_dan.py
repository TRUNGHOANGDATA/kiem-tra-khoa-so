"""giai_thu_muc_xuat: đường dẫn xuất báo cáo giải đúng, không chạm thư mục thật."""
from pathlib import Path

from app import duong_dan as dd


def test_duong_tuyet_doi_giu_nguyen(tmp_path):
    p = tmp_path / "bao cao cua toi"
    assert dd.giai_thu_muc_xuat(str(p)) == str(p)      # người dùng tự chọn -> theo họ


def test_mac_dinh_tuong_doi_dat_canh_app(tmp_path, monkeypatch):
    cai = tmp_path / "app"
    monkeypatch.setattr(dd, "_dong_goi", lambda: True)          # giả bản đóng gói
    monkeypatch.setattr(dd, "thu_muc_cai_dat", lambda: cai)
    d = dd.giai_thu_muc_xuat("2. Report")
    assert d == str(cai / "2. Report")                 # cạnh app
    assert (cai / "2. Report").is_dir()                # đã tạo sẵn


def test_thu_muc_cai_chi_doc_thi_lui_ve_du_lieu(tmp_path, monkeypatch):
    dulieu = tmp_path / "data"
    monkeypatch.setattr(dd, "_dong_goi", lambda: True)
    monkeypatch.setattr(dd, "thu_muc_cai_dat", lambda: tmp_path / "ro")
    monkeypatch.setattr(dd, "_ghi_duoc", lambda _p: False)      # giả thư mục cài chỉ-đọc
    monkeypatch.setattr(dd, "thu_muc_du_lieu", lambda: dulieu)
    assert dd.giai_thu_muc_xuat("2. Report") == str(dulieu / "2. Report")
