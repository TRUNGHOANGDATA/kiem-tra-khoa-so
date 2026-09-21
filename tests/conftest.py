import pandas as pd
import pytest

from app.checks.base import BoiCanh

MAC_DINH = {
    # PC = phiếu chi, cố ý KHÔNG thuộc DOC_DIEU_CHUYEN để dòng mặc định vẫn bị C1.4 soi
    "DocCode": "PC", "DocNo": "PC2608-000001", "DocDate": "2026-08-15",
    "DebitAccount": "6421", "CreditAccount": "1111", "Amount": 1_000_000.0,
    "Description": "Chi phí", "TaxCode": None, "CustomerCode": None,
    "CustomerName": None, "CurrencyCode": "VND", "OriginalAmount": 0.0,
    "ExchangeRate": 1.0, "Quantity9": 0.0, "UnitCost": 0.0,
    "ItemCode": None, "ItemName": None, "WarehouseName": None,
    "CreatedByName": "Kế toán A",
    # Mặc định để trống: phần lớn test chỉ quan tâm một đơn vị, các test nhiều chi
    # nhánh / báo cáo quản trị tự ghi đè các cột này.
    "BranchCode": None, "Đơn vị": None,
    # Trục dựng báo cáo quản trị (Nhóm 8): mã khoản mục chi phí & bộ phận.
    "ExpenseCatgCode": None, "ExpenseCatgName": None, "DeptName": None,
    # Tài khoản ngân hàng hai vế — thứ phân biệt "chuyển tiền giữa hai ngân hàng của
    # công ty" với "tự chuyển vào chính mình" khi số hiệu TK hai vế giống nhau (C2.3).
    "BankAccId": None, "CrspBankAccId": None,
}


COT_SO_TEST = ("Amount", "OriginalAmount", "ExchangeRate", "Quantity9", "UnitCost")


def tao_df(rows: list[dict]) -> pd.DataFrame:
    """Tạo DataFrame test: mỗi dict chỉ cần ghi cột khác mặc định.

    Danh sách rỗng phải ra frame rỗng ĐÚNG KIỂU (không phải KeyError) — các lỗi
    khó nhất trên nhánh này đều xuất hiện ở frame rỗng hoặc toàn NaN.
    """
    full = [{**MAC_DINH, **r} for r in rows]
    df = pd.DataFrame(full, columns=list(MAC_DINH))
    df["DocDate"] = pd.to_datetime(df["DocDate"])
    for c in COT_SO_TEST:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0).astype(float)
    return df


COT_CDPS = ("account", "ten", "du_dau_no", "du_dau_co", "ps_no", "ps_co",
            "du_cuoi_no", "du_cuoi_co", "is_group", "level")


def tao_cdps(rows: list[dict]) -> pd.DataFrame:
    """CĐPS giả: mỗi dict chỉ cần ghi cột khác mặc định (mặc định là dòng LÁ, số 0)."""
    mac_dinh = {"account": "1111", "ten": "", "du_dau_no": 0.0, "du_dau_co": 0.0,
                "ps_no": 0.0, "ps_co": 0.0, "du_cuoi_no": 0.0, "du_cuoi_co": 0.0,
                "is_group": False, "level": 1}
    df = pd.DataFrame([{**mac_dinh, **r} for r in rows], columns=list(COT_CDPS))
    for c in COT_CDPS[2:8]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0).astype(float)
    return df


@pytest.fixture
def ctx() -> BoiCanh:
    return BoiCanh(ky_thang=8, ky_nam=2026)


@pytest.fixture
def df_rong() -> pd.DataFrame:
    """Kỳ không có dòng nào."""
    return tao_df([])


@pytest.fixture
def df_tk_null() -> pd.DataFrame:
    """File mà mọi số hiệu tài khoản đều trống — chỉ C2.2 (vàng) bắt được."""
    return tao_df([{"DebitAccount": None, "CreditAccount": None},
                   {"DebitAccount": None, "CreditAccount": None, "Amount": 5.0}])


@pytest.fixture
def df_description_nan() -> pd.DataFrame:
    """Diễn giải và tên vật tư đều NaN trên mọi dòng."""
    return tao_df([{"Description": None, "ItemName": None},
                   {"Description": None, "ItemName": None, "DebitAccount": "6221"}])
