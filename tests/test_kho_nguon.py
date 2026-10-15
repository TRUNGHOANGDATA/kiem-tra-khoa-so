import sqlite3

from app.kho import BANG_KE, SO_BAN_HANG, KhoChotSo, sao_luu
from app.kho.schema import PHIEN_BAN_SCHEMA
from tests.conftest import tao_df, tao_sbh


def _kho(tmp_path, ten="k.sqlite"):
    return KhoChotSo(str(tmp_path / ten))


def _snap(kho, cn="A01"):
    return kho.luu_snapshot(ky_nam=2026, ky_thang=8, chi_nhanh=cn, van_tay_hash="h", so_dong=1,
                            tong_ps=1.0, ket_luan_ma="san_sang", dem={}, checks=[], df=tao_df([{}]))


def test_luu_doc_nguon_khong_troi_kieu(tmp_path):
    kho = _kho(tmp_path)
    df = tao_sbh([{"DocNo": "0051998"}])
    assert kho.luu_nguon(SO_BAN_HANG, "A01", 2026, 8, df, "f.xlsx", "2026-08-31T10:00:00") == "moi"
    ra = kho.doc_nguon(SO_BAN_HANG, "A01", 2026, 8)
    assert ra.loc[0, "DocNo"] == "0051998" and ra["Amount3"].dtype == float
    assert kho.doc_nguon(BANG_KE, "A01", 2026, 8) is None          # loại khác = chưa nạp
    assert kho.co_nguon(SO_BAN_HANG, "A01", 2026, 8)
    kho.dong()


def test_nap_lai_y_het_chi_cham_thoi_diem(tmp_path):
    kho = _kho(tmp_path)
    df = tao_df([{}])
    kho.luu_nguon(BANG_KE, "A01", 2026, 8, df, thoi_diem="2026-09-01T00:00:00")
    assert kho.luu_nguon(BANG_KE, "A01", 2026, 8, df, thoi_diem="2026-09-02T00:00:00") == "giong"
    assert kho.trang_thai_nguon(BANG_KE)[0]["thoi_diem_nap"] == "2026-09-02T00:00:00"
    assert kho.luu_nguon(BANG_KE, "A01", 2026, 8, tao_df([{"Amount": 5}])) == "doi"
    assert kho.doc_nguon(BANG_KE, "A01", 2026, 8).loc[0, "Amount"] == 5
    kho.dong()


def test_chot_so_dong_bang_so_ban_hang(tmp_path):
    kho = _kho(tmp_path)
    sid0 = _snap(kho)
    assert kho.doc_so_ban_hang_snapshot(sid0).empty               # chốt khi chưa nạp: rỗng
    kho.luu_nguon(SO_BAN_HANG, "A01", 2026, 8, tao_sbh([{"Amount3": 0}]))
    sid = _snap(kho)
    kho.luu_nguon(SO_BAN_HANG, "A01", 2026, 8, tao_sbh([{"Amount3": 123}]))   # sửa sau chốt
    assert kho.doc_so_ban_hang_snapshot(sid).loc[0, "Amount3"] == 0
    kho.dong()


def test_kho_v4_cu_len_v5_khong_mat_gi(tmp_path):
    p = str(tmp_path / "cu.sqlite")
    kho = KhoChotSo(p); sid = _snap(kho); kho.dong()
    con = sqlite3.connect(p)
    con.execute("UPDATE schema_version SET phien_ban = 4")
    con.execute("DROP TABLE nguon"); con.execute("DROP TABLE snapshot_so_ban_hang")
    con.commit(); con.close()
    kho = KhoChotSo(p)
    assert kho.doc_hieu_luc(2026, 8, "A01")["id"] == sid
    assert kho.doc_so_ban_hang_snapshot(sid).empty and kho.trang_thai_nguon(BANG_KE) == []
    assert kho.con.execute("SELECT phien_ban FROM schema_version").fetchone()[0] == PHIEN_BAN_SCHEMA
    kho.dong()


def test_nhap_gop_mang_theo_so_ban_hang_dong_bang(tmp_path):
    nguon = _kho(tmp_path, "nguon.sqlite")
    nguon.luu_nguon(SO_BAN_HANG, "A01", 2026, 8, tao_sbh([{"Amount3": 0}]))
    _snap(nguon); nguon.dong()
    sao_luu.nhap_gop(str(tmp_path / "dich.sqlite"), str(tmp_path / "nguon.sqlite"))
    dich = _kho(tmp_path, "dich.sqlite")
    h = dich.doc_hieu_luc(2026, 8, "A01")
    assert len(dich.doc_so_ban_hang_snapshot(h["id"])) == 1
    dich.dong()


def test_tom_tat_kho_dem_nguon(tmp_path):
    kho = _kho(tmp_path)
    kho.luu_nguon(BANG_KE, "A01", 2026, 8, tao_df([{}]))
    kho.luu_nguon(SO_BAN_HANG, "A01", 2026, 8, tao_sbh([{}]))
    kho.luu_nguon(SO_BAN_HANG, "A02", 2026, 8, tao_sbh([{}]))
    _snap(kho); kho.dong()
    t = sao_luu.tom_tat_kho(str(tmp_path / "k.sqlite"))
    assert t["so_ky_bang_ke"] == 1 and t["so_ky_so_ban_hang"] == 2
