import pandas as pd
import pytest

from app import so_ban_hang as sbh
from tests.conftest import MAC_DINH_SBH


def _ghi(path, rows=None, bo_cot=()):
    rows = rows or [{}]
    df = pd.DataFrame([{**MAC_DINH_SBH, **r} for r in rows])
    df = df.drop(columns=list(bo_cot))
    df.to_excel(path, sheet_name="Table1", index=False)
    return str(path)


def test_suy_chi_nhanh_ky_khi_ma_nam_giua_ten_file():
    assert sbh.suy_branch_ky("So chi tiet ban hang A01 092026.xlsx") == ("A01", 2026, 9)
    assert sbh.suy_branch_ky(r"D:\x\a05 082026 So ban hang.xlsx") == ("A05", 2026, 8)
    assert sbh.suy_branch_ky("So chi tiet ban hang A01.xlsx") is None
    assert sbh.suy_branch_ky("So chi tiet ban hang A01 132026.xlsx") is None


def test_nhan_dien_theo_cot():
    assert sbh.la_so_ban_hang(MAC_DINH_SBH)
    assert not sbh.la_so_ban_hang(["DocNo", "DebitAccount", "CreditAccount", "Amount"])


def test_doc_giu_so_0_dau_va_ep_so(tmp_path):
    p = _ghi(tmp_path / "So chi tiet ban hang A01 082026.xlsx",
             [{"DocNo": "0051998", "Amount3": "0"}])
    df, m = sbh.doc_so_ban_hang(p)
    assert (m.ma, m.nam, m.thang) == ("A01", 2026, 8)
    assert df.loc[0, "DocNo"] == "0051998"
    assert df["Amount3"].dtype == float and df.loc[0, "Amount3"] == 0


def test_thieu_cot_bao_ro(tmp_path):
    p = _ghi(tmp_path / "So chi tiet ban hang A01 082026.xlsx", bo_cot=("Amount3",))
    with pytest.raises(sbh.KhongPhaiSoBanHang, match="Amount3"):
        sbh.doc_so_ban_hang(p)


def test_ky_ten_file_khac_ngay_chung_tu_thi_tu_choi(tmp_path):
    """Đặt tên tháng 09 nhưng ruột là tháng 08 = nạp nhầm file, không được đoán."""
    p = _ghi(tmp_path / "So chi tiet ban hang A01 092026.xlsx")
    with pytest.raises(sbh.KhongPhaiSoBanHang, match="08/2026"):
        sbh.doc_so_ban_hang(p)
