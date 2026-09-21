"""Seed bộ cài không được nhúng dữ liệu tài chính thật (CĐPS) hay chạm kho thật."""
import json

from app.cau_hinh import MAC_DINH
from app.kho import KhoChotSo
from tools import tao_seed


def test_seed_khong_nhung_cdps(monkeypatch, tmp_path):
    # ép nguồn tên chi nhánh vào tmp, không đọc file chi_nhanh.json thật ở gốc repo
    cn = tmp_path / "chi_nhanh.json"
    cn.write_text(json.dumps({"A01": "Hà Nội"}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(tao_seed, "FILE_CHI_NHANH", cn)

    seed = tmp_path / "_seed"
    tao_seed.dung(seed)

    # kho có bảng quy đổi tên nhưng KHÔNG có CĐPS nào
    kho = KhoChotSo(str(seed / MAC_DINH["thu_muc_kho"] / "kho_chot_so.sqlite"))
    try:
        assert kho.doc_quy_doi().get("A01") == "Hà Nội"
        assert kho.trang_thai_cdps() == []          # <-- không nhúng CĐPS
    finally:
        kho.dong()
    # không copy file CĐPS gốc vào seed
    assert not list((seed / MAC_DINH["thu_muc_nguon"]).rglob("*.xlsx"))
