"""1.3.1 — file gộp A00/C00/T00, Id cùng kiểu, vân tay không phụ thuộc file chứa, A99/T99.

Đi ĐƯỜNG THẬT: ghi Excel -> loader / api -> kho (ép tmp_path qua conftest) -> đọc lại. Dựng
frame cùng kiểu trong bộ nhớ thì lỗi "Id chuỗi vs Id số" (đo thật: khớp 0/165) không lộ.
"""
import os
import time

import pandas as pd

from app import chot_so
from app.api import JsApi
from app.kho import SO_BAN_HANG
from app.loader import doc_nhieu_bang_ke
from tests.conftest import MAC_DINH_SBH, tao_df

BAN = {"DocCode": "HD", "DebitAccount": "1311", "CreditAccount": "51111", "Amount": 1_000_000.0}


def _bk(tmp_path, ten, rows):
    """Bảng kê .xlsx — mỗi dòng nêu BranchCode, Id và cột khác mặc định."""
    p = tmp_path / ten
    tao_df(rows).assign(**{"Id": [r.get("Id") for r in rows],
                           "WarehouseId": [r.get("WarehouseId") for r in rows]}).to_excel(p, index=False)
    return str(p)


def _sbh(thu_muc, ten, rows):
    thu_muc.mkdir(exist_ok=True)
    pd.DataFrame([{**MAC_DINH_SBH, **r} for r in rows]).to_excel(thu_muc / ten, sheet_name="Table1", index=False)
    return thu_muc / ten


def _cn(ds):
    return [(tt.chi_nhanh, tt.ky, tt.so_dong) for _, tt in ds]


# --------------------------------------------------------------- bảng kê chồng nhau
def test_bang_ke_a00_va_t00_giong_nhau_khong_nhan_doi(tmp_path):
    a01 = [{"BranchCode": "A01", "Id": 1, "DocNo": "1"}, {"BranchCode": "A01", "Id": 2, "DocNo": "2"}]
    a00 = _bk(tmp_path, "Bang ke 082026 A00.xlsx", a01)
    t00 = _bk(tmp_path, "Bang ke 082026 T00.xlsx", a01 + [{"BranchCode": "C01", "Id": 3, "DocNo": "3"}])
    bao = []
    ds = doc_nhieu_bang_ke([a00, t00], bao=bao)
    assert _cn(ds) == [("A01", "08/2026", 2), ("C01", "08/2026", 1)]
    assert any("giống hệt" in b for b in bao)
    assert ds[0][1].cac_file == ["Bang ke 082026 A00.xlsx"]       # nguồn dựng SAU khi chọn


def test_bang_ke_trung_id_khac_noi_dung_thi_dung_khay_do(tmp_path):
    a00 = _bk(tmp_path, "A00.xlsx", [{"BranchCode": "A01", "Id": 1, "Amount": 100.0}])
    t00 = _bk(tmp_path, "T00.xlsx", [{"BranchCode": "A01", "Id": 1, "Amount": 999.0},
                                     {"BranchCode": "C01", "Id": 3}])
    bao = []
    ds = doc_nhieu_bang_ke([a00, t00], bao=bao)
    assert _cn(ds) == [("C01", "08/2026", 1)]                     # A01 KHÔNG được đoán
    dung = [b for b in bao if b.startswith("✕")]
    assert len(dung) == 1 and "A00.xlsx" in dung[0] and "T00.xlsx" in dung[0]


def test_mot_khay_hai_file_khong_trung_id_thi_cong_du(tmp_path):
    a = _bk(tmp_path, "a.xlsx", [{"BranchCode": "A01", "Id": 1, "Amount": 100.0}])
    b = _bk(tmp_path, "b.xlsx", [{"BranchCode": "A01", "Id": 2, "Amount": 250.0}])
    ds = doc_nhieu_bang_ke([a, b])
    assert _cn(ds) == [("A01", "08/2026", 2)] and ds[0][1].tong_ps == 350.0


def test_cung_khay_hai_thang_la_hai_don_vi(tmp_path):
    a = _bk(tmp_path, "t7.xlsx", [{"BranchCode": "A01", "Id": 1, "DocDate": "2026-07-10"}])
    b = _bk(tmp_path, "t8.xlsx", [{"BranchCode": "A01", "Id": 2}])
    assert _cn(doc_nhieu_bang_ke([a, b])) == [("A01", "07/2026", 1), ("A01", "08/2026", 1)]


