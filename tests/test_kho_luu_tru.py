import pandas as pd
from app.kho.luu_tru import KhoChotSo

def _kho(tmp_path): return KhoChotSo(str(tmp_path / "kho.sqlite"))
DF = pd.DataFrame([{"DocCode": "PX", "DocNo": "1", "Amount": 100.0}])
CHECKS = [{"ma": "C1.1", "ten": "x", "muc_do": "vang", "so_loi": 0, "la_thong_ke": False}]

def _luu(kho, **ghi):
    args = dict(ky_nam=2026, ky_thang=8, chi_nhanh="A01", van_tay_hash="h1",
                so_dong=1, tong_ps=100.0, ket_luan_ma="SAN_SANG",
                dem={"so_do":0,"so_vang":0,"so_chua_lam":0,"so_can_ra":0},
                checks=CHECKS, df=DF, ghi_chu="")
    args.update(ghi)
    return kho.luu_snapshot(**args)

def test_luu_va_doc_hieu_luc(tmp_path):
    kho = _kho(tmp_path)
    try:
        sid = _luu(kho)
        h = kho.doc_hieu_luc(2026, 8, "A01")
        assert h["id"] == sid and h["van_tay"] == "h1" and h["ket_luan_ma"] == "SAN_SANG"
    finally:
        kho.dong()

def test_du_lieu_round_trip(tmp_path):
    kho = _kho(tmp_path)
    try:
        sid = _luu(kho)
        lai = kho.doc_du_lieu(sid)
        assert list(lai["DocNo"]) == ["1"] and float(lai["Amount"].iloc[0]) == 100.0
    finally:
        kho.dong()

def test_du_lieu_round_trip_giu_nguyen_kieu(tmp_path):
    # orient="table" nhúng schema → chuỗi số 0 đầu ("0001") không rụng, float không bị ép int.
    df = pd.DataFrame([{"DocCode": "PX", "DocNo": "0001", "Amount": 123.45}])
    kho = _kho(tmp_path)
    try:
        sid = _luu(kho, df=df)
        lai = kho.doc_du_lieu(sid)
        assert lai["DocNo"].iloc[0] == "0001"
        assert float(lai["Amount"].iloc[0]) == 123.45
    finally:
        kho.dong()

def test_chot_lai_append_only(tmp_path):
    kho = _kho(tmp_path)
    try:
        sid1 = _luu(kho, van_tay_hash="h1", ghi_chu="lan 1")
        sid2 = _luu(kho, van_tay_hash="h2", ghi_chu="lan 2")
        assert sid2 != sid1
        assert kho.doc_hieu_luc(2026, 8, "A01")["id"] == sid2       # bản mới hiệu lực
        assert len(kho.liet_ke()) == 2                              # bản cũ vẫn còn
        assert kho.dem_ky_hieu_luc() == 1                           # nhưng chỉ 1 hiệu lực
    finally:
        kho.dong()

def test_mo_lai(tmp_path):
    kho = _kho(tmp_path)
    try:
        _luu(kho)
        assert kho.mo_lai(2026, 8, "A01") is True
        assert kho.doc_hieu_luc(2026, 8, "A01") is None             # không còn bản hiệu lực
        assert len(kho.liet_ke()) == 1                              # nhưng lịch sử vẫn giữ
    finally:
        kho.dong()
