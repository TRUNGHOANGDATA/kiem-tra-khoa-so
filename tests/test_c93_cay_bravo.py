"""C9.3 theo cây TK của Bravo (Id/ParentId) — kho v6 lưu cột `cha`.

Danh mục Bravo có TK con KHÁC đầu số cha: 62781/62782 khai dưới 6277 (kỳ 10/2026, mọi khay),
nên dòng 6277 của CĐPS đã gồm chúng. So theo đầu số thì báo "cha ≠ tổng con" giả.
"""
import sqlite3

import pandas as pd

from app import cdps
from app.api import JsApi
from app.checks import g9_toan_ven_cdps as g9
from app.checks import cdps_tien_ich as cd
from app.kho import KhoChotSo
from app.kho import schema

COT_FILE = ["Account", "AccountName", "DebitBal1", "CreditBal1", "DebitAmount", "CreditAmount",
            "DebitBal2", "CreditBal2", "IsGroup", "Level", "Id", "ParentId"]


def _dong(tk, ps, nhom, cap, id_, cha_id):
    return [tk, "", 0, 0, ps, ps, 0, 0, "True" if nhom else "False", cap, id_, cha_id]


def _file_627(thu_muc, ten="A01 102026 BANG CAN DOI PHAT SINH.xlsx"):
    """6277 (nhóm) = 62771 + 62772 + 62781 + 62782 theo cây Bravo; 6278 lá riêng."""
    rows = [_dong("627", 300, True, 0, "1", ""), _dong("6277", 300, True, 1, "2", "1"),
            _dong("62771", 100, False, 2, "3", "2"), _dong("62772", 50, False, 2, "4", "2"),
            _dong("62781", 100, False, 2, "5", "2"), _dong("62782", 50, False, 2, "6", "2"),
            _dong("6278", 0, False, 1, "7", "1")]
    thu_muc.mkdir(exist_ok=True)
    pd.DataFrame(rows, columns=COT_FILE).to_excel(thu_muc / ten, sheet_name="Table1", index=False)
    return thu_muc / ten


def _c93(df):
    return g9._c93(df, cd.dong_la(df))


def test_doc_cdps_lay_tk_cha_theo_parentid(tmp_path):
    df, _ = cdps.doc_cdps(str(_file_627(tmp_path)))
    assert dict(zip(df["account"], df["cha"])) == {
        "627": None, "6277": "627", "62771": "6277", "62772": "6277",
        "62781": "6277", "62782": "6277", "6278": "627"}


def test_c93_theo_cay_khong_bao_gia_con_khac_dau_so(tmp_path):
    df, _ = cdps.doc_cdps(str(_file_627(tmp_path)))
    assert _c93(df).so_loi == 0
    # cùng file mà không có cây (CĐPS nạp trước v6) thì đúng là bị báo theo đầu số
    assert _c93(df.drop(columns=["cha"])).so_loi == 1


def test_c93_theo_cay_van_bat_cha_lech_that(tmp_path):
    df, _ = cdps.doc_cdps(str(_file_627(tmp_path)))
    df.loc[df["account"] == "6277", "ps_no"] = 999
    r = _c93(df)       # 6277 lệch con của nó; 627 cũng lệch vì 6277 là con của 627
    ly_do = dict(zip(r.chi_tiet.iloc[:, 0].astype(str), r.chi_tiet["Lý do"] if "Lý do" in r.chi_tiet else r.chi_tiet.iloc[:, -1]))
    assert set(ly_do) == {"627", "6277"} and "cha 999 ≠ con 300" in ly_do["6277"]


def test_kho_v5_nang_len_v6_them_cot_cha(tmp_path):
    p = tmp_path / "kho.sqlite"
    con = sqlite3.connect(p)
    for cau in schema.DDL:
        con.execute(cau.replace(",\n        cha TEXT", ""))
    con.execute("INSERT INTO schema_version (phien_ban) VALUES (5)")
    con.execute("INSERT INTO cdps (chi_nhanh, ky_nam, ky_thang, account) VALUES ('A01', 2026, 10, '6277')")
    con.commit(); con.close()
    kho = KhoChotSo(str(p))
    try:
        df = kho.doc_cdps("A01", 2026, 10)
        assert "cha" in df.columns and df["cha"].isna().all()
        assert kho.thieu_cha_cdps("A01", 2026, 10)
        assert kho.con.execute("SELECT phien_ban FROM schema_version").fetchone()[0] == 6
    finally:
        kho.dong()


def test_nap_lai_cdps_giong_het_thi_bo_sung_cot_cha(tmp_path):
    tm = tmp_path / "cd"
    _file_627(tm)
    api = JsApi()
    api.nap_cdps_thu_muc(str(tm))
    kho = api._kho()
    try:                                   # giả lập CĐPS nạp trước v6: xóa cột cha
        kho.con.execute("UPDATE cdps SET cha = NULL")
        kho.con.commit()
    finally:
        kho.dong()
    r = api.nap_cdps_thu_muc(str(tm))      # không tick ghi đè — số liệu y hệt
    assert r["nap"] == [] and len(r["bo_qua_trung"]) == 1
    kho = api._kho()
    try:
        assert not kho.thieu_cha_cdps("A01", 2026, 10)
        assert _c93(kho.doc_cdps("A01", 2026, 10)).so_loi == 0
    finally:
        kho.dong()
