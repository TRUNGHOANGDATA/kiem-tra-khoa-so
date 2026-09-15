"""B4 — kết luận sẵn sàng khóa sổ ba mức, phải giống nhau ở giao diện và báo cáo Excel."""
import openpyxl
import pytest

from app import checks, report, trang_thai as tt
from app.api import JsApi
from app.loader import ThongTinFile
from tests.conftest import tao_df

# Ba kịch bản: sạch hoàn toàn / chỉ còn vàng + cần rà / có đỏ hoặc chưa làm.
SAN_SANG = [{"DebitAccount": "1111", "CreditAccount": "1121", "Amount": 100.0}]
# 131 mà thiếu mã đối tượng -> C2.1 vàng, không có check đỏ nào
CAN_RA_SOAT = [{"DebitAccount": "1111", "CreditAccount": "1121", "Amount": 100.0},
               {"DebitAccount": "1311", "CreditAccount": "1121", "Amount": 50.0,
                "CustomerCode": None}]
# có 632 nhưng chưa kết chuyển sang 911 -> C5.2 đỏ
CHUA_SAN_SANG = [{"DebitAccount": "632111", "CreditAccount": "1551", "Amount": 70.0}]


def _chay(rows, ctx):
    df = tao_df(rows)
    kq = checks.chay_tat_ca(df, ctx)
    return kq, tt.suy_trang_thai(df, {r.ma: r for r in kq})


def test_san_sang_khi_khong_con_gi(ctx):
    kl = tt.tinh_ket_luan(*_chay(SAN_SANG, ctx))
    assert kl["muc_do_ket_luan"] == tt.SAN_SANG and kl["san_sang"] is True
    assert kl["cau_ket_luan"] == "SẴN SÀNG KHÓA SỔ"
    assert kl["con_viec"] == 0 and kl["so_do"] == 0 and kl["so_vang"] == 0 and kl["so_can_ra"] == 0


def test_can_ra_soat_khi_chi_con_vang(ctx):
    """Băng xanh 'SẴN SÀNG' với 8 check vàng đang mở là kết luận sai."""
    kl = tt.tinh_ket_luan(*_chay(CAN_RA_SOAT, ctx))
    assert kl["muc_do_ket_luan"] == tt.CAN_RA_SOAT
    assert kl["san_sang"] is False              # còn việc -> không phải "sẵn sàng"
    assert kl["so_do"] == 0 and kl["so_chua_lam"] == 0
    assert kl["so_vang"] + kl["so_can_ra"] > 0
    assert kl["cau_ket_luan"] == f"CÒN {kl['con_viec']} MỤC CẦN RÀ SOÁT"
    assert kl["con_viec"] == kl["so_vang"] + kl["so_can_ra"]


def test_chua_san_sang_khi_con_do_hoac_chua_lam(ctx):
    kl = tt.tinh_ket_luan(*_chay(CHUA_SAN_SANG, ctx))
    assert kl["muc_do_ket_luan"] == tt.CHUA_SAN_SANG and kl["san_sang"] is False
    assert kl["cau_ket_luan"] == f"CHƯA SẴN SÀNG KHÓA SỔ — còn {kl['con_viec']} việc phải xử lý"
    assert kl["con_viec"] == kl["so_do"] + kl["so_chua_lam"] > 0


def test_tk_toan_bo_de_trong_khong_duoc_bao_san_sang(ctx, df_tk_null):
    """File mà mọi số hiệu TK đều trống chỉ trip C2.2 (vàng) — trước đây ra băng xanh."""
    kq = checks.chay_tat_ca(df_tk_null, ctx)
    kl = tt.tinh_ket_luan(kq, tt.suy_trang_thai(df_tk_null, {r.ma: r for r in kq}))
    assert kl["so_do"] == 0 and kl["so_vang"] > 0
    assert kl["muc_do_ket_luan"] == tt.CAN_RA_SOAT and kl["san_sang"] is False


def _xlsx(tmp_path, rows):
    p = tmp_path / "bk.xlsx"
    tao_df(rows).to_excel(p, sheet_name="Table1", index=False)
    return str(p)


@pytest.mark.parametrize("rows,muc_do", [(SAN_SANG, tt.SAN_SANG),
                                         (CAN_RA_SOAT, tt.CAN_RA_SOAT),
                                         (CHUA_SAN_SANG, tt.CHUA_SAN_SANG)])
def test_api_tra_ba_muc_ket_luan(tmp_path, rows, muc_do):
    kq = JsApi().chay_kiem_tra(_xlsx(tmp_path, rows))
    t = kq["tomtat"]
    assert t["muc_do_ket_luan"] == muc_do
    assert t["san_sang"] is (muc_do == tt.SAN_SANG)
    assert "so_can_ra" in t and t["con_viec"] == (
        t["so_do"] + t["so_chua_lam"] if muc_do == tt.CHUA_SAN_SANG
        else t["so_vang"] + t["so_can_ra"] if muc_do == tt.CAN_RA_SOAT else 0)


@pytest.mark.parametrize("rows,cau", [(SAN_SANG, "SẴN SÀNG KHÓA SỔ"),
                                      (CAN_RA_SOAT, "CẦN RÀ SOÁT"),
                                      (CHUA_SAN_SANG, "CHƯA SẴN SÀNG KHÓA SỔ")])
def test_bao_cao_excel_viet_dung_cau_ket_luan(tmp_path, ctx, rows, cau):
    kq, ts = _chay(rows, ctx)
    tt_file = ThongTinFile("x.xlsx", "x.xlsx", "08/2026", 8, 2026, len(rows), 0.0, [])
    path = report.xuat_bao_cao(kq, ts, tt_file, str(tmp_path))
    a3 = openpyxl.load_workbook(path)["Tong quan"]["A3"].value
    assert a3.startswith("Kết luận: ") and cau in a3


def test_api_va_bao_cao_luon_dong_y_nhau(tmp_path, ctx):
    """Hai chỗ kết luận phải dùng chung một hàm — lệch nhau là lỗi headline."""
    for rows in (SAN_SANG, CAN_RA_SOAT, CHUA_SAN_SANG):
        kq, ts = _chay(rows, ctx)
        kl = tt.tinh_ket_luan(kq, ts)
        api_kq = JsApi().chay_kiem_tra(_xlsx(tmp_path, rows))
        assert api_kq["tomtat"]["cau_ket_luan"] == kl["cau_ket_luan"]
        assert api_kq["tomtat"]["muc_do_ket_luan"] == kl["muc_do_ket_luan"]
