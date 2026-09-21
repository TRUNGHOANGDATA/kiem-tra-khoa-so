import io

import pandas as pd

from app.chot_so import (van_tay, chuoi_dong, doi_chieu, dien_diff, dien_diff_ct,
                         KHOP, LECH, CHUA_CHOT)


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
    assert kq.so_ct_anh_huong == 1  # chỉ chứng từ PX·2 mới xuất hiện


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
    assert d["tom_tat"]["so_ct_anh_huong"] == 2  # PX·2 (thêm) và PX·9 (bớt)


def test_dien_diff_index_trung_lap_van_dung():
    """df.loc[idx] với index trùng lặp có thể trả nhiều dòng — dien_diff phải
    reset index trước khi chọn dòng để không đếm nhầm."""
    cu = _df([
        {"DocCode": "PX", "DocNo": "1", "DebitAccount": "621", "Amount": 100.0},
        {"DocCode": "PX", "DocNo": "9", "DebitAccount": "621", "Amount": 10.0},
    ])
    moi = _df([
        {"DocCode": "PX", "DocNo": "1", "DebitAccount": "621", "Amount": 100.0},
        {"DocCode": "PX", "DocNo": "2", "DebitAccount": "621", "Amount": 50.0},
    ])
    cu.index = [0, 0]
    moi.index = [0, 0]
    d = dien_diff(cu, moi)
    assert len(d["them"]) == 1 and d["them"].iloc[0]["DocNo"] == "2"
    assert len(d["bot"]) == 1 and d["bot"].iloc[0]["DocNo"] == "9"
    assert d["tom_tat"]["so_them"] == 1 and d["tom_tat"]["so_bot"] == 1
    assert d["tom_tat"]["so_ct_anh_huong"] == 2


def test_dien_diff_thieu_doccode_dung_docno_de_dem():
    cu = _df([
        {"DocNo": "1", "DebitAccount": "621", "Amount": 100.0},
        {"DocNo": "9", "DebitAccount": "621", "Amount": 10.0},
    ])
    moi = _df([
        {"DocNo": "1", "DebitAccount": "621", "Amount": 100.0},
        {"DocNo": "2", "DebitAccount": "621", "Amount": 50.0},
    ])
    d = dien_diff(cu, moi)
    assert d["tom_tat"]["so_ct_anh_huong"] == 2  # thiếu DocCode vẫn đếm được qua DocNo


def test_dien_diff_thieu_docno_khong_loi():
    """Thiếu DocNo (chỉ có DocCode) không được ném lỗi — trước đây AttributeError."""
    cu = _df([
        {"DocCode": "PX", "DebitAccount": "621", "Amount": 100.0},
        {"DocCode": "PX", "DebitAccount": "621", "Amount": 10.0},
    ])
    moi = _df([
        {"DocCode": "PX", "DebitAccount": "621", "Amount": 100.0},
        {"DocCode": "PX", "DebitAccount": "621", "Amount": 50.0},
    ])
    d = dien_diff(cu, moi)
    assert d["tom_tat"]["so_them"] == 1 and d["tom_tat"]["so_bot"] == 1


# ------------------------------------------------ dien_diff_ct: phân loại theo CHỨNG TỪ
def _ct(rows):
    """Bảng kê tối thiểu có đủ khóa chứng từ."""
    return pd.DataFrame(rows, columns=["DocCode", "DocNo", "DebitAccount", "CreditAccount", "Amount"])


def test_dien_diff_ct_chung_tu_bi_SUA_khong_bi_ke_thanh_them_va_bot():
    """Một dòng của chứng từ đổi số tiền: `dien_diff` cũ kể thành 1 bớt + 1 thêm rời rạc,
    người đọc phải tự ghép. Phân loại theo chứng từ thì nó là MỘT việc: chứng từ bị SỬA."""
    chot = _ct([["HD", "0001", "1311", "5111", 100.0],
                ["HD", "0001", "1311", "33311", 10.0]])
    moi = _ct([["HD", "0001", "1311", "5111", 120.0],      # đổi số tiền
               ["HD", "0001", "1311", "33311", 10.0]])
    d = dien_diff_ct(chot, moi)
    assert d["tom_tat"] == {"ct_them": 0, "ct_bot": 0, "ct_sua": 1}
    assert len(d["them"]) == 0 and len(d["bot"]) == 0
    sua = d["sua"][0]
    assert sua["so_ct"] == "HD·0001"
    assert sua["dong_cu"]["Amount"].tolist() == [100.0]     # chỉ DÒNG LỆCH, không cả chứng từ
    assert sua["dong_moi"]["Amount"].tolist() == [120.0]


def test_dien_diff_ct_tach_bach_them_bot_sua():
    chot = _ct([["HD", "A", "1311", "5111", 10.0],          # còn nguyên -> không hiện
                ["HD", "B", "1311", "5111", 20.0],          # biến mất -> BỚT
                ["HD", "C", "1311", "5111", 30.0]])         # đổi -> SỬA
    moi = _ct([["HD", "A", "1311", "5111", 10.0],
               ["HD", "C", "1311", "5111", 35.0],
               ["HD", "D", "1311", "5111", 40.0]])          # mới -> THÊM
    d = dien_diff_ct(chot, moi)
    assert d["tom_tat"] == {"ct_them": 1, "ct_bot": 1, "ct_sua": 1}
    assert d["them"]["DocNo"].tolist() == ["D"]
    assert d["bot"]["DocNo"].tolist() == ["B"]
    assert [s["so_ct"] for s in d["sua"]] == ["HD·C"]


def test_dien_diff_ct_them_bot_dong_trong_cung_chung_tu():
    """Chứng từ thêm hẳn một dòng mới: vẫn là SỬA, và dòng cũ rỗng."""
    chot = _ct([["PX", "9", "6211", "1521", 50.0]])
    moi = _ct([["PX", "9", "6211", "1521", 50.0],
               ["PX", "9", "6211", "1522", 70.0]])
    d = dien_diff_ct(chot, moi)
    assert d["tom_tat"]["ct_sua"] == 1
    sua = d["sua"][0]
    assert len(sua["dong_cu"]) == 0 and sua["dong_moi"]["Amount"].tolist() == [70.0]


def test_dien_diff_ct_khong_doi_gi_thi_rong():
    df = _ct([["HD", "1", "1311", "5111", 10.0]])
    d = dien_diff_ct(df, df)
    assert d["tom_tat"] == {"ct_them": 0, "ct_bot": 0, "ct_sua": 0} and d["sua"] == []


def test_dien_diff_ct_giu_nguyen_dien_diff_cu():
    """Bản cũ vẫn phải chạy y như trước — lay_diff_chot đang dùng."""
    chot = _ct([["HD", "1", "1311", "5111", 10.0]])
    moi = _ct([["HD", "1", "1311", "5111", 11.0]])
    cu = dien_diff(chot, moi)
    assert cu["tom_tat"]["so_them"] == 1 and cu["tom_tat"]["so_bot"] == 1
