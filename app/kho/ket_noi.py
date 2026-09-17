"""Mở/khởi tạo/migrate kho SQLite. Một file .sqlite = toàn bộ dữ liệu."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from . import schema


class PhienBanMoiHon(Exception):
    """File kho được tạo bởi bản tool mới hơn — từ chối để không làm hỏng dữ liệu."""


class KhongPhaiKho(Exception):
    """File được chọn không phải kho chốt sổ (thiếu bảng chuẩn)."""


BANG_KHO = ("snapshot", "snapshot_check", "snapshot_du_lieu", "schema_version")


def la_kho(path: str) -> bool:
    """True nếu file .sqlite đã có đủ các bảng của kho — KHÔNG tạo bảng mới (khác mo_kho)."""
    if not Path(path).exists():
        return False
    con = sqlite3.connect(path)
    try:
        ten = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    except sqlite3.DatabaseError:
        return False
    finally:
        con.close()
    return set(BANG_KHO) <= ten


def mo_kho(path: str) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    for cau in schema.DDL:
        con.execute(cau)
    hang = con.execute("SELECT phien_ban FROM schema_version").fetchone()
    if hang is None:
        con.execute("INSERT INTO schema_version (phien_ban) VALUES (?)", (schema.PHIEN_BAN_SCHEMA,))
        con.commit()
    else:
        pb = int(hang[0])
        if pb > schema.PHIEN_BAN_SCHEMA:
            con.close()
            raise PhienBanMoiHon(f"Kho phiên bản {pb} > tool {schema.PHIEN_BAN_SCHEMA}. Hãy cập nhật tool.")
        if pb < schema.PHIEN_BAN_SCHEMA:
            # Bảng mới (nếu có) đã được DDL `IF NOT EXISTS` ở trên tạo sẵn; chỉ cần
            # nâng số phiên bản. (Migrate cần ALTER dữ liệu thì chèn thêm ở đây.)
            con.execute("UPDATE schema_version SET phien_ban = ?", (schema.PHIEN_BAN_SCHEMA,))
            con.commit()
    return con
