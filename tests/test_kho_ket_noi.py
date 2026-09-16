import sqlite3
from pathlib import Path
import pytest
from app.kho import ket_noi
from app.kho.schema import PHIEN_BAN_SCHEMA

def test_mo_kho_tao_file_va_bang(tmp_path):
    p = tmp_path / "3. Chot so" / "kho.sqlite"
    con = ket_noi.mo_kho(str(p))
    ten = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"snapshot", "snapshot_check", "snapshot_du_lieu", "schema_version"} <= ten
    assert con.execute("SELECT phien_ban FROM schema_version").fetchone()[0] == PHIEN_BAN_SCHEMA
    assert p.exists()
    con.close()

def test_mo_kho_tu_choi_phien_ban_moi_hon(tmp_path):
    p = tmp_path / "kho.sqlite"
    con = ket_noi.mo_kho(str(p)); con.execute(
        "UPDATE schema_version SET phien_ban = ?", (PHIEN_BAN_SCHEMA + 1,)); con.commit(); con.close()
    with pytest.raises(ket_noi.PhienBanMoiHon):
        ket_noi.mo_kho(str(p))