def test_bo_qua_a99_t99_khong_thanh_khay_khong_chan_kiem_tra(tmp_path):
    p = _bk(tmp_path, "T00.xlsx", [{"BranchCode": "A01", "Id": 1}, {"BranchCode": "A99", "Id": 2},
                                   {"BranchCode": "T99", "Id": 3}, {"BranchCode": "T99", "Id": 4}])
    api = JsApi()
    r = api.nap_nhieu_file([p])
    assert [d["ma"] for d in r["don_vi"]] == ["A01"]
    assert any("1 dòng A99" in b and "2 dòng T99" in b for b in r["bao_nap"])
    assert [x["chi_nhanh"] for x in api.thieu_cdps()] == ["A01"]   # A99/T99 không đòi CĐPS


# ------------------------------------------------------------ vân tay & chốt sổ
def test_van_tay_khay_tu_file_rieng_va_file_gop_khop(tmp_path):
    """Cột int ở file riêng thành float ở file gộp (khay khác có ô trống) — cùng dữ liệu
    phải cùng vân tay, không thì bản đã chốt báo LỆCH giả."""
    a01 = [{"BranchCode": "A01", "Id": 1, "WarehouseId": 5}, {"BranchCode": "A01", "Id": 2, "WarehouseId": 7}]
    rieng = doc_nhieu_bang_ke([_bk(tmp_path, "A01.xlsx", a01)])[0][0]
    gop = doc_nhieu_bang_ke([_bk(tmp_path, "A00.xlsx", a01 + [{"BranchCode": "A02", "Id": 3}])])[0][0]
    assert str(rieng["WarehouseId"].dtype) != str(gop["WarehouseId"].dtype)   # đúng là khác kiểu
    assert chot_so.van_tay(rieng).ma_bam == chot_so.van_tay(gop).ma_bam


def test_ban_chot_mang_hash_luat_cu_du_lieu_khong_doi_van_khop():
    df = tao_df([{"Amount": 100.0}]).assign(WarehouseId=[5])
    vt_cu = chot_so.VanTay(1, 100.0, "hash-theo-luat-canonical-cu")
    assert chot_so.doi_chieu(vt_cu, df, df_chot=df).trang_thai == chot_so.KHOP
    doi = df.assign(Amount=[200.0])
    assert chot_so.doi_chieu(vt_cu, doi, df_chot=df).trang_thai == chot_so.LECH


# ---------------------------------------------------------------- sổ bán hàng gộp
def _nap_bk(api, tmp_path, rows, ten="Bang ke 082026 A00.xlsx"):
    r = api.nap_nhieu_file([_bk(tmp_path, ten, rows)])
    assert "loi" not in r, r
    return r


def test_so_gop_chua_co_bang_ke_thi_tu_choi(tmp_path):
    _sbh(tmp_path / "s", "So chi tiet ban hang T00 082026.xlsx", [{"Id": 1}])
    r = JsApi().nap_so_ban_hang_thu_muc(str(tmp_path / "s"))
    assert r["nap"] == [] and "nạp bảng kê kỳ 08/2026 trước" in r["bo_qua"][0]["ly_do"]


def test_so_gop_tach_dung_khay_du_trung_docno_va_bao_dong_khong_khop(tmp_path):
    api = JsApi()
    _nap_bk(api, tmp_path, [{**BAN, "BranchCode": "A01", "Id": 11, "DocNo": "0001"},
                            {**BAN, "BranchCode": "C01", "Id": 22, "DocNo": "0001"}])
    _sbh(tmp_path / "s", "So chi tiet ban hang T00 082026.xlsx",
         [{"Id": 11, "DocNo": "0001"}, {"Id": 22, "DocNo": "0001", "Amount3": 0},
          {"Id": 99, "DocNo": "0009"}])
    r = api.nap_so_ban_hang_thu_muc(str(tmp_path / "s"))
    assert sorted((x["chi_nhanh"], x["so_dong"], x["tu_gop"]) for x in r["nap"]) == [("A01", 1, "T00"), ("C01", 1, "T00")]
    assert r["khong_khop"] == [{"file": "So chi tiet ban hang T00 082026.xlsx", "ky": "08/2026",
                                "so_dong": 1, "so_ct": 1}]
    assert api.thieu_so_ban_hang() == []
    kho = api._kho()
    try:
        assert kho.doc_nguon(SO_BAN_HANG, "C01", 2026, 8)["Amount3"].tolist() == [0.0]
    finally:
        kho.dong()


