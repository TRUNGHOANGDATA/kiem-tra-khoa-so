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


def tao_df(rows: list[dict]) -> pd.DataFrame:
    """Tạo DataFrame test: mỗi dict chỉ cần ghi cột khác mặc định."""
    full = [{**MAC_DINH, **r} for r in rows]
    df = pd.DataFrame(full)
    df["DocDate"] = pd.to_datetime(df["DocDate"])
    for c in ("Amount", "OriginalAmount", "ExchangeRate", "Quantity9", "UnitCost"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df


@pytest.fixture
def ctx() -> BoiCanh:
    return BoiCanh(ky_thang=8, ky_nam=2026)
