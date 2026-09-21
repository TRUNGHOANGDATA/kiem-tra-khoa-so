"""api: nạp CĐPS theo thư mục, trạng thái đã nhập, và bơm lỗ lũy kế vào ctx (C7.6)."""
from types import SimpleNamespace

import pandas as pd

from app.api import JsApi

COT = ["Account", "AccountName", "DebitBal1", "CreditBal1", "DebitAmount",
       "CreditAmount", "DebitBal2", "CreditBal2", "IsGroup", "Level"]


def _viet(p, rows):
    pd.DataFrame(rows, columns=COT).to_excel(p, sheet_name="Table1", index=False)


def _nguon(tmp_path, rows, ten="A08 082026 CDPS.xlsx"):
    src = tmp_path / "1. Source"
    src.mkdir(exist_ok=True)
    _viet(src / ten, rows)
    return src


def test_nap_cdps_thu_muc_va_trang_thai(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    _nguon(tmp_path, [
        ["421", "LN", "2981950998", "0", "0", "1571960518", "1409990480", "0", "True", "0"],
        ["4212", "LN", "2981950998", "0", "0", "1571960518", "1409990480", "0", "False", "1"],
    ])
    api = JsApi()
    r = api.nap_cdps_thu_muc()
    assert any(x["chi_nhanh"] == "A08" for x in r["nap"])
    ts = api.trang_thai_cdps()
    assert any(x["chi_nhanh"] == "A08" and x["ky"] == "08/2026" for x in ts)


def test_nap_cdps_bo_qua_file_khong_dung_quy_uoc(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    src = _nguon(tmp_path, [["911", "x", "0", "0", "0", "0", "0", "0", "False", "0"]],
                 ten="A08 082026 CDPS.xlsx")
    _viet(src / "Bang ke chung tu 082026 A00.xlsx", [["911", "x", "0", "0", "0", "0", "0", "0", "False", "0"]])
    api = JsApi()
    r = api.nap_cdps_thu_muc()
    assert [x["chi_nhanh"] for x in r["nap"]] == ["A08"]
    assert "Bang ke chung tu 082026 A00.xlsx" in r["bo_qua"]


def test_lo_luy_ke_dau_bom_dung(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    _nguon(tmp_path, [["4212", "LN", "2981950998", "0", "0", "1571960518", "1409990480", "0", "False", "1"]])
    api = JsApi()
    api.nap_cdps_thu_muc()
    d = SimpleNamespace(nhan="A08", tt=SimpleNamespace(ky_nam=2026, ky_thang=8))
    assert api._lo_luy_ke_dau(d) == 2981950998.0
    d2 = SimpleNamespace(nhan="A07", tt=SimpleNamespace(ky_nam=2026, ky_thang=8))
    assert api._lo_luy_ke_dau(d2) is None      # chi nhánh chưa nhập -> None


def test_lo_luy_ke_dau_none_khi_chua_co_kho(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    d = SimpleNamespace(nhan="A08", tt=SimpleNamespace(ky_nam=2026, ky_thang=8))
    assert api._lo_luy_ke_dau(d) is None       # chưa có kho -> None, không tạo kho thừa


def test_thieu_cdps_liet_ke_chi_nhanh_chua_co(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    bk = tmp_path / "bk.xlsx"
    pd.DataFrame([{"DocNo": "A", "DocDate": "2026-08-01", "DebitAccount": "6214",
                   "CreditAccount": "1521", "Amount": 100}]).to_excel(bk, sheet_name="Table1", index=False)
    api._nap_nhieu([str(bk)])
    cn = api._dv[0].nhan
    assert [x["chi_nhanh"] for x in api.thieu_cdps()] == [cn]   # chưa có CĐPS -> thiếu
    kho = api._kho()
    df = pd.DataFrame([["4212", "LN", 0, 0, 0, 0, 0, 0, False, 1]],
                      columns=["account", "ten", "du_dau_no", "du_dau_co", "ps_no", "ps_co",
                               "du_cuoi_no", "du_cuoi_co", "is_group", "level"])
    kho.luu_cdps(cn, 2026, 8, df)
    kho.dong()
    assert api.thieu_cdps() == []                                # đã đủ CĐPS -> không thiếu


def test_cdps_cua_bom_vao_ctx(tmp_path, monkeypatch):
    """G9/G10/C7 cần cả bảng CĐPS, không chỉ lỗ lũy kế."""
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    d = SimpleNamespace(nhan="A08", tt=SimpleNamespace(ky_nam=2026, ky_thang=8))
    assert api._cdps_cua(d) is None                      # chưa có kho -> None
    kho = api._kho()
    df = pd.DataFrame([["1111", "Tiền mặt", 0, 0, 0, 0, 500, 0, False, 1]],
                      columns=["account", "ten", "du_dau_no", "du_dau_co", "ps_no", "ps_co",
                               "du_cuoi_no", "du_cuoi_co", "is_group", "level"])
    kho.luu_cdps("A08", 2026, 8, df)
    kho.dong()
    got = api._cdps_cua(d)
    assert got is not None and got["account"].tolist() == ["1111"]
    assert api._cdps_cua(SimpleNamespace(nhan="A07", tt=SimpleNamespace(ky_nam=2026, ky_thang=8))) is None


def test_chi_tiet_cdps(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    kho = api._kho()
    df = pd.DataFrame([["4212", "LN", 2981950998, 0, 0, 1571960518, 1409990480, 0, False, 1]],
                      columns=["account", "ten", "du_dau_no", "du_dau_co", "ps_no", "ps_co",
                               "du_cuoi_no", "du_cuoi_co", "is_group", "level"])
    kho.luu_cdps("A08", 2026, 8, df)
    kho.dong()
    r = api.chi_tiet_cdps("A08", 2026, 8)
    assert len(r["dong"]) == 1 and r["dong"][0]["account"] == "4212"
    assert r["dong"][0]["du_dau_no"] == 2981950998.0
    assert api.chi_tiet_cdps("A08", 2026, 9)["dong"] == []       # kỳ chưa có -> rỗng


def test_nap_lai_cdps_khac_thi_bao_thay_doi(tmp_path, monkeypatch):
    """Nạp lại là GHI ĐÈ SẠCH — phải báo đổi ở đâu, không được im lặng thay số."""
    monkeypatch.setattr("app.api.GOC", tmp_path)
    _nguon(tmp_path, [["911", "XDKQ", "0", "0", "100", "100", "0", "0", "False", "0"]])
    api = JsApi()
    assert api.nap_cdps_thu_muc()["thay_doi"] == []          # lần đầu: không có gì để so

    _nguon(tmp_path, [["911", "XDKQ", "0", "0", "150", "100", "0", "0", "False", "0"],
                      ["642", "CP QLDN", "0", "0", "7", "0", "0", "0", "False", "0"]])
    td = JsApi().nap_cdps_thu_muc(ghi_de=True)["thay_doi"]
    assert len(td) == 1 and td[0]["chi_nhanh"] == "A08"
    assert (td[0]["so_doi"], td[0]["so_them"], td[0]["so_bot"]) == (1, 1, 0)
    assert {d["account"] for d in td[0]["dong"]} == {"911", "642"}


# ----------------------------------------------- CĐPS kỳ liền trước bơm vào ctx
KHO_COLS = ["account", "ten", "du_dau_no", "du_dau_co", "ps_no", "ps_co",
            "du_cuoi_no", "du_cuoi_co", "is_group", "level"]


def _kho_df(rows):
    return pd.DataFrame(rows, columns=KHO_COLS)


def test_boi_canh_mac_dinh_chua_co_cdps_truoc():
    from app.checks.base import BoiCanh
    assert BoiCanh(8, 2026).cdps_truoc is None


def test_cdps_truoc_doc_ky_lien_truoc(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    d = SimpleNamespace(nhan="A08", tt=SimpleNamespace(ky_nam=2026, ky_thang=8))
    assert api._cdps_truoc(d) is None                    # chưa có kho -> None
    kho = api._kho()
    kho.luu_cdps("A08", 2026, 7, _kho_df([["1111", "Tiền mặt", 0, 0, 0, 0, 500, 0, False, 1]]))
    kho.dong()
    got = api._cdps_truoc(d)
    assert got is not None and got["account"].tolist() == ["1111"]
    # kỳ 07 chưa có kỳ 06 -> None, không được trả nhầm chính kỳ đó
    assert api._cdps_truoc(SimpleNamespace(nhan="A08", tt=SimpleNamespace(ky_nam=2026, ky_thang=7))) is None


def test_cdps_truoc_bom_vao_boi_canh(tmp_path, monkeypatch):
    """Đường ống phải nối tới BoiCanh — có ở api thôi thì check vẫn không thấy."""
    from app.api import DonVi
    from app.checks.base import BoiCanh
    from app.loader import ThongTinFile
    from tests.conftest import tao_df

    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    kho = api._kho()
    kho.luu_cdps("A01", 2026, 7, _kho_df([["1111", "Tiền mặt", 0, 0, 0, 0, 500, 0, False, 1]]))
    kho.dong()
    df = tao_df([{"DocNo": "1", "DebitAccount": "621", "CreditAccount": "1521", "Amount": 100.0}])
    d = DonVi(df=df, tt=ThongTinFile(path="x.xlsx", ten="x.xlsx", ky="08/2026", ky_thang=8,
                                     ky_nam=2026, so_dong=1, tong_ps=100.0, chi_nhanh="A01"))
    ghi = []

    def _ghi(*a, **kw):
        ctx = BoiCanh(*a, **kw)
        ghi.append(ctx)
        return ctx

    monkeypatch.setattr("app.api.BoiCanh", _ghi)
    api._chay_mot_don_vi(d)
    assert ghi[0].cdps_truoc is not None
    assert ghi[0].cdps_truoc["account"].tolist() == ["1111"]


def test_cot_so_nhan_dien_theo_kieu_du_lieu(tmp_path, monkeypatch):
    """Mọi cột SỐ phải vào `cot_so`, kể cả bảng đã đổi sang nhãn tiếng Việt.

    G9/G10/G11 dựng bảng với tên cột tiếng Việt sẵn ("Dư cuối Nợ", "PS Nợ bảng kê")
    nên danh sách tên cố định COT_SO_HIEN_THI không khớp -> số tiền hiện trần trụi
    464282494 thay vì 464.282.494, kế toán đọc không nổi.
    """
    monkeypatch.setattr("app.api.GOC", tmp_path)
    src = _nguon(tmp_path, [
        ["1111", "Tien mat", "900000000", "0", "0", "800000000", "100000000", "0", "False", "0"],
        ["6421", "CP QLDN", "0", "0", "800000000", "0", "800000000", "0", "False", "0"],
    ])
    bk = src / "Bang ke chung tu 082026 A08.xlsx"
    pd.DataFrame([{"BranchCode": "A08", "DocNo": "A", "DocDate": "2026-08-01",
                   "DebitAccount": "6421", "CreditAccount": "1111", "Amount": 800000000}]
                 ).to_excel(bk, sheet_name="Table1", index=False)
    api = JsApi()
    api.nap_cdps_thu_muc()
    api.chay_kiem_tra(str(bk))
    thieu = {}
    for ma in api._kq:
        ct = api.lay_chi_tiet(ma)
        so = set(ct["cot_so"]) | set(ct["cot_so_le"])
        for dong in ct["dong"][:5]:
            for cot, gt in dong.items():
                if isinstance(gt, (int, float)) and not isinstance(gt, bool) and cot not in so:
                    thieu.setdefault(ma, set()).add(cot)
    assert thieu == {}, f"cột số không được định dạng: {thieu}"


# ------------------- xem trước & xác nhận ghi đè (không ghi đè im lặng)
def _nap_lan_dau(tmp_path):
    _nguon(tmp_path, [["911", "XDKQ", "0", "0", "100", "100", "0", "0", "False", "0"]])
    api = JsApi()
    api.nap_cdps_thu_muc(ghi_de=True)
    return api


def test_xem_truoc_khong_ghi_gi_vao_kho(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    _nguon(tmp_path, [["911", "XDKQ", "0", "0", "100", "100", "0", "0", "False", "0"]])
    api = JsApi()
    xt = api.xem_truoc_cdps()
    assert [x["chi_nhanh"] for x in xt["moi"]] == ["A08"] and xt["trung"] == []
    assert api.trang_thai_cdps() == []          # xem trước là CHỈ ĐỌC


def test_xem_truoc_neu_da_co_thi_bao_trung_kem_khac_biet(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = _nap_lan_dau(tmp_path)
    _nguon(tmp_path, [["911", "XDKQ", "0", "0", "150", "100", "0", "0", "False", "0"]])
    xt = JsApi().xem_truoc_cdps()
    assert xt["moi"] == [] and len(xt["trung"]) == 1
    t = xt["trung"][0]
    assert t["chi_nhanh"] == "A08" and t["ky"] == "08/2026" and t["khac"] is True
    assert t["so_doi"] == 1


def test_xem_truoc_phan_biet_trung_nhung_y_het(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    _nap_lan_dau(tmp_path)
    t = JsApi().xem_truoc_cdps()["trung"][0]
    assert t["khac"] is False and t["so_doi"] == 0


def test_mac_dinh_KHONG_ghi_de_ky_da_co(tmp_path, monkeypatch):
    """Ghi đè là mất số liệu cũ — phải do người dùng chọn, không mặc định."""
    monkeypatch.setattr("app.api.GOC", tmp_path)
    _nap_lan_dau(tmp_path)
    _nguon(tmp_path, [["911", "XDKQ", "0", "0", "150", "100", "0", "0", "False", "0"]])
    api = JsApi()
    r = api.nap_cdps_thu_muc()
    assert r["nap"] == [] and [x["chi_nhanh"] for x in r["bo_qua_trung"]] == ["A08"]
    kho = api._kho()
    assert float(kho.doc_cdps("A08", 2026, 8)["ps_no"].iloc[0]) == 100.0   # giữ bản cũ
    kho.dong()


def test_ghi_de_khi_duoc_chon(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    _nap_lan_dau(tmp_path)
    _nguon(tmp_path, [["911", "XDKQ", "0", "0", "150", "100", "0", "0", "False", "0"]])
    api = JsApi()
    r = api.nap_cdps_thu_muc(ghi_de=True)
    assert [x["chi_nhanh"] for x in r["nap"]] == ["A08"] and len(r["thay_doi"]) == 1
    kho = api._kho()
    assert float(kho.doc_cdps("A08", 2026, 8)["ps_no"].iloc[0]) == 150.0
    kho.dong()


def test_xem_truoc_moi_dong_co_khoa_nhan_dang(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = _nap_lan_dau(tmp_path)
    _nguon(tmp_path, [["911", "XDKQ", "0", "0", "150", "100", "0", "0", "False", "0"]])
    t = JsApi().xem_truoc_cdps()["trung"][0]
    assert t["khoa"] == "A08|08/2026"


def test_ghi_de_chi_nhung_ky_duoc_tick(tmp_path, monkeypatch):
    """Người dùng tick 1-2 dòng, không phải toàn bộ."""
    monkeypatch.setattr("app.api.GOC", tmp_path)
    # nạp sẵn A08 và A07 kỳ 08
    for ma in ("A07", "A08"):
        _nguon(tmp_path, [["911", "x", "0", "0", "100", "100", "0", "0", "False", "0"]],
               ten=f"{ma} 082026 CDPS.xlsx")
    JsApi().nap_cdps_thu_muc(ghi_de=True)
    for ma in ("A07", "A08"):
        _nguon(tmp_path, [["911", "x", "0", "0", "150", "100", "0", "0", "False", "0"]],
               ten=f"{ma} 082026 CDPS.xlsx")
    api = JsApi()
    r = api.nap_cdps_thu_muc(ghi_de=["A08|08/2026"])       # chỉ tick A08
    assert [x["chi_nhanh"] for x in r["nap"]] == ["A08"]
    assert [x["chi_nhanh"] for x in r["bo_qua_trung"]] == ["A07"]
    kho = api._kho()
    assert float(kho.doc_cdps("A08", 2026, 8)["ps_no"].iloc[0]) == 150.0   # đè
    assert float(kho.doc_cdps("A07", 2026, 8)["ps_no"].iloc[0]) == 100.0   # giữ
    kho.dong()


def _doc_thoi_diem(api, cn, nam, thang):
    kho = api._kho()
    try:
        return kho.thoi_diem_nap_cdps(cn, nam, thang)
    finally:
        kho.dong()


def test_nap_lai_so_lieu_TRUNG_KHOP_thi_cham_dau_thoi_gian(tmp_path, monkeypatch):
    """Nạp lại để kiểm chứng mà số liệu y hệt: không ghi đè, nhưng phải ghi nhận
    "vừa đối chiếu" — nếu không, cảnh báo "CĐPS cũ hơn bảng kê" kêu oan."""
    monkeypatch.setattr("app.api.GOC", tmp_path)
    rows = [["632", "GVHB", "0", "0", "15944", "0", "0", "0", "False", "0"]]
    src = _nguon(tmp_path, rows)
    api = JsApi()
    api.nap_cdps_thu_muc(str(src))
    truoc = _doc_thoi_diem(api, "A08", 2026, 8)

    r = api.nap_cdps_thu_muc(str(src))                  # nạp lại, KHÔNG chọn đè
    assert r["nap"] == [] and len(r["bo_qua_trung"]) == 1
    assert r["bo_qua_trung"][0]["da_doi_chieu"] is True
    assert _doc_thoi_diem(api, "A08", 2026, 8) >= truoc


def test_nap_lai_so_lieu_KHAC_ma_khong_de_thi_KHONG_cham(tmp_path, monkeypatch):
    """Số liệu thật sự khác mà người dùng giữ bản cũ -> kho đúng là chưa khớp file,
    cảnh báo phải còn nguyên, không được chạm dấu thời gian."""
    monkeypatch.setattr("app.api.GOC", tmp_path)
    src = _nguon(tmp_path, [["632", "GVHB", "0", "0", "15944", "0", "0", "0", "False", "0"]])
    api = JsApi()
    api.nap_cdps_thu_muc(str(src))
    truoc = _doc_thoi_diem(api, "A08", 2026, 8)

    _nguon(tmp_path, [["632", "GVHB", "0", "0", "99999", "0", "0", "0", "False", "0"]])
    r = api.nap_cdps_thu_muc(str(src))
    assert r["nap"] == [] and not r["bo_qua_trung"][0].get("da_doi_chieu")
    assert _doc_thoi_diem(api, "A08", 2026, 8) == truoc
