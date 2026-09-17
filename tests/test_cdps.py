"""Parser CĐPS: suy chi nhánh+kỳ từ tên file + đọc sheet Table1 chuẩn hóa."""
import pandas as pd
import pytest

from app import cdps

COT = ["Account", "AccountName", "DebitBal1", "CreditBal1", "DebitAmount",
       "CreditAmount", "DebitBal2", "CreditBal2", "IsGroup", "Level"]


def _viet_cdps(path, rows):
    pd.DataFrame(rows, columns=COT).to_excel(path, sheet_name="Table1", index=False)


def test_suy_branch_ky_tu_ten_file():
    assert cdps.suy_branch_ky("A08 082026 BANG CAN DOI PHAT SINH.xlsx") == ("A08", 2026, 8)
    assert cdps.suy_branch_ky(r"C:\x\A10 122025 CDPS.xlsx") == ("A10", 2025, 12)


def test_suy_branch_ky_ten_la_tra_none():
    assert cdps.suy_branch_ky("bang can doi.xlsx") is None
    assert cdps.suy_branch_ky("A08_082026.xlsx") is None      # thiếu khoảng trắng
    assert cdps.suy_branch_ky("A08 132026 CDPS.xlsx") is None  # tháng 13 không hợp lệ


def test_doc_cdps_du_dau_4212_va_meta(tmp_path):
    p = tmp_path / "A08 082026 CDPS.xlsx"
    _viet_cdps(p, [
        ["421", "Loi nhuan sau thue", "2981950998", "0", "0", "1571960518", "1409990480", "0", "True", "0"],
        ["4212", "Loi nhuan chua pp", "2981950998", "0", "0", "1571960518", "1409990480", "0", "False", "1"],
        ["911", "XD ket qua KD", "0", "0", "11403455364", "11403455364", "0", "0", "False", "0"],
    ])
    df, meta = cdps.doc_cdps(str(p))
    assert (meta.ma, meta.nam, meta.thang) == ("A08", 2026, 8)
    r = df[df["account"] == "4212"].iloc[0]
    assert r["du_dau_no"] == 2981950998.0 and r["du_dau_co"] == 0.0
    assert r["ps_co"] == 1571960518.0 and r["du_cuoi_no"] == 1409990480.0
    assert bool(r["is_group"]) is False and int(r["level"]) == 1
    assert bool(df[df["account"] == "421"].iloc[0]["is_group"]) is True


def test_doc_cdps_o_trong_thanh_0(tmp_path):
    p = tmp_path / "A08 082026 CDPS.xlsx"
    _viet_cdps(p, [["133", "Thue GTGT", "", "", "152637721", "152637721", "", "", "False", "0"]])
    df, _ = cdps.doc_cdps(str(p))
    r = df.iloc[0]
    assert r["du_dau_no"] == 0.0 and r["ps_no"] == 152637721.0


def test_doc_cdps_thieu_cot_bao_loi(tmp_path):
    p = tmp_path / "A08 082026 CDPS.xlsx"
    pd.DataFrame([{"Account": "911", "Foo": "1"}]).to_excel(p, sheet_name="Table1", index=False)
    with pytest.raises(cdps.KhongPhaiCdps):
        cdps.doc_cdps(str(p))


def test_doc_cdps_ten_file_khong_suy_duoc_bao_loi(tmp_path):
    p = tmp_path / "khong dung quy uoc.xlsx"
    _viet_cdps(p, [["911", "XDKQ", "0", "0", "0", "0", "0", "0", "False", "0"]])
    with pytest.raises(cdps.KhongPhaiCdps):
        cdps.doc_cdps(str(p))
