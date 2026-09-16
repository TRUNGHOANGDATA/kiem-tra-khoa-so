"""Định nghĩa bảng kho chốt sổ + phiên bản schema (để migrate nhẹ)."""
PHIEN_BAN_SCHEMA = 1

DDL = [
    """CREATE TABLE IF NOT EXISTS snapshot (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ky_nam INTEGER NOT NULL, ky_thang INTEGER NOT NULL, chi_nhanh TEXT NOT NULL,
        thoi_diem_chot TEXT NOT NULL, ghi_chu TEXT DEFAULT '',
        so_dong INTEGER NOT NULL, tong_ps REAL NOT NULL, van_tay TEXT NOT NULL,
        ket_luan_ma TEXT NOT NULL,
        so_do INTEGER DEFAULT 0, so_vang INTEGER DEFAULT 0,
        so_chua_lam INTEGER DEFAULT 0, so_can_ra INTEGER DEFAULT 0,
        con_hieu_luc INTEGER NOT NULL DEFAULT 1
    )""",
    "CREATE INDEX IF NOT EXISTS ix_snapshot_ky ON snapshot (ky_nam, ky_thang, chi_nhanh, con_hieu_luc)",
    """CREATE TABLE IF NOT EXISTS snapshot_check (
        snapshot_id INTEGER NOT NULL REFERENCES snapshot(id),
        ma TEXT, ten TEXT, muc_do TEXT, so_loi INTEGER, la_thong_ke INTEGER
    )""",
    "CREATE INDEX IF NOT EXISTS ix_check_snap ON snapshot_check (snapshot_id)",
    """CREATE TABLE IF NOT EXISTS snapshot_du_lieu (
        snapshot_id INTEGER PRIMARY KEY REFERENCES snapshot(id),
        du_lieu BLOB NOT NULL
    )""",
    "CREATE TABLE IF NOT EXISTS schema_version (phien_ban INTEGER NOT NULL)",
]
