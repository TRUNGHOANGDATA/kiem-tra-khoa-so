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

def test_khong_ghi_duoc_thi_van_tra_gia_tri_khong_nem(tmp_path, monkeypatch):
    # GOC khong the ghi (vd chi doc) -> _ghi_tho nem OSError khi tao file lan dau;
    # doc_cau_hinh KHONG duoc nem ra ngoai, phai tra ve gia tri MAC_DINH da giai.
    def _ghi_loi(goc, cfg):
        raise OSError("khong ghi duoc")
    monkeypatch.setattr(cau_hinh, "_ghi_tho", _ghi_loi)
    cfg = cau_hinh.doc_cau_hinh(str(tmp_path))
    assert cfg["thu_muc_nguon"] == str(tmp_path / "1. Source")
    assert cfg["thu_muc_xuat"] == str(tmp_path / "2. Report")
    assert cfg["thu_muc_kho"] == str(tmp_path / "3. Chot so")
    assert not (tmp_path / "cau-hinh.json").exists()   # ghi that bai -> khong co file

def test_first_run_seed_tu_file_mau(tmp_path):
    # co san file mau -> cau-hinh.json tao ra phai theo mau, va bo qua khoa _huong_dan
    (tmp_path / "cau-hinh.mau.json").write_text(
        json.dumps({"_huong_dan": "ghi chu", "thu_muc_nguon": "NguonMau",
                    "thu_muc_xuat": "XuatMau", "thu_muc_kho": "KhoMau"}, ensure_ascii=False),
        encoding="utf-8")
    cfg = cau_hinh.doc_cau_hinh(str(tmp_path))
    assert cfg["thu_muc_nguon"] == str(tmp_path / "NguonMau")   # gia tri tu mau
    tho = json.loads((tmp_path / "cau-hinh.json").read_text(encoding="utf-8"))
    # 3 khoa thu muc + khoa quy doi chi nhanh (rong), bo _huong_dan
    assert set(tho.keys()) == {"thu_muc_nguon", "thu_muc_xuat", "thu_muc_kho", "quy_doi_chi_nhanh"}


def test_quy_doi_luu_roi_doc_lai(tmp_path):
    cau_hinh.ghi_cau_hinh(str(tmp_path), {"quy_doi_chi_nhanh": {"A01": "Nhà máy Hải Phòng", "A02": "Kho Hà Nội"}})
    assert cau_hinh.doc_quy_doi(str(tmp_path)) == {"A01": "Nhà máy Hải Phòng", "A02": "Kho Hà Nội"}


def test_quy_doi_bo_cap_rong_va_khoang_trang(tmp_path):
    cau_hinh.ghi_cau_hinh(str(tmp_path), {"quy_doi_chi_nhanh": {"A01": "  Nhà máy  ", "A02": "   ", "": "X"}})
    assert cau_hinh.doc_quy_doi(str(tmp_path)) == {"A01": "Nhà máy"}   # A02 rong va ma rong -> bo


def test_luu_thu_muc_khong_xoa_quy_doi(tmp_path):
    cau_hinh.ghi_cau_hinh(str(tmp_path), {"quy_doi_chi_nhanh": {"A01": "Nhà máy"}})
    cau_hinh.ghi_cau_hinh(str(tmp_path), {"thu_muc_nguon": "D:/Nguon"})   # chi luu thu muc
    assert cau_hinh.doc_quy_doi(str(tmp_path)) == {"A01": "Nhà máy"}       # ban do van con
    assert cau_hinh.doc_cau_hinh(str(tmp_path))["thu_muc_nguon"] == "D:/Nguon"


def test_luu_quy_doi_khong_xoa_thu_muc(tmp_path):
    cau_hinh.ghi_cau_hinh(str(tmp_path), {"thu_muc_nguon": "D:/Nguon"})
    cau_hinh.ghi_cau_hinh(str(tmp_path), {"quy_doi_chi_nhanh": {"A01": "Nhà máy"}})  # chi luu ban do
    assert cau_hinh.doc_cau_hinh(str(tmp_path))["thu_muc_nguon"] == "D:/Nguon"        # thu muc van con
