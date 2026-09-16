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


def test_chot_roi_sua_file_cung_path_thi_thay_drift(tmp_path):
    import pandas as pd
    from app.api import JsApi
    xlsx = tmp_path / "bk.xlsx"

    def lam(rows):
        pd.DataFrame(rows).to_excel(xlsx, index=False)

    R = [{"BranchCode": "A01", "DocCode": "PX", "DocNo": "0001", "DocDate": "05/08/2026",
          "DebitAccount": "6214", "CreditAccount": "1521", "Amount": 1000.0, "Description": "x"}]
    lam(R)
    api = JsApi(); api._thu_muc_kho = str(tmp_path)
    api.nap_nhieu_file([str(xlsx)]); api.chay_kiem_tra([str(xlsx)])
    assert api.chot_so("")["chot"]["trang_thai"] == "DA_CHOT"
    # sửa file, GIỮ NGUYÊN path, KHÔNG gọi nạp lại:
    lam(R + [{"BranchCode": "A01", "DocCode": "PX", "DocNo": "0002", "DocDate": "06/08/2026",
              "DebitAccount": "6214", "CreditAccount": "1521", "Amount": 500.0, "Description": "y"}])
    tt = api.chay_kiem_tra([str(xlsx)])   # cùng path -> phải tự đọc lại vì kỳ đã chốt
    assert tt["tomtat"]["chot"]["doi_chieu"] == "LECH"
    assert tt["tomtat"]["chot"]["tom_tat_lech"]["delta_dong"] == 1


def test_trang_thai_chot_bao_loi_kho_moi_hon(tmp_path):
    from app.api import JsApi, DonVi
    from app.kho.ket_noi import mo_kho
    from app.kho.schema import PHIEN_BAN_SCHEMA
    from app.loader import ThongTinFile
    import pandas as pd
    p = str(tmp_path / "kho_chot_so.sqlite")
    con = mo_kho(p); con.execute("UPDATE schema_version SET phien_ban=?", (PHIEN_BAN_SCHEMA + 1,)); con.commit(); con.close()
    api = JsApi(); api._thu_muc_kho = str(tmp_path)
    df = pd.DataFrame([{"DocCode": "PX", "DocNo": "1", "DebitAccount": "621", "CreditAccount": "1521", "Amount": 100.0}])
    tt = ThongTinFile(path="x.xlsx", ten="x.xlsx", ky="08/2026", ky_thang=8, ky_nam=2026,
                      so_dong=1, tong_ps=100.0, chi_nhanh="A01")
    r = api._trang_thai_chot(DonVi(df=df, tt=tt))
    assert r["trang_thai"] == "CHUA_CHOT" and "loi_kho" in r
