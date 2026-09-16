import json
from pathlib import Path
from app import cau_hinh

def test_doc_tao_file_tu_mac_dinh_khi_chua_co(tmp_path):
    cfg = cau_hinh.doc_cau_hinh(str(tmp_path))
    assert (tmp_path / "cau-hinh.json").exists()
    # tương đối -> giải theo gốc
    assert cfg["thu_muc_nguon"] == str(tmp_path / "1. Source")
    assert cfg["thu_muc_xuat"] == str(tmp_path / "2. Report")
    assert cfg["thu_muc_kho"] == str(tmp_path / "3. Chot so")

def test_doc_ton_trong_gia_tri_da_ghi(tmp_path):
    cau_hinh.ghi_cau_hinh(str(tmp_path), {"thu_muc_nguon": "D:/Ke Toan/Nguon",
                                          "thu_muc_xuat": "2. Report", "thu_muc_kho": "3. Chot so"})
    cfg = cau_hinh.doc_cau_hinh(str(tmp_path))
    assert cfg["thu_muc_nguon"] == "D:/Ke Toan/Nguon"           # tuyệt đối -> giữ nguyên
    assert cfg["thu_muc_xuat"] == str(tmp_path / "2. Report")   # tương đối -> giải

def test_json_hong_thi_ve_mac_dinh(tmp_path):
    (tmp_path / "cau-hinh.json").write_text("{ hỏng", encoding="utf-8")
    cfg = cau_hinh.doc_cau_hinh(str(tmp_path))
    assert cfg["thu_muc_kho"] == str(tmp_path / "3. Chot so")

def test_thieu_khoa_thi_bu_mac_dinh(tmp_path):
    (tmp_path / "cau-hinh.json").write_text(json.dumps({"thu_muc_nguon": "X"}), encoding="utf-8")
    cfg = cau_hinh.doc_cau_hinh(str(tmp_path))
    assert cfg["thu_muc_nguon"].endswith("X")
    assert cfg["thu_muc_xuat"] == str(tmp_path / "2. Report")   # khóa thiếu -> mặc định
