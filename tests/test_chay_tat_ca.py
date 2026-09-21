from app import checks
from tests.conftest import tao_df


def test_chay_tat_ca_tra_60_check_va_bao_tien_trinh(ctx):
    goi = []
    kq = checks.chay_tat_ca(tao_df([{}]), ctx, on_progress=lambda ten, pct: goi.append((ten, pct)))
    #          G1  G2  G3  G4  G5  G6  G7  G8  G9  G10 G11   (G10 có 8 từ khi tách C10.8)
    assert len(kq) == 7 + 4 + 3 + 6 + 6 + 7 + 7 + 3 + 5 + 8 + 4
    assert {r.nhom for r in kq} == set(checks.TEN_NHOM)
    assert goi[0][1] == 0 and goi[-1] == ("Hoàn tất", 100)
    assert len({r.ma for r in kq}) == len(kq)  # mã không trùng
