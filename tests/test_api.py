import json

import pandas as pd

import app.api as api_module
from app.api import JsApi
from app.checks.base import CheckResult


def _xlsx(tmp_path):
    rows = [
        {"DocNo": "A", "DocDate": "2026-08-01", "DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100, "Description": "x"},
        {"DocNo": "B", "DocDate": "2026-08-02", "DebitAccount": "154", "CreditAccount": "6214", "Amount": 100, "Description": None},
        {"DocNo": "C", "DocDate": "2026-08-03", "DebitAccount": "632111", "CreditAccount": "1551", "Amount": 70, "Description": "gv"},
    ]
    p = tmp_path / "bk.xlsx"
    pd.DataFrame(rows).to_excel(p, sheet_name="Table1", index=False)
    return str(p)


def test_chay_kiem_tra_tra_json_hop_le(tmp_path):
    api = JsApi()
    kq = api.chay_kiem_tra(_xlsx(tmp_path))
    json.dumps(kq)  # không numpy scalar
    assert kq["tomtat"]["ky"] == "08/2026" and kq["tomtat"]["so_dong"] == 3
    assert kq["tomtat"]["san_sang"] is False           # 632 chưa kết chuyển -> C5.2 đỏ
    assert len(kq["trang_thai"]) == 11 and len(kq["nhom"]) == 6
    g5 = next(n for n in kq["nhom"] if n["ma"] == "G5")
    assert g5["muc_do"] == "do"


def test_lay_chi_tiet_phan_trang_va_tim_kiem(tmp_path):
    api = JsApi()
    api.chay_kiem_tra(_xlsx(tmp_path))
    ct = api.lay_chi_tiet("C1.1")
    assert ct["tong"] == 1 and ct["dong"][0]["DocNo"] == "B" and ct["dong"][0]["DocDate"] == "02/08/2026"
    assert api.lay_chi_tiet("C1.1", tim_kiem="zzz")["tong"] == 0
    assert "TK" in api.lay_chi_tiet("C5.2")["cot"]


def test_xuat_bao_cao_va_loi_khi_chua_chay(tmp_path, monkeypatch):
    api = JsApi()
    assert "loi" in api.xuat_bao_cao()
    api.chay_kiem_tra(_xlsx(tmp_path))
    monkeypatch.setattr(api, "thu_muc_report", str(tmp_path / "out"))
    kq = api.xuat_bao_cao()
    assert kq["path"].endswith(".xlsx") and (tmp_path / "out").exists()


def test_file_khong_ton_tai_tra_loi():
    assert "loi" in JsApi().chay_kiem_tra("khong/co/file.xlsx")


def test_nap_file_hop_le_va_khong_hop_le(tmp_path):
    api = JsApi()
    kq = api.nap_file(_xlsx(tmp_path))
    assert kq["so_dong"] == 3 and kq["ky"] == "08/2026"
    assert "loi" in api.nap_file("khong/co/file.xlsx")


def test_lay_file_moi_nhat_none_khi_khong_co_file(tmp_path):
    api = JsApi()
    api.thu_muc_source = str(tmp_path)
    assert api.lay_file_moi_nhat() is None


def test_lay_file_moi_nhat_tra_ve_file_moi_nhat(tmp_path):
    api = JsApi()
    api.thu_muc_source = str(tmp_path)
    p = _xlsx(tmp_path)
    kq = api.lay_file_moi_nhat()
    assert kq["path"] == p and kq["so_dong"] == 3


class _FakeWindow:
    def __init__(self):
        self.evaluate_js_calls = []

    def evaluate_js(self, script):
        self.evaluate_js_calls.append(script)


def test_gan_window_day_tien_trinh_qua_evaluate_js(tmp_path):
    api = JsApi()
    fw = _FakeWindow()
    api.gan_window(fw)
    api.chay_kiem_tra(_xlsx(tmp_path))
    assert fw.evaluate_js_calls
    assert fw.evaluate_js_calls[-1].endswith(", 100)")


def test_chon_file_loi_dialog_tra_ve_loi():
    class _FakeWindowLoi:
        def create_file_dialog(self, *a, **kw):
            raise RuntimeError("boom")

    api = JsApi()
    api.gan_window(_FakeWindowLoi())
    kq = api.chon_file()
    assert "loi" in kq


def test_mo_file_goi_os_startfile(monkeypatch):
    calls = []
    monkeypatch.setattr(api_module.os, "startfile", lambda p: calls.append(p), raising=False)
    api = JsApi()
    assert api.mo_file("C:/mot/file.xlsx") is True
    assert calls == ["C:/mot/file.xlsx"]


def test_mo_thu_muc_goi_popen_khi_la_file(monkeypatch, tmp_path):
    p = tmp_path / "bk.xlsx"
    p.write_text("x")
    calls = []
    monkeypatch.setattr(api_module.subprocess, "Popen", lambda args: calls.append(args))
    api = JsApi()
    assert api.mo_thu_muc(str(p)) is True
    assert calls == [["explorer", "/select,", str(p)]]


def test_mo_thu_muc_goi_os_startfile_khi_la_thu_muc(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(api_module.os, "startfile", lambda p: calls.append(p), raising=False)
    api = JsApi()
    assert api.mo_thu_muc(str(tmp_path)) is True
    assert calls == [str(tmp_path)]


def test_tim_kiem_theo_ngay_hien_thi(tmp_path):
    api = JsApi()
    api.chay_kiem_tra(_xlsx(tmp_path))
    ct = api.lay_chi_tiet("C1.1", tim_kiem="02/08/2026")
    assert ct["tong"] == 1 and ct["dong"][0]["DocNo"] == "B"


def test_kich_thuoc_gioi_han_toi_da_500():
    api = JsApi()
    df = pd.DataFrame({"DocNo": [f"D{i}" for i in range(600)]})
    api._kq = {"CX": CheckResult(ma="CX", ten="t", nhom="G1", muc_do="do", chi_tiet=df)}
    ct = api.lay_chi_tiet("CX", kich_thuoc=10_000)
    assert ct["tong"] == 600 and len(ct["dong"]) == 500
    ct2 = api.lay_chi_tiet("CX", trang=2, kich_thuoc=10_000)
    assert len(ct2["dong"]) == 100
