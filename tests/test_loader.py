import pandas as pd
import pytest

from app import loader


def _xlsx_mau(tmp_path):
    df = pd.DataFrame({
        "DocCode": ["BT", "PN"], "DocNo": ["BT1", "PN1"],
        "DocDate": ["2026-08-05", "2026-08-20"],
        "DebitAccount": [" 6421 ", 1521], "CreditAccount": ["1111", "3311"],
        "Amount": [1000, "abc"], "Description": ["NULL", "Mua NVL"],
        "TaxCode": ["NULL", "V10"], "CustomerCode": ["NULL", "NCC01"],
        "CurrencyCode": ["VND", "VND"], "OriginalAmount": [0, 0], "ExchangeRate": [1, 1],
        "Quantity9": [0, 10], "UnitCost": [0, 500], "CreatedByName": ["A", "B"],
    })
    p = tmp_path / "Bang ke test.xlsx"
    df.to_excel(p, sheet_name="Table1", index=False)
    return p


def test_chuan_hoa_null_va_so():
    df = pd.DataFrame({"Description": ["NULL", " ", "ok"], "Amount": ["1", "x", 3],
                       "DebitAccount": [6421, " 111 ", None], "CreditAccount": ["1", "2", "3"],
                       "DocNo": ["a", "b", "c"], "DocDate": ["2026-08-01"] * 3})
    out, log = loader.chuan_hoa(df)
    assert out["Description"].isna().tolist() == [True, True, False]
    assert out["Amount"].tolist() == [1.0, 0.0, 3.0]
    assert out["DebitAccount"].tolist()[:2] == ["6421", "111"]
    assert any("Amount" in m for m in log)


def test_chuan_hoa_cot_ma_doc_thanh_float_khong_con_duoi_cham_khong():
    df = pd.DataFrame({
        "DebitAccount": [6421.0, 1521.0, None],
        "CreditAccount": ["1111", "3311", "1111"],
        "DocNo": ["a", "b", "c"], "DocDate": ["2026-08-01"] * 3, "Amount": [1, 2, 3],
    })
    out, _ = loader.chuan_hoa(df)
    assert out["DebitAccount"].tolist()[:2] == ["6421", "1521"]
    assert out["DebitAccount"].isna().tolist() == [False, False, True]


def test_xac_dinh_ky_lay_thang_pho_bien():
    df = pd.DataFrame({"DocDate": pd.to_datetime(["2026-08-01", "2026-08-09", "2026-07-31"])})
    assert loader.xac_dinh_ky(df) == (8, 2026)


def test_doc_bang_ke_tra_thong_tin(tmp_path):
    df, tt = loader.doc_bang_ke(str(_xlsx_mau(tmp_path)))
    assert tt.so_dong == 2 and tt.ky == "08/2026" and tt.tong_ps == 1000.0
    assert df["DebitAccount"].tolist() == ["6421", "1521"]
    assert df["TaxCode"].isna().tolist() == [True, False]


def test_doc_bang_ke_thieu_cot_bao_loi(tmp_path):
    p = tmp_path / "sai.xlsx"
    pd.DataFrame({"DocNo": ["x"]}).to_excel(p, index=False)
    with pytest.raises(ValueError, match="Thiếu cột"):
        loader.doc_bang_ke(str(p))


def test_tim_file_moi_nhat(tmp_path):
    (tmp_path / "a.xlsx").write_bytes(b"1")
    import time; time.sleep(0.05)
    (tmp_path / "b.xlsx").write_bytes(b"1")
    (tmp_path / "~$tam.xlsx").write_bytes(b"1")
    assert loader.tim_file_moi_nhat(str(tmp_path)).endswith("b.xlsx")
    assert loader.tim_file_moi_nhat(str(tmp_path / "khong_co")) is None


FILE_THAT = "1. Source/Bang ke chung tu 082027.xlsx"


@pytest.mark.skipif(not __import__("os").path.exists(FILE_THAT), reason="không có file thật")
def test_doc_file_that():
    import time
    t = time.time()
    df, tt = loader.doc_bang_ke(FILE_THAT)
    assert tt.so_dong > 70_000 and tt.ky == "08/2026"
    assert time.time() - t < 30
