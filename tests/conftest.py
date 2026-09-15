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
