"""Định vị thư mục — tách rõ DỮ LIỆU (ghi được) khỏi TÀI NGUYÊN (chỉ đọc).

Chạy từ mã nguồn: cả hai đều là gốc repo, giữ nguyên nếp cũ.
Bản đóng gói (PyInstaller): tài nguyên nằm trong `sys._MEIPASS` (chỉ đọc), còn dữ
liệu người dùng phải ra `%LOCALAPPDATA%\\KiemTraKhoaSo` — vì thư mục cài (Program
Files) không ghi được. Lần đầu chạy tự bày sẵn kho + cấu hình từ `_seed` đã đóng
kèm, để mở lên là dùng được ngay.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

TEN_APP = "KiemTraKhoaSo"


def _dong_goi() -> bool:
    return bool(getattr(sys, "frozen", False))


def thu_muc_tai_nguyen() -> Path:
    """Nơi chứa tài nguyên chỉ-đọc (webapp, app.ico, _seed)."""
    if _dong_goi():
        return Path(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))
    return Path(__file__).resolve().parents[1]


def thu_muc_du_lieu() -> Path:
    """Nơi ghi cấu hình / kho / báo cáo. Tạo sẵn nếu chưa có (bản đóng gói)."""
    if not _dong_goi():
        return Path(__file__).resolve().parents[1]
    base = os.environ.get("LOCALAPPDATA") or str(Path.home())
    d = Path(base) / TEN_APP
    d.mkdir(parents=True, exist_ok=True)
    return d


def bay_seed_neu_can() -> None:
    """Lần đầu chạy bản đóng gói: chép `_seed` (kho dựng sẵn, cấu hình, khung thư mục)
    sang thư mục dữ liệu. Không đè lên thứ người dùng đã có."""
    if not _dong_goi():
        return
    seed = thu_muc_tai_nguyen() / "_seed"
    if not seed.is_dir():
        return
    dich = thu_muc_du_lieu()
    for src in seed.rglob("*"):
        rel = src.relative_to(seed)
        out = dich / rel
        if src.is_dir():
            out.mkdir(parents=True, exist_ok=True)
        elif not out.exists():                 # giữ nguyên dữ liệu người dùng đã có
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out)
