import io

import pandas as pd

from app.chot_so import van_tay, chuoi_dong


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
