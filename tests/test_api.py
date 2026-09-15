import json

import pandas as pd

from app.api import JsApi


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
