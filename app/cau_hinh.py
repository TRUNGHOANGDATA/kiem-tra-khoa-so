"""Cấu hình thư mục (Nguồn/Xuất/Kho) — đọc JSON, tự tạo từ mẫu, đọc lại mỗi lần dùng.

Đường dẫn tương đối giải theo gốc repo; đường dẫn tuyệt đối giữ nguyên. Ghi/đọc
không bao giờ ném ra ngoài: file hỏng/thiếu khóa -> bù mặc định, để một file JSON
gõ nhầm không làm chết app."""
from __future__ import annotations

import json
from pathlib import Path

KHOA = ("thu_muc_nguon", "thu_muc_xuat", "thu_muc_kho")
MAC_DINH = {"thu_muc_nguon": "1. Source", "thu_muc_xuat": "2. Report", "thu_muc_kho": "3. Chot so"}


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
        try:
            _ghi_tho(goc, sach)
        except OSError:
            return sach   # không ghi được kho cấu hình -> vẫn trả giá trị, KHÔNG ném
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(MAC_DINH)


def _ghi_tho(goc: str, cfg: dict) -> None:
    sach = {k: str(cfg.get(k, MAC_DINH[k])) for k in KHOA}
    duong_dan_cau_hinh(goc).write_text(json.dumps(sach, ensure_ascii=False, indent=2), encoding="utf-8")


def doc_cau_hinh(goc: str) -> dict:
    tho = _doc_tho(goc)
    return {k: _giai(goc, str(tho.get(k, MAC_DINH[k]))) for k in KHOA}


def ghi_cau_hinh(goc: str, cfg: dict) -> None:
    _ghi_tho(goc, cfg)
