"""Repository kho chốt sổ: mọi thao tác đọc/ghi SQLite gói ở đây."""
from __future__ import annotations

import gzip
from datetime import datetime

import pandas as pd

from . import quy_doi as _quy_doi
from .ket_noi import mo_kho


def _nen(df: pd.DataFrame) -> bytes:
    # orient="table" nhúng schema (dtype) → read lại KHÔNG trôi kiểu: chuỗi "0001"
    # vẫn là "0001" (không mất số 0 đầu), float không bị ép thành int. Nhờ vậy vân
    # tay/diff ổn định qua lưu/đọc mà chuoi_dong không phải coerce lossy.
    return gzip.compress(df.to_json(orient="table", index=False).encode("utf-8"))


def _giai_nen(blob: bytes) -> pd.DataFrame:
    import io
    df = pd.read_json(io.StringIO(gzip.decompress(blob).decode("utf-8")), orient="table")
    return df.reset_index(drop=True)


class KhoChotSo:
    def __init__(self, path: str):
        self.path = path
        self.con = mo_kho(path)

    def dong(self):
        self.con.close()

    def luu_snapshot(self, *, ky_nam, ky_thang, chi_nhanh, van_tay_hash, so_dong,
                     tong_ps, ket_luan_ma, dem, checks, df, ghi_chu="") -> int:
        with self.con:  # transaction
            self.con.execute(
                "UPDATE snapshot SET con_hieu_luc=0 WHERE ky_nam=? AND ky_thang=? AND chi_nhanh=? AND con_hieu_luc=1",
                (ky_nam, ky_thang, chi_nhanh))
            cur = self.con.execute(
                """INSERT INTO snapshot (ky_nam, ky_thang, chi_nhanh, thoi_diem_chot, ghi_chu,
                     so_dong, tong_ps, van_tay, ket_luan_ma, so_do, so_vang, so_chua_lam, so_can_ra, con_hieu_luc)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1)""",
                (ky_nam, ky_thang, chi_nhanh, datetime.now().isoformat(timespec="seconds"), ghi_chu,
                 so_dong, tong_ps, van_tay_hash, ket_luan_ma,
                 dem.get("so_do", 0), dem.get("so_vang", 0), dem.get("so_chua_lam", 0), dem.get("so_can_ra", 0)))
            sid = int(cur.lastrowid)
            self.con.executemany(
                "INSERT INTO snapshot_check (snapshot_id, ma, ten, muc_do, so_loi, la_thong_ke) VALUES (?,?,?,?,?,?)",
                [(sid, c["ma"], c["ten"], c["muc_do"], int(c["so_loi"]), int(bool(c["la_thong_ke"]))) for c in checks])
            self.con.execute("INSERT INTO snapshot_du_lieu (snapshot_id, du_lieu) VALUES (?,?)", (sid, _nen(df)))
        return sid

    def doc_hieu_luc(self, ky_nam, ky_thang, chi_nhanh) -> dict | None:
        r = self.con.execute(
            "SELECT * FROM snapshot WHERE ky_nam=? AND ky_thang=? AND chi_nhanh=? AND con_hieu_luc=1",
            (ky_nam, ky_thang, chi_nhanh)).fetchone()
        return dict(r) if r else None

    def doc_du_lieu(self, snapshot_id) -> pd.DataFrame:
        r = self.con.execute("SELECT du_lieu FROM snapshot_du_lieu WHERE snapshot_id=?", (snapshot_id,)).fetchone()
        return _giai_nen(r[0]) if r else pd.DataFrame()

    def liet_ke(self, chi_nhanh=None, ky_nam=None, ky_thang=None) -> list[dict]:
        dk, tham = [], []
        if chi_nhanh: dk.append("chi_nhanh=?"); tham.append(chi_nhanh)
        if ky_nam: dk.append("ky_nam=?"); tham.append(ky_nam)
        if ky_thang: dk.append("ky_thang=?"); tham.append(ky_thang)
        sql = "SELECT * FROM snapshot"
        if dk: sql += " WHERE " + " AND ".join(dk)
        sql += " ORDER BY ky_nam DESC, ky_thang DESC, chi_nhanh, thoi_diem_chot DESC"
        return [dict(r) for r in self.con.execute(sql, tham)]

    def mo_lai(self, ky_nam, ky_thang, chi_nhanh) -> bool:
        with self.con:
            cur = self.con.execute(
                "UPDATE snapshot SET con_hieu_luc=0 WHERE ky_nam=? AND ky_thang=? AND chi_nhanh=? AND con_hieu_luc=1",
                (ky_nam, ky_thang, chi_nhanh))
        return cur.rowcount > 0

    def dem_ky_hieu_luc(self) -> int:
        return int(self.con.execute("SELECT COUNT(*) FROM snapshot WHERE con_hieu_luc=1").fetchone()[0])

    # ---- quy đổi mã chi nhánh -> tên hiển thị (bảng phụ, không thuộc dữ liệu chốt) ----
    def doc_quy_doi(self) -> dict:
        return _quy_doi.doc(self.con)

    def ghi_quy_doi(self, m: dict) -> None:
        _quy_doi.ghi_toan_bo(self.con, m)
