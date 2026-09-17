"""Bảng quy đổi mã chi nhánh -> tên hiển thị, lưu trong chính kho chốt sổ."""
import sqlite3

from app.kho import ket_noi, quy_doi
from app.kho.schema import PHIEN_BAN_SCHEMA


def test_mo_kho_co_bang_quy_doi(tmp_path):
    con = ket_noi.mo_kho(str(tmp_path / "kho.sqlite"))
    ten = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "quy_doi_chi_nhanh" in ten
    con.close()


def test_ghi_roi_doc_lai(tmp_path):
    con = ket_noi.mo_kho(str(tmp_path / "kho.sqlite"))
    quy_doi.ghi_toan_bo(con, {"A01": "Nhà máy Hải Phòng", "A02": "Kho Hà Nội"})
    assert quy_doi.doc(con) == {"A01": "Nhà máy Hải Phòng", "A02": "Kho Hà Nội"}
    con.close()


def test_doc_rong_khi_chua_co(tmp_path):
    con = ket_noi.mo_kho(str(tmp_path / "kho.sqlite"))
    assert quy_doi.doc(con) == {}
    con.close()


def test_ghi_toan_bo_xoa_ma_vang(tmp_path):
    con = ket_noi.mo_kho(str(tmp_path / "kho.sqlite"))
    quy_doi.ghi_toan_bo(con, {"A01": "Nhà máy", "A02": "Kho"})
    quy_doi.ghi_toan_bo(con, {"A01": "Nhà máy đổi tên"})   # A02 vắng -> phải bị xóa
    assert quy_doi.doc(con) == {"A01": "Nhà máy đổi tên"}
    con.close()


def test_ghi_toan_bo_rong_xoa_het(tmp_path):
    con = ket_noi.mo_kho(str(tmp_path / "kho.sqlite"))
    quy_doi.ghi_toan_bo(con, {"A01": "Nhà máy"})
    quy_doi.ghi_toan_bo(con, {})
    assert quy_doi.doc(con) == {}
    con.close()


def test_ghi_toan_bo_bo_cap_rong_va_cat_khoang_trang(tmp_path):
    con = ket_noi.mo_kho(str(tmp_path / "kho.sqlite"))
    quy_doi.ghi_toan_bo(con, {"A01": "  Nhà máy  ", "A02": "   ", "": "X"})
    assert quy_doi.doc(con) == {"A01": "Nhà máy"}
    con.close()


def test_xoa_mot_ma(tmp_path):
    con = ket_noi.mo_kho(str(tmp_path / "kho.sqlite"))
    quy_doi.ghi_toan_bo(con, {"A01": "Nhà máy", "A02": "Kho"})
    quy_doi.xoa(con, "A01")
    assert quy_doi.doc(con) == {"A02": "Kho"}
    con.close()


def test_kho_v1_cu_mo_lai_tu_len_v2_va_co_bang(tmp_path):
    """Kho tạo bởi bản cũ (schema v1, chưa có bảng quy đổi) khi mở lại phải tự có
    bảng quy_doi_chi_nhanh và schema_version được nâng lên phiên bản hiện tại."""
    p = tmp_path / "kho.sqlite"
    con = ket_noi.mo_kho(str(p))               # tạo kho hiện đại
    con.execute("DROP TABLE quy_doi_chi_nhanh")  # giả lập kho v1: bỏ bảng mới
    con.execute("UPDATE schema_version SET phien_ban = 1")
    con.commit()
    con.close()

    con = ket_noi.mo_kho(str(p))               # mở lại -> migrate
    ten = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "quy_doi_chi_nhanh" in ten
    assert con.execute("SELECT phien_ban FROM schema_version").fetchone()[0] == PHIEN_BAN_SCHEMA
    con.close()
