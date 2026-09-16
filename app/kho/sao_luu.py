"""Sao lưu / phục hồi / nhập-gộp kho — đều thao tác trên một file .sqlite."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from .ket_noi import mo_kho


def _ten_backup(thu_muc: str) -> str:
    Path(thu_muc).mkdir(parents=True, exist_ok=True)
    return str(Path(thu_muc) / f"kho_{datetime.now():%Y%m%d-%H%M%S}.sqlite")


def sao_luu(path_kho: str, thu_muc_backup: str) -> str:
    """Chép kho ra file có dấu thời gian bằng backup API (an toàn cả khi đang mở)."""
    dich = _ten_backup(thu_muc_backup)
    nguon = sqlite3.connect(path_kho); ra = sqlite3.connect(dich)
    with ra:
        nguon.backup(ra)
    nguon.close(); ra.close()
    return dich


def phuc_hoi(path_kho: str, path_nguon: str, thu_muc_backup: str) -> str:
    """Kiểm nguồn hợp lệ → sao lưu kho hiện tại → thay bằng nguồn. Trả đường dẫn backup."""
    from . import ket_noi
    if not ket_noi.la_kho(path_nguon):
        raise ket_noi.KhongPhaiKho("File được chọn không phải kho chốt sổ (.sqlite thiếu bảng chuẩn)")
    mo_kho(path_nguon).close()                     # ném PhienBanMoiHon nếu nguồn mới hơn
    bk = sao_luu(path_kho, thu_muc_backup) if Path(path_kho).exists() else ""
    ra = sqlite3.connect(path_kho); ng = sqlite3.connect(path_nguon)
    with ra:
        ng.backup(ra)                              # ghi đè kho bằng nội dung nguồn
    ra.close(); ng.close()
    return bk


def tom_tat_kho(path_nguon: str) -> dict:
    """Tóm tắt nội dung một file kho — CHỈ ĐỌC, để xem trước khi phục hồi/nhập-gộp.

    Không dùng mo_kho (tránh chạm/tạo bảng lên file người dùng chọn): đọc thẳng
    bảng snapshot. Trả số bản chốt, số bản còn hiệu lực, số kỳ, số chi nhánh và
    khoảng kỳ (kỳ đầu → kỳ cuối) để hộp xác nhận hiện cho người dùng đối chiếu.
    """
    from . import ket_noi
    if not ket_noi.la_kho(path_nguon):
        raise ket_noi.KhongPhaiKho("File được chọn không phải kho chốt sổ (.sqlite thiếu bảng chuẩn)")
    con = sqlite3.connect(path_nguon)
    con.row_factory = sqlite3.Row
    try:
        r = con.execute(
            "SELECT COUNT(*) so_ban, COALESCE(SUM(con_hieu_luc),0) so_hieu_luc, "
            "COUNT(DISTINCT ky_nam*100+ky_thang) so_ky, COUNT(DISTINCT chi_nhanh) so_cn, "
            "MIN(ky_nam*100+ky_thang) ky_min, MAX(ky_nam*100+ky_thang) ky_max FROM snapshot"
        ).fetchone()
    finally:
        con.close()

    def _ky(v: int | None) -> str:
        return f"{v % 100:02d}/{v // 100}" if v else ""

    return {"so_ban": int(r["so_ban"] or 0), "so_ban_hieu_luc": int(r["so_hieu_luc"] or 0),
            "so_ky": int(r["so_ky"] or 0), "so_chi_nhanh": int(r["so_cn"] or 0),
            "ky_dau": _ky(r["ky_min"]), "ky_cuoi": _ky(r["ky_max"])}


def nhap_gop(path_kho: str, path_nguon: str) -> dict:
    """Gộp snapshot chưa trùng từ nguồn vào kho; tính lại con_hieu_luc mỗi (kỳ,chi nhánh)."""
    dich = mo_kho(path_kho); ng = mo_kho(path_nguon)
    da_them = bo_qua = 0
    cham = set()
    try:
        with dich:
            for s in ng.execute("SELECT * FROM snapshot ORDER BY id"):
                trung = dich.execute(
                    "SELECT 1 FROM snapshot WHERE ky_nam=? AND ky_thang=? AND chi_nhanh=? "
                    "AND thoi_diem_chot=? AND van_tay=?",
                    (s["ky_nam"], s["ky_thang"], s["chi_nhanh"], s["thoi_diem_chot"], s["van_tay"])).fetchone()
                if trung:
                    bo_qua += 1; continue
                cur = dich.execute(
                    """INSERT INTO snapshot (ky_nam,ky_thang,chi_nhanh,thoi_diem_chot,ghi_chu,so_dong,
                         tong_ps,van_tay,ket_luan_ma,so_do,so_vang,so_chua_lam,so_can_ra,con_hieu_luc)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,0)""",
                    (s["ky_nam"], s["ky_thang"], s["chi_nhanh"], s["thoi_diem_chot"], s["ghi_chu"],
                     s["so_dong"], s["tong_ps"], s["van_tay"], s["ket_luan_ma"],
                     s["so_do"], s["so_vang"], s["so_chua_lam"], s["so_can_ra"]))
                moi = int(cur.lastrowid)
                for c in ng.execute("SELECT * FROM snapshot_check WHERE snapshot_id=?", (s["id"],)):
                    dich.execute("INSERT INTO snapshot_check (snapshot_id,ma,ten,muc_do,so_loi,la_thong_ke) VALUES (?,?,?,?,?,?)",
                                 (moi, c["ma"], c["ten"], c["muc_do"], c["so_loi"], c["la_thong_ke"]))
                d = ng.execute("SELECT du_lieu FROM snapshot_du_lieu WHERE snapshot_id=?", (s["id"],)).fetchone()
                if d:
                    dich.execute("INSERT INTO snapshot_du_lieu (snapshot_id,du_lieu) VALUES (?,?)", (moi, d[0]))
                da_them += 1
                cham.add((s["ky_nam"], s["ky_thang"], s["chi_nhanh"]))
            # Tính lại hiệu lực cho mỗi (kỳ,chi nhánh) bị chạm: bản thoi_diem_chot mới nhất = 1
            for ky_nam, ky_thang, cn in cham:
                dich.execute("UPDATE snapshot SET con_hieu_luc=0 WHERE ky_nam=? AND ky_thang=? AND chi_nhanh=?",
                             (ky_nam, ky_thang, cn))
                r = dich.execute(
                    "SELECT id FROM snapshot WHERE ky_nam=? AND ky_thang=? AND chi_nhanh=? "
                    "ORDER BY thoi_diem_chot DESC, id DESC LIMIT 1", (ky_nam, ky_thang, cn)).fetchone()
                if r:
                    dich.execute("UPDATE snapshot SET con_hieu_luc=1 WHERE id=?", (r["id"],))
    finally:
        dich.close(); ng.close()
    return {"da_them": da_them, "bo_qua_trung": bo_qua}
