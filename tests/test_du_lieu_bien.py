"""D2/C7 — chạy toàn bộ pipeline trên các hình dạng dữ liệu từng làm vỡ chương trình."""
import pytest

from app import checks, trang_thai as tt
from app.checks import g4_kho_gia_von as g4

TEN_FIXTURE = ["df_rong", "df_tk_null", "df_description_nan"]


@pytest.mark.parametrize("ten", TEN_FIXTURE)
def test_pipeline_chay_duoc_tren_moi_hinh_dang(ten, ctx, request):
    df = request.getfixturevalue(ten)
    kq = checks.chay_tat_ca(df, ctx)
    assert len(kq) == 40
    ds = tt.suy_trang_thai(df, {r.ma: r for r in kq})
    assert len(ds) == 16
    kl = tt.tinh_ket_luan(kq, ds)
    assert kl["muc_do_ket_luan"] in (tt.SAN_SANG, tt.CAN_RA_SOAT, tt.CHUA_SAN_SANG)


def test_frame_rong_khong_lam_vo_g4(df_rong, ctx):
    """C7: "chuỗi" + Series float64 rỗng ném _UFuncNoLoopError ở dòng lý do C4.1."""
    kq = {r.ma: r for r in g4.kiem_tra(df_rong, ctx)}
    assert kq["C4.1"].so_loi == 0 and kq["C4.2"].so_loi == 0
    assert list(kq["C4.1"].chi_tiet.columns)[-1] == "ly_do"


def test_frame_rong_thi_ca_11_buoc_deu_khong_ap_dung(df_rong, ctx):
    """Không dòng nào thì không bước nào áp dụng — kể cả bước 11.

    Trước đây bước 11 ra "đã làm / Mọi TK doanh thu/chi phí đã về 0" trên file rỗng.
    """
    kq = {r.ma: r for r in checks.chay_tat_ca(df_rong, ctx)}
    ds = tt.suy_trang_thai(df_rong, kq)
    assert [b.trang_thai for b in ds] == [tt.KHONG_AP_DUNG] * 16


def test_tk_toan_null_chi_trip_check_vang(df_tk_null, ctx):
    kq = {r.ma: r for r in checks.chay_tat_ca(df_tk_null, ctx)}
    assert kq["C2.2"].so_loi == 2                       # TK sai định dạng
    assert all(r.muc_do_thuc != "do" for r in kq.values())


def test_description_nan_bi_bat_boi_c11(df_description_nan, ctx):
    kq = {r.ma: r for r in checks.chay_tat_ca(df_description_nan, ctx)}
    assert kq["C1.1"].so_loi == 2
