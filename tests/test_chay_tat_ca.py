from app import checks
from tests.conftest import tao_df


def test_chay_tat_ca_tra_30_check_va_bao_tien_trinh(ctx):
    goi = []
    kq = checks.chay_tat_ca(tao_df([{}]), ctx, on_progress=lambda ten, pct: goi.append((ten, pct)))
    assert len(kq) == 6 + 4 + 3 + 6 + 6 + 5
    assert {r.nhom for r in kq} == set(checks.TEN_NHOM)
    assert goi[0][1] == 0 and goi[-1] == ("Hoàn tất", 100)
    assert len({r.ma for r in kq}) == len(kq)  # mã không trùng
