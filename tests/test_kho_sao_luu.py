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
    a = KhoChotSo(str(tmp_path / "kho.sqlite")); _luu(a, chi_nhanh="A01", van_tay_hash="h1"); a.dong()
    ng = KhoChotSo(str(tmp_path / "nguon.sqlite"))
    _luu(ng, chi_nhanh="A01", van_tay_hash="h1")   # trùng
    _luu(ng, chi_nhanh="B02", van_tay_hash="h9")   # mới
    ng.dong()
    kq = sl.nhap_gop(str(tmp_path / "kho.sqlite"), str(tmp_path / "nguon.sqlite"))
    assert kq["da_them"] == 1 and kq["bo_qua_trung"] == 1
    kho = KhoChotSo(str(tmp_path / "kho.sqlite"))
    assert kho.doc_hieu_luc(2026, 8, "B02") is not None
    kho.dong()
