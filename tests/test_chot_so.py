import io

import pandas as pd

from app.chot_so import van_tay, chuoi_dong, doi_chieu, dien_diff, KHOP, LECH, CHUA_CHOT


def _df(rows):
    return pd.DataFrame(rows)


def test_van_tay_giong_nhau_khi_du_lieu_giong():
    df1 = _df([{"DocNo": "1", "Amount": 100.0}, {"DocNo": "2", "Amount": 200.0}])
    df2 = _df([{"DocNo": "1", "Amount": 100.0}, {"DocNo": "2", "Amount": 200.0}])
    assert van_tay(df1).ma_bam == van_tay(df2).ma_bam
    assert van_tay(df1).so_dong == 2
    assert van_tay(df1).tong_ps == 300.0


def test_van_tay_khong_doi_khi_dao_thu_tu_dong():
    df1 = _df([{"DocNo": "1", "Amount": 100.0}, {"DocNo": "2", "Amount": 200.0}])
    df2 = _df([{"DocNo": "2", "Amount": 200.0}, {"DocNo": "1", "Amount": 100.0}])
    assert van_tay(df1).ma_bam == van_tay(df2).ma_bam  # đảo dòng ≠ đổi dữ liệu


def test_van_tay_khac_khi_sua_mot_dong():
    df1 = _df([{"DocNo": "1", "Amount": 100.0}])
    df2 = _df([{"DocNo": "1", "Amount": 100.01}])
    assert van_tay(df1).ma_bam != van_tay(df2).ma_bam


def test_van_tay_on_dinh_qua_table_round_trip():
    df = _df([{"DocNo": "0001", "DocDate": pd.Timestamp("2026-08-01"), "Amount": 100.0}])
    blob = df.to_json(orient="table", index=False)
    lai = pd.read_json(io.StringIO(blob), orient="table").reset_index(drop=True)
    assert van_tay(df).ma_bam == van_tay(lai).ma_bam


def test_van_tay_giu_so_0_dau_docno():
    assert van_tay(_df([{"DocNo": "0001", "Amount": 100.0}])).ma_bam != \
           van_tay(_df([{"DocNo": "1", "Amount": 100.0}])).ma_bam


def test_doi_chieu_chua_chot_khi_khong_co_van_tay():
    df = _df([{"DocCode": "PX", "DocNo": "1", "DebitAccount": "621", "Amount": 100.0}])
    assert doi_chieu(None, df).trang_thai == CHUA_CHOT


def test_doi_chieu_khop_khi_du_lieu_khong_doi():
    df = _df([{"DocCode": "PX", "DocNo": "1", "DebitAccount": "621", "Amount": 100.0}])
    assert doi_chieu(van_tay(df), df).trang_thai == KHOP


def test_doi_chieu_lech_va_bao_delta():
    cu = _df([{"DocCode": "PX", "DocNo": "1", "DebitAccount": "621", "Amount": 100.0}])
    moi = _df([
        {"DocCode": "PX", "DocNo": "1", "DebitAccount": "621", "Amount": 100.0},
        {"DocCode": "PX", "DocNo": "2", "DebitAccount": "621", "Amount": 50.0},
    ])
    kq = doi_chieu(van_tay(cu), moi, df_chot=cu)
    assert kq.trang_thai == LECH
    assert kq.delta_dong == 1
    assert kq.delta_ps == 50.0


def test_dien_diff_them_bot():
    cu = _df([
        {"DocCode": "PX", "DocNo": "1", "DebitAccount": "621", "Amount": 100.0},
        {"DocCode": "PX", "DocNo": "9", "DebitAccount": "621", "Amount": 10.0},
    ])
    moi = _df([
        {"DocCode": "PX", "DocNo": "1", "DebitAccount": "621", "Amount": 100.0},
        {"DocCode": "PX", "DocNo": "2", "DebitAccount": "621", "Amount": 50.0},
    ])
    d = dien_diff(cu, moi)
    assert len(d["them"]) == 1 and d["them"].iloc[0]["DocNo"] == "2"
    assert len(d["bot"]) == 1 and d["bot"].iloc[0]["DocNo"] == "9"
    assert d["tom_tat"]["so_them"] == 1 and d["tom_tat"]["so_bot"] == 1
