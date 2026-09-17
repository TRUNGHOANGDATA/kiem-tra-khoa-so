"""Cấu hình thư mục (Nguồn/Xuất/Kho) — đọc JSON, tự tạo từ mẫu, đọc lại mỗi lần dùng.

Đường dẫn tương đối giải theo gốc repo; đường dẫn tuyệt đối giữ nguyên. Ghi/đọc
không bao giờ ném ra ngoài: file hỏng/thiếu khóa -> bù mặc định, để một file JSON
gõ nhầm không làm chết app."""
from __future__ import annotations

import json
from pathlib import Path

KHOA = ("thu_muc_nguon", "thu_muc_xuat", "thu_muc_kho")
MAC_DINH = {"thu_muc_nguon": "1. Source", "thu_muc_xuat": "2. Report", "thu_muc_kho": "3. Chot so"}
# Quy đổi mã chi nhánh -> tên hiển thị (A01 = "Nhà máy Hải Phòng"). Chỉ để HIỂN THỊ:
# mã gốc vẫn là danh tính lưu trong kho chốt sổ, đổi tên không phá đối chiếu kỳ cũ.
KHOA_MAP = "quy_doi_chi_nhanh"


def _lam_sach_map(m) -> dict:
    """Chỉ giữ cặp mã->tên mà cả hai đều là chuỗi khác rỗng (đã cắt khoảng trắng)."""
    if not isinstance(m, dict):
        return {}
    sach = {}
    for k, v in m.items():
        ma, ten = str(k).strip(), str(v).strip()
        if ma and ten:
            sach[ma] = ten
    return sach


def duong_dan_cau_hinh(goc: str) -> Path:
    return Path(goc) / "cau-hinh.json"


def _giai(goc: str, gia_tri: str) -> str:
    p = Path(gia_tri)
    return gia_tri if p.is_absolute() else str(Path(goc) / gia_tri)


def _doc_tho(goc: str) -> dict:
    f = duong_dan_cau_hinh(goc)
    if not f.exists():
        mau = Path(goc) / "cau-hinh.mau.json"
        try:
            data = json.loads(mau.read_text(encoding="utf-8")) if mau.exists() else dict(MAC_DINH)
        except (OSError, json.JSONDecodeError):
            data = dict(MAC_DINH)
        sach = {k: data.get(k, MAC_DINH[k]) for k in KHOA}
        sach[KHOA_MAP] = data.get(KHOA_MAP, {})   # tôn trọng bảng quy đổi soạn sẵn trong file mẫu
        try:
            _ghi_tho(goc, sach)
        except OSError:
            return sach   # không ghi được kho cấu hình -> vẫn trả giá trị, KHÔNG ném
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(MAC_DINH)


def _ghi_tho(goc: str, cfg: dict) -> None:
    sach = {k: (str(cfg.get(k, MAC_DINH[k])).strip() or MAC_DINH[k]) for k in KHOA}
    sach[KHOA_MAP] = _lam_sach_map(cfg.get(KHOA_MAP, {}))
    duong_dan_cau_hinh(goc).write_text(json.dumps(sach, ensure_ascii=False, indent=2), encoding="utf-8")


def doc_cau_hinh(goc: str) -> dict:
    tho = _doc_tho(goc)
    return {k: _giai(goc, str(tho.get(k, MAC_DINH[k]))) for k in KHOA}


def doc_quy_doi(goc: str) -> dict:
    """Bảng quy đổi mã->tên hiển thị (rỗng nếu chưa cấu hình)."""
    tho = _doc_tho(goc)
    return _lam_sach_map(tho.get(KHOA_MAP, {}) if isinstance(tho, dict) else {})


def xoa_quy_doi(goc: str) -> None:
    """Dọn bản đồ quy đổi khỏi JSON (sau khi đã di trú sang kho SQLite). Giữ thư mục."""
    hien = _doc_tho(goc)
    moi = dict(hien) if isinstance(hien, dict) else {}
    moi[KHOA_MAP] = {}
    _ghi_tho(goc, moi)


def ghi_cau_hinh(goc: str, cfg: dict) -> None:
    """Ghi ĐÈ TỪNG KHÓA: chỉ khóa nào có trong `cfg` mới bị thay, còn lại giữ nguyên
    giá trị đang có trên đĩa. Nhờ vậy lưu thư mục không xóa bảng quy đổi và ngược lại."""
    hien = _doc_tho(goc)
    moi = dict(hien) if isinstance(hien, dict) else {}
    for k in KHOA:
        if k in cfg:
            moi[k] = cfg[k]
    if KHOA_MAP in cfg:
        moi[KHOA_MAP] = cfg[KHOA_MAP]
    _ghi_tho(goc, moi)
