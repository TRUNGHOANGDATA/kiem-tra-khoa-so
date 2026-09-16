import shutil

import pandas as pd
from pathlib import Path
from app.kho.luu_tru import KhoChotSo
from app.kho import sao_luu as sl

DF = pd.DataFrame([{"DocCode": "PX", "DocNo": "1", "Amount": 100.0}])
def _luu(kho, **g):
    a = dict(ky_nam=2026, ky_thang=8, chi_nhanh="A01", van_tay_hash="h1", so_dong=1,
             tong_ps=100.0, ket_luan_ma="SAN_SANG",
             dem={"so_do":0,"so_vang":0,"so_chua_lam":0,"so_can_ra":0},
             checks=[], df=DF, ghi_chu=""); a.update(g)
    return kho.luu_snapshot(**a)

def test_sao_luu_tao_file_mo_lai_duoc(tmp_path):
    kho = KhoChotSo(str(tmp_path / "kho.sqlite")); _luu(kho); kho.dong()
    bk = sl.sao_luu(str(tmp_path / "kho.sqlite"), str(tmp_path / "backup"))
    assert Path(bk).exists()
    kho_bk = KhoChotSo(bk)
    assert kho_bk.dem_ky_hieu_luc() == 1  # backup mở lại được, đủ dữ liệu
    kho_bk.dong()

def test_phuc_hoi_backup_cu_roi_thay(tmp_path):
    a = KhoChotSo(str(tmp_path / "kho.sqlite")); _luu(a, chi_nhanh="A01"); a.dong()
    ng = KhoChotSo(str(tmp_path / "nguon.sqlite")); _luu(ng, chi_nhanh="B02"); ng.dong()
    sl.phuc_hoi(str(tmp_path / "kho.sqlite"), str(tmp_path / "nguon.sqlite"), str(tmp_path / "backup"))
    kho = KhoChotSo(str(tmp_path / "kho.sqlite"))
    assert kho.doc_hieu_luc(2026, 8, "B02") is not None  # đã thay bằng nguồn
    assert kho.doc_hieu_luc(2026, 8, "A01") is None
    assert any(Path(tmp_path / "backup").glob("*.sqlite"))  # có backup bản cũ
    kho.dong()

def test_nhap_gop_bo_qua_trung(tmp_path):
    # Nguồn là bản sao byte-for-byte của đích (cùng file .sqlite) → dòng A01 trong nguồn
    # có thoi_diem_chot GIỐNG HỆT đích, đảm bảo trùng khóa (ky,chi_nhanh,thoi_diem_chot,van_tay)
    # một cách tất định, không phụ thuộc việc 2 lần _luu() rơi cùng giây đồng hồ thực.
    a = KhoChotSo(str(tmp_path / "kho.sqlite")); _luu(a, chi_nhanh="A01", van_tay_hash="h1"); a.dong()
    shutil.copy2(str(tmp_path / "kho.sqlite"), str(tmp_path / "nguon.sqlite"))
    ng = KhoChotSo(str(tmp_path / "nguon.sqlite"))
    _luu(ng, chi_nhanh="B02", van_tay_hash="h9")   # mới
    ng.dong()
    kq = sl.nhap_gop(str(tmp_path / "kho.sqlite"), str(tmp_path / "nguon.sqlite"))
    assert kq["da_them"] == 1 and kq["bo_qua_trung"] == 1
    kho = KhoChotSo(str(tmp_path / "kho.sqlite"))
    assert kho.doc_hieu_luc(2026, 8, "B02") is not None
    kho.dong()

def test_phuc_hoi_tu_choi_file_khong_phai_kho(tmp_path):
    import sqlite3
    import pytest
    from app.kho.ket_noi import KhongPhaiKho
    a = KhoChotSo(str(tmp_path / "kho.sqlite")); _luu(a, chi_nhanh="A01"); a.dong()
    lac = str(tmp_path / "lac.sqlite")
    con = sqlite3.connect(lac); con.execute("CREATE TABLE t(x)"); con.commit(); con.close()
    with pytest.raises(KhongPhaiKho):
        sl.phuc_hoi(str(tmp_path / "kho.sqlite"), lac, str(tmp_path / "backup"))
    kho = KhoChotSo(str(tmp_path / "kho.sqlite"))
    try:
        assert kho.doc_hieu_luc(2026, 8, "A01") is not None   # kho cũ còn nguyên
    finally:
        kho.dong()


def test_nhap_gop_ghi_de_khi_moi_hon(tmp_path):
    # Đích đã chốt kỳ (2026/8, A01) với thoi_diem_chot CŨ → đang hiệu lực. Nguồn có bản
    # MỚI HƠN cho cùng (kỳ, chi nhánh). Sau nhập-gộp: bản mới trở thành hiệu lực, bản cũ
    # bị hạ (con_hieu_luc=0) nhưng vẫn còn trong lịch sử — không mất dữ liệu.
    # thoi_diem_chot được set tay (không dựa datetime.now() độ phân giải giây) để tất định.
    dich = KhoChotSo(str(tmp_path / "kho.sqlite"))
    sid_cu = _luu(dich, chi_nhanh="A01", van_tay_hash="h_cu")
    with dich.con:
        dich.con.execute("UPDATE snapshot SET thoi_diem_chot=? WHERE id=?",
                          ("2026-09-01T10:00:00", sid_cu))
    dich.dong()

    ng = KhoChotSo(str(tmp_path / "nguon.sqlite"))
    sid_moi = _luu(ng, chi_nhanh="A01", van_tay_hash="h_moi")
    with ng.con:
        ng.con.execute("UPDATE snapshot SET thoi_diem_chot=? WHERE id=?",
                        ("2026-09-02T10:00:00", sid_moi))
    ng.dong()

    kq = sl.nhap_gop(str(tmp_path / "kho.sqlite"), str(tmp_path / "nguon.sqlite"))
    assert kq["da_them"] == 1 and kq["bo_qua_trung"] == 0

    kho = KhoChotSo(str(tmp_path / "kho.sqlite"))
    hang = kho.doc_hieu_luc(2026, 8, "A01")
    assert hang is not None and hang["van_tay"] == "h_moi"          # bản mới đang hiệu lực
    assert len(kho.liet_ke()) == 2                                   # lịch sử giữ cả 2 bản
    assert kho.dem_ky_hieu_luc() == 1                                 # chỉ 1 bản hiệu lực
    kho.dong()
