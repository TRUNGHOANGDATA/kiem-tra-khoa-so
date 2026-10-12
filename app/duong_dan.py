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


def thu_muc_cai_dat() -> Path:
    """Thư mục CHỨA ứng dụng (nơi đặt .exe). Bản đóng gói: cạnh exe (= {app} của bộ
    cài, per-user nên ghi được); chạy mã nguồn: gốc repo. Dùng làm nơi MẶC ĐỊNH để
    xuất báo cáo — cạnh phần mềm cho dễ tìm, thay vì chôn trong %LOCALAPPDATA%."""
    if _dong_goi():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def thu_muc_du_lieu() -> Path:
    """Nơi ghi cấu hình / kho / báo cáo. Tạo sẵn nếu chưa có (bản đóng gói)."""
    if not _dong_goi():
        return Path(__file__).resolve().parents[1]
    base = os.environ.get("LOCALAPPDATA") or str(Path.home())
    d = Path(base) / TEN_APP
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ghi_duoc(d: Path) -> bool:
    """Thử tạo thư mục + ghi một file dò rồi xóa — cách chắc chắn nhất để biết ghi
    được (os.access trên Windows không tin được vì ACL)."""
    try:
        d.mkdir(parents=True, exist_ok=True)
        probe = d / ".wtest"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def giai_thu_muc_xuat(raw: str) -> str:
    """Giải đường dẫn xuất báo cáo. Tuyệt đối -> giữ nguyên (người dùng tự chọn).
    Tương đối (mặc định "2. Report") -> đặt CẠNH APP cho dễ tìm; chỉ khi thư mục cài
    chỉ-đọc (hiếm: cài quyền admin vào Program Files thật) mới lui về thư mục dữ liệu."""
    p = Path(raw)
    if p.is_absolute():
        return str(p)
    canh_app = thu_muc_cai_dat() / raw
    if not _dong_goi() or _ghi_duoc(canh_app):
        return str(canh_app)
    return str(thu_muc_du_lieu() / raw)


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
