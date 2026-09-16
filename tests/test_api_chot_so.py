import pandas as pd

from app.api import JsApi
from app.loader import ThongTinFile
from app.checks.base import BoiCanh
from tests.conftest import tao_df


def _api(tmp_path):
    api = JsApi(); api._thu_muc_kho = str(tmp_path)   # ép kho vào thư mục test
    return api


def _don_vi(df):
    from app.api import DonVi
    tt = ThongTinFile(path="x.xlsx", ten="x.xlsx", ky="08/2026", ky_thang=8, ky_nam=2026,
                      so_dong=len(df), tong_ps=float(df["Amount"].sum()), chi_nhanh="A01")
    return DonVi(df=df, tt=tt)


# tao_df (tests/conftest.py) điền sẵn mọi cột COT_CHUAN mà 30 check cần (Description,
# DocDate,...) — DataFrame thô chỉ 5 cột như trong brief sẽ vỡ ở G1/G6 (KeyError
# "Description") vì đây là dữ liệu thật đi qua chay_tat_ca, không phải mock.
DF = tao_df([{"DocCode": "PX", "DocNo": "1", "DebitAccount": "621", "CreditAccount": "1521", "Amount": 100.0}])


def test_chot_roi_bao_da_chot_va_khop(tmp_path):
    api = _api(tmp_path); d = _don_vi(DF); api._dv = [d]; api._i = 0
    api._chay_mot_don_vi(d)
    assert api.chot_so("lần 1")["chot"]["trang_thai"] == "DA_CHOT"
    # chạy lại kiểm tra: đối chiếu phải KHỚP
    tt = api._tom_tat()
    assert tt["tomtat"]["chot"]["doi_chieu"] == "KHOP"


def test_sua_du_lieu_thi_doi_chieu_lech(tmp_path):
    api = _api(tmp_path); d = _don_vi(DF); api._dv = [d]; api._i = 0
    api._chay_mot_don_vi(d); api.chot_so("")
    # đổi dữ liệu nguồn rồi chạy lại
    d.df = pd.concat([DF, tao_df([{"DocCode": "PX", "DocNo": "2", "DebitAccount": "621",
                                    "CreditAccount": "1521", "Amount": 50.0}])], ignore_index=True)
    api._chay_mot_don_vi(d)
    tt = api._tom_tat()
    assert tt["tomtat"]["chot"]["doi_chieu"] == "LECH"
    assert tt["tomtat"]["chot"]["tom_tat_lech"]["delta_dong"] == 1