def test_so_a00_roi_t00_giong_nhau_thi_giong(tmp_path):
    api = JsApi()
    _nap_bk(api, tmp_path, [{**BAN, "BranchCode": "A01", "Id": 11}])
    _sbh(tmp_path / "s1", "So chi tiet ban hang A00 082026.xlsx", [{"Id": 11}])
    _sbh(tmp_path / "s2", "So chi tiet ban hang T00 082026.xlsx", [{"Id": 11}])
    assert api.nap_so_ban_hang_thu_muc(str(tmp_path / "s1"))["nap"][0]["ket_qua"] == "moi"
    assert api.nap_so_ban_hang_thu_muc(str(tmp_path / "s2"))["nap"][0]["ket_qua"] == "giong"


def test_so_cu_hon_ban_trong_kho_ma_khac_thi_khong_de(tmp_path):
    api = JsApi()
    _nap_bk(api, tmp_path, [{**BAN, "BranchCode": "A01", "Id": 11}])
    moi = _sbh(tmp_path / "moi", "So chi tiet ban hang A00 082026.xlsx", [{"Id": 11, "Amount3": 80_000}])
    cu = _sbh(tmp_path / "cu", "So chi tiet ban hang T00 082026.xlsx", [{"Id": 11, "Amount3": 0}])
    gio = time.time()
    os.utime(cu, (gio - 3600, gio - 3600))
    os.utime(moi, (gio, gio))
    api.nap_so_ban_hang_thu_muc(str(tmp_path / "moi"))
    r = api.nap_so_ban_hang_thu_muc(str(tmp_path / "cu"))
    assert r["nap"][0]["ket_qua"] == "cu_hon"
    kho = api._kho()
    try:
        assert kho.doc_nguon(SO_BAN_HANG, "A01", 2026, 8)["Amount3"].tolist() == [80_000.0]
    finally:
        kho.dong()


def test_cung_thu_muc_file_moi_nhat_thang(tmp_path):
    """Trước 1.3.1 duyệt mới->cũ nên file CŨ NHẤT đè cuối cùng và thắng."""
    api = JsApi()
    _nap_bk(api, tmp_path, [{**BAN, "BranchCode": "A01", "Id": 11}])
    tm = tmp_path / "s"
    cu = _sbh(tm, "So chi tiet ban hang A01 082026 ban cu.xlsx", [{"Id": 11, "Amount3": 0}])
    moi = _sbh(tm, "So chi tiet ban hang A01 082026 ban moi.xlsx", [{"Id": 11, "Amount3": 80_000}])
    gio = time.time()
    os.utime(cu, (gio - 3600, gio - 3600))
    os.utime(moi, (gio, gio))
    api.nap_so_ban_hang_thu_muc(str(tm))
    kho = api._kho()
    try:
        assert kho.doc_nguon(SO_BAN_HANG, "A01", 2026, 8)["Amount3"].tolist() == [80_000.0]
    finally:
        kho.dong()


def test_c32_so_khong_phu_du_thi_khong_noi_dat(tmp_path):
    api = JsApi()
    p = _bk(tmp_path, "Bang ke 082026 A00.xlsx", [{**BAN, "BranchCode": "A01", "Id": 11, "DocNo": "1"},
                                                   {**BAN, "BranchCode": "A01", "Id": 12, "DocNo": "2"}])
    api.nap_nhieu_file([p])
    _sbh(tmp_path / "s", "So chi tiet ban hang A00 082026.xlsx", [{"Id": 11}])    # thiếu Id 12
    api.nap_so_ban_hang_thu_muc(str(tmp_path / "s"))
    kq = api.chay_kiem_tra([p])
    c32 = next(c for n in kq["nhom"] for c in n["checks"] if c["ma"] == "C3.2")
    assert c32["so_loi"] == 0 and c32["la_thong_ke"] and "KHÔNG phủ đủ: thiếu 1 chứng từ" in c32["ghi_chu"]


