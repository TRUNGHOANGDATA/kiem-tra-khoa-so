"""Mở/khởi tạo/migrate kho SQLite. Một file .sqlite = toàn bộ dữ liệu."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from . import schema


class PhienBanMoiHon(Exception):
    """File kho được tạo bởi bản tool mới hơn — từ chối để không làm hỏng dữ liệu."""


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
        # (migrate khi có phiên bản > 1 trong tương lai: chèn các bước ALTER ở đây)
    return con
