from app import cap_nhat as cn


def test_moi_hon_theo_tung_so():
    assert cn.moi_hon("1.1.4", "1.1.3") is True
    assert cn.moi_hon("1.2.0", "1.1.9") is True
    assert cn.moi_hon("1.1.3", "1.1.3") is False
    assert cn.moi_hon("1.1.2", "1.1.3") is False


def test_moi_hon_bo_tien_to_v_va_do_dai_lech():
    assert cn.moi_hon("v1.2.0", "1.1.5") is True      # có 'v'
    assert cn.moi_hon("1.2", "1.1.9") is True          # thiếu số cuối -> (1,2) > (1,1,9)
    assert cn.moi_hon("1.2.0", "1.2") is False         # (1,2,0) == (1,2,0)
