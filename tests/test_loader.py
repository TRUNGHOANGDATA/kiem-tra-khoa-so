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


def test_ngay_dang_text_doc_theo_kieu_viet_nam():
    """B1: không có dayfirst, "05/08/2026" thành 08/05 -> suy ra kỳ 05/2026 mà không báo gì."""
    df = pd.DataFrame({"DocDate": ["05/08/2026", "12/08/2026", "20/08/2026", "31/08/2026"],
                       "DocNo": list("abcd"), "DebitAccount": ["6421"] * 4,
                       "CreditAccount": ["1111"] * 4, "Amount": [1] * 4})
    out, log = loader.chuan_hoa(df)
    assert out["DocDate"].dt.day.tolist() == [5, 12, 20, 31]
    assert out["DocDate"].dt.month.tolist() == [8] * 4
    assert loader.xac_dinh_ky(out) == (8, 2026)
    assert log == []


def test_ngay_dang_text_iso_khong_bi_dao_thang():
    """B1: bật dayfirst cho cả cột sẽ đọc "2026-08-05" thành 08/05 và "2026-08-20" thành NaT."""
    s = pd.Series(["2026-08-05", "2026-08-20", "2026-08-31"])
    ngay = loader.doc_ngay(s)
    assert ngay.dt.month.tolist() == [8, 8, 8]
    assert ngay.dt.day.tolist() == [5, 20, 31]


def test_doc_ngay_giu_nguyen_cot_datetime_that():
    s = pd.to_datetime(pd.Series(["2026-08-05", "2026-08-20"]))
    assert loader.doc_ngay(s).equals(s)


def test_ngay_khong_doc_duoc_ghi_vao_nhat_ky():
    """B1: ngày hỏng phải để lại vết như cột số, không âm thầm thành NaT."""
    df = pd.DataFrame({"DocDate": ["05/08/2026", "khong-phai-ngay", "32/13/2026"],
                       "DocNo": list("abc"), "DebitAccount": ["6421"] * 3,
                       "CreditAccount": ["1111"] * 3, "Amount": [1] * 3})
    out, log = loader.chuan_hoa(df)
    assert out["DocDate"].isna().tolist() == [False, True, True]
    assert any("DocDate" in m and "2 giá trị" in m for m in log), log


def test_xac_dinh_ky_bao_loi_khi_khong_co_ngay_hop_le():
    """D3: nhánh ValueError này là chốt chặn duy nhất trước khi các check gặp frame rỗng."""
    df = pd.DataFrame({"DocDate": pd.to_datetime(pd.Series([None, None], dtype="object"))})
    with pytest.raises(ValueError, match="Không có ngày chứng từ hợp lệ"):
        loader.xac_dinh_ky(df)


def test_doc_bang_ke_file_rong_bao_dung_nguyen_nhan(tmp_path):
    """C7: file rỗng phải nói là rỗng, không phải 'không có ngày chứng từ hợp lệ'."""
    p = tmp_path / "rong.xlsx"
    pd.DataFrame(columns=["DocNo", "DocDate", "DebitAccount", "CreditAccount", "Amount"]).to_excel(p, index=False)
    with pytest.raises(ValueError, match="không có dòng dữ liệu"):
        loader.doc_bang_ke(str(p))


def test_nhat_ky_ghi_so_thuc_khong_nguyen(tmp_path):
    """D3: dòng log của phép ép kiểu số — nguồn duy nhất của sheet 'Nhat ky xu ly'."""
    df = pd.DataFrame({"DocNo": ["a", "b"], "DocDate": ["2026-08-01"] * 2,
                       "DebitAccount": ["6421", "1111"], "CreditAccount": ["1111", "1121"],
                       "Amount": ["1000", "khong-phai-so"]})
    _, log = loader.chuan_hoa(df)
    assert [m for m in log if m.startswith("Cột Amount")] == [
        "Cột Amount: 1 giá trị không phải số, đã ép về 0"]


def test_chuan_hoa_giu_nguyen_float_le_o_cot_ma():
    """D3: cột mã đọc thành float nhưng có giá trị lẻ -> không ép Int64, giữ nguyên chuỗi."""
    df = pd.DataFrame({"DebitAccount": [6421.5, 1521.0], "CreditAccount": ["1111", "3311"],
                       "DocNo": ["a", "b"], "DocDate": ["2026-08-01"] * 2, "Amount": [1, 2]})
    out, _ = loader.chuan_hoa(df)
    assert out["DebitAccount"].tolist() == ["6421.5", "1521.0"]


def test_xac_dinh_ky_lay_thang_pho_bien():
    df = pd.DataFrame({"DocDate": pd.to_datetime(["2026-08-01", "2026-08-09", "2026-07-31"])})
    assert loader.xac_dinh_ky(df) == (8, 2026)


def test_thong_ke_ngoai_ky_tra_tong_va_phan_ra_theo_thang():
    """Cảnh báo sớm: dòng ngoài kỳ 08/2026 phải đếm đúng tổng và sắp nhiều->ít."""
    df = pd.DataFrame({"DocDate": pd.to_datetime([
        "2026-08-01", "2026-08-02", "2026-08-03",   # 3 dòng trong kỳ
        "2026-07-30", "2026-07-31",                  # 2 dòng 07/2026
        "2026-09-01",                                 # 1 dòng 09/2026
    ])})
    tong, ct = loader.thong_ke_ngoai_ky(df, 8, 2026)
    assert tong == 3
    assert ct == [("07/2026", 2), ("09/2026", 1)]


def test_thong_ke_ngoai_ky_frame_sach_tra_rong():
    df = pd.DataFrame({"DocDate": pd.to_datetime(["2026-08-01", "2026-08-31"])})
    assert loader.thong_ke_ngoai_ky(df, 8, 2026) == (0, [])


def test_thong_ke_ngoai_ky_khong_co_ngay_hop_le_tra_rong():
    df = pd.DataFrame({"DocDate": pd.to_datetime(pd.Series([None, None], dtype="object"))})
    assert loader.thong_ke_ngoai_ky(df, 8, 2026) == (0, [])


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