def test_chot_khay_co_so_tach_tu_file_gop_thi_snapshot_co_so(tmp_path):
    api = JsApi()
    p = _bk(tmp_path, "Bang ke 082026 A00.xlsx", [{**BAN, "BranchCode": "A01", "Id": 11}])
    api.nap_nhieu_file([p])
    _sbh(tmp_path / "s", "So chi tiet ban hang A00 082026.xlsx", [{"Id": 11}])
    api.nap_so_ban_hang_thu_muc(str(tmp_path / "s"))
    api.chay_kiem_tra([p])
    assert "loi" not in api.chot_so("test")
    kho = api._kho()
    try:
        h = kho.doc_hieu_luc(2026, 8, "A01")
        assert len(kho.doc_so_ban_hang_snapshot(h["id"])) == 1
    finally:
        kho.dong()


# ------------------------------------------------------------------- CĐPS gộp
def test_cdps_mang_ma_gop_bi_bo_qua(tmp_path):
    tm = tmp_path / "cd"
    tm.mkdir()
    dong = {"Account": "111", "AccountName": "Tiền", "DebitBal1": 1, "CreditBal1": 0, "DebitAmount": 0,
            "CreditAmount": 0, "DebitBal2": 1, "CreditBal2": 0, "IsGroup": "False", "Level": 1}
    for ma in ("T00", "A01"):
        pd.DataFrame([dong]).to_excel(tm / f"{ma} 082026 BANG CAN DOI PHAT SINH.xlsx", sheet_name="Table1", index=False)
    api = JsApi()
    r = api.nap_cdps_thu_muc(str(tm))
    assert [x["chi_nhanh"] for x in r["nap"]] == ["A01"]
    assert any(b.startswith("T00 082026") and "cần CĐPS từng khay" in b for b in r["bo_qua"])
    assert [x["chi_nhanh"] for x in api.trang_thai_cdps()] == ["A01"]


# ------------------------------------------------------------ màn "Dữ liệu đã nạp"
def test_xem_nguon_loc_tong_phan_trang_va_nap_lai_khong_hien_khung_cu(tmp_path):
    api = JsApi()
    _nap_bk(api, tmp_path, [{**BAN, "BranchCode": "A01", "Id": 11}])
    _sbh(tmp_path / "s", "So chi tiet ban hang A01 082026.xlsx",
         [{"Id": 11}, {"Id": 11, "Amount3": 0}, {"Id": 11, "DebitAccount2": "52131", "CreditAccount2": "1311",
                                                "Amount2": -200_000.0, "Amount3": -16_000.0}])
    api.nap_so_ban_hang_thu_muc(str(tmp_path / "s"))
    r = api.xem_nguon("so_ban_hang", "A01", 2026, 8, 1, 2)
    assert r["tong"] == 3 and len(r["dong"]) == 2 and r["nhan"][r["cot"].index("Amount2")] == "Doanh thu"
    tong = {o["nhan"]: o["gia_tri"] for o in r["tong_hop"]}
    assert tong["Doanh thu (Nợ131/Có511)"] == 2_000_000 and tong["Thuế ra"] == 80_000
    assert tong["Trả lại (Nợ521/Có131)"] == -200_000
    assert api.xem_nguon("so_ban_hang", "A01", 2026, 8, chi_thue_0=True)["tong"] == 1
    assert api.xem_nguon("so_ban_hang", "A01", 2026, 8, loc_no="521")["tong"] == 1
    assert api.xem_nguon("so_ban_hang", "A01", 2026, 8, tim="15/08/2026")["tong"] == 3
    # nạp lại sổ khác -> không được hiện khung cũ trong bộ nhớ tạm
    time.sleep(1.1)
    _sbh(tmp_path / "s2", "So chi tiet ban hang A01 082026.xlsx", [{"Id": 11}])
    api.nap_so_ban_hang_thu_muc(str(tmp_path / "s2"))
    assert api.xem_nguon("so_ban_hang", "A01", 2026, 8)["tong"] == 1
    bk = api.xem_nguon("bang_ke", "A01", 2026, 8)
    assert bk["tong"] == 1 and bk["loai_ct"] == ["HD"]
    x = api.xuat_nguon("so_ban_hang", "A01", 2026, 8)
    assert "loi" not in x and os.path.exists(x["path"])
