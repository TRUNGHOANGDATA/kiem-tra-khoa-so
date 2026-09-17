"""Bảng quy đổi mã chi nhánh -> tên hiển thị, lưu trong chính kho chốt sổ.

Chỉ để HIỂN THỊ: mã gốc (BranchCode) vẫn là danh tính khi chốt sổ, đổi tên không
phá đối chiếu kỳ cũ. Mọi thao tác đọc/ghi bảng này gói ở đây."""
from __future__ import annotations

import sqlite3
from datetime import datetime


def _sach(m) -> dict:
    """Chỉ giữ cặp mã->tên mà cả hai đều là chuỗi khác rỗng (đã cắt khoảng trắng)."""
    sach = {}
    for k, v in (m or {}).items():
        ma, ten = str(k).strip(), str(v).strip()
        if ma and ten:
            sach[ma] = ten
    return sach


def doc(con: sqlite3.Connection) -> dict:
    return {r[0]: r[1] for r in con.execute("SELECT ma, ten FROM quy_doi_chi_nhanh ORDER BY ma")}


def xoa(con: sqlite3.Connection, ma: str) -> None:
    with con:
        con.execute("DELETE FROM quy_doi_chi_nhanh WHERE ma = ?", (str(ma).strip(),))


def ghi_toan_bo(con: sqlite3.Connection, m: dict) -> None:
    """Đặt bảng quy đổi = đúng `m`: upsert mã có tên, XÓA mã không còn trong `m`
    (nhờ vậy bỏ một hàng ở màn Cài đặt rồi Lưu là xóa hẳn trong kho)."""
    sach = _sach(m)
    now = datetime.now().isoformat(timespec="seconds")
    with con:
        if sach:
            ph = ",".join("?" * len(sach))
            con.execute(f"DELETE FROM quy_doi_chi_nhanh WHERE ma NOT IN ({ph})", list(sach))
        else:
            con.execute("DELETE FROM quy_doi_chi_nhanh")
        con.executemany(
            "INSERT INTO quy_doi_chi_nhanh (ma, ten, cap_nhat) VALUES (?,?,?) "
            "ON CONFLICT(ma) DO UPDATE SET ten=excluded.ten, cap_nhat=excluded.cap_nhat",
            [(ma, ten, now) for ma, ten in sach.items()])
