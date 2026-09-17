"""Định vị thư mục khi chạy từ mã nguồn và khi đóng gói (frozen).

Bản đóng gói KHÔNG được ghi vào thư mục cài (Program Files chỉ đọc) — dữ liệu phải
nằm ở thư mục người dùng, và lần đầu chạy phải tự bày sẵn (seed) kho + cấu hình để
mở lên là dùng được ngay, không cần thao tác gì.
"""
import sys

from app import duong_dan


def test_khi_chay_ma_nguon_goc_la_repo(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    goc = duong_dan.thu_muc_du_lieu()
    assert (goc / "app").is_dir() and (goc / "requirements.txt").exists()


def test_khi_dong_goi_du_lieu_o_thu_muc_nguoi_dung(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "appdata"))
    goc = duong_dan.thu_muc_du_lieu()
    assert str(tmp_path / "appdata") in str(goc)
    assert str(tmp_path / "bundle") not in str(goc)      # KHÔNG ghi vào thư mục cài


def test_seed_lan_dau_chep_kho_va_cau_hinh(monkeypatch, tmp_path):
    bundle = tmp_path / "bundle"
    (bundle / "_seed" / "3. Chot so").mkdir(parents=True)
    (bundle / "_seed" / "3. Chot so" / "kho_chot_so.sqlite").write_bytes(b"SEED-DB")
    (bundle / "_seed" / "cau-hinh.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    data = tmp_path / "appdata" / "KiemTraKhoaSo"
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "appdata"))

    duong_dan.bay_seed_neu_can()
    assert (data / "3. Chot so" / "kho_chot_so.sqlite").read_bytes() == b"SEED-DB"
    assert (data / "cau-hinh.json").exists()


def test_seed_khong_de_len_du_lieu_da_co(monkeypatch, tmp_path):
    bundle = tmp_path / "bundle"
    (bundle / "_seed" / "3. Chot so").mkdir(parents=True)
    (bundle / "_seed" / "3. Chot so" / "kho_chot_so.sqlite").write_bytes(b"SEED-DB")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "appdata"))
    data = tmp_path / "appdata" / "KiemTraKhoaSo" / "3. Chot so"
    data.mkdir(parents=True)
    (data / "kho_chot_so.sqlite").write_bytes(b"DU-LIEU-THAT")     # người dùng đã có kho

    duong_dan.bay_seed_neu_can()
    assert (data / "kho_chot_so.sqlite").read_bytes() == b"DU-LIEU-THAT"   # KHÔNG bị đè
