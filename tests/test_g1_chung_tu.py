from app.checks import g1_chung_tu as g1
from tests.conftest import tao_df


def _kq(df, ctx):
    return {r.ma: r for r in g1.kiem_tra(df, ctx)}


def test_du_6_ma_theo_thu_tu(ctx):
    assert [r.ma for r in g1.kiem_tra(tao_df([{}]), ctx)] == ["C1.1", "C1.2", "C1.3", "C1.4", "C1.5", "C1.6", "C1.7"]


def test_c11_chung_tu_khong_co_dien_giai_nao(ctx):
    df = tao_df([{"DocNo": "A", "Description": None}, {"DocNo": "A", "Description": "  "},
                 {"DocNo": "B", "Description": "ok"}])
    assert _kq(df, ctx)["C1.1"].so_loi == 2          # cả chứng từ A đều trống


def test_c11_khong_bat_dong_thue_cua_hoa_don_da_co_dien_giai(ctx):
    """Dữ liệu thật: 10.308 dòng bị bắt ở A01/A02/A03, 100% là cặp 1311/33311 —
    dòng thuế GTGT của hóa đơn bán hàng. Nó không có tên vật tư (không phải dòng
    hàng) và Bravo không điền diễn giải, nhưng CHỨNG TỪ thì đã được mô tả ở dòng
    doanh thu. Không một chứng từ nào trong 8 chi nhánh thiếu diễn giải hoàn toàn."""
    df = tao_df([
        {"DocNo": "0045281", "DebitAccount": "1311", "CreditAccount": "5111",
         "Description": "Bán hàng theo HĐ 0045281"},
        {"DocNo": "0045281", "DebitAccount": "1311", "CreditAccount": "33311",
         "Description": None, "ItemName": None},                # dòng thuế -> KHÔNG báo
    ])
    assert _kq(df, ctx)["C1.1"].so_loi == 0


def test_c11_gom_theo_quyen_va_so_ct(ctx):
    """Hai quyển trùng số CT: phiếu trống không được núp bóng phiếu kia đã có mô tả."""
    df = tao_df([
        {"DocCode": "PC", "DocNo": "001", "Description": "Chi tiền mặt"},
        {"DocCode": "PN", "DocNo": "001", "Description": None, "ItemName": None},
    ])
    assert _kq(df, ctx)["C1.1"].so_loi == 1


def test_c11_item_name_duoc_tinh_la_dien_giai(ctx):
    """A3: Bravo để diễn giải ở cột tên vật tư — chỉ báo thiếu khi cả hai cột đều trống."""
    df = tao_df([
        {"DocNo": "A", "Description": None, "ItemName": "Trần nhựa nano P06 - 5.0kg"},
        {"DocNo": "B", "Description": "  ", "ItemName": "  "},
        {"DocNo": "B", "Description": None, "ItemName": None},
        {"DocNo": "C", "Description": "Thuế GTGT", "ItemName": None},
    ])
    kq = _kq(df, ctx)["C1.1"]
    assert kq.so_loi == 2                 # chỉ chứng từ B trống hoàn toàn
    assert kq.ghi_chu == g1.GHI_CHU_C11


def test_c12_ngay_ngoai_ky(ctx):
    df = tao_df([{"DocDate": "2026-07-31"}, {"DocDate": "2026-08-31"}, {"DocDate": "2026-09-01"}])
    kq = _kq(df, ctx)["C1.2"]
    assert kq.so_loi == 2 and kq.muc_do == "do"


def test_c13_nghi_trung(ctx):
    r = {"DocNo": "X", "DebitAccount": "6421", "CreditAccount": "1111", "Amount": 5, "Description": "a"}
    df = tao_df([r, r, {**r, "Amount": 6}])
    c13 = _kq(df, ctx)["C1.3"]
    assert c13.la_thong_ke is True and c13.so_loi == 0   # nghi trùng -> chỉ thống kê
    assert len(c13.chi_tiet) == 2                         # vẫn liệt kê 2 dòng trùng


def test_c14_no_bang_co(ctx):
    df = tao_df([{"DebitAccount": "1111", "CreditAccount": "1111"}, {}])
    assert _kq(df, ctx)["C1.4"].so_loi == 1


def test_c14_loai_tru_chung_tu_dieu_chuyen(ctx):
    """A2: điều chuyển kho/nội bộ (DC/LR/BN/BT) cùng TK hai vế là đúng nghiệp vụ."""
    rows = [{"DocCode": ma, "DebitAccount": "1561", "CreditAccount": "1561"}
            for ma in g1.DOC_DIEU_CHUYEN]
    rows.append({"DocCode": "PC", "DebitAccount": "1561", "CreditAccount": "1561"})   # còn lại -> báo
    kq = _kq(tao_df(rows), ctx)["C1.4"]
    assert kq.so_loi == 1
    assert kq.chi_tiet["ly_do"].iloc[0].endswith("(không tính chứng từ điều chuyển DC/LR/BN/BT)")
    assert "DC/LR/BN/BT" in kq.ghi_chu


def test_c14_bo_qua_khi_ca_hai_tk_deu_trong(ctx):
    """Hai vế cùng NaN không phải 'cùng một tài khoản'."""
    df = tao_df([{"DebitAccount": None, "CreditAccount": None}])
    assert _kq(df, ctx)["C1.4"].so_loi == 0


def test_c15_chi_do_khi_amount_bang_0(ctx):
    # Amount = 0 -> ĐỎ (dòng không giá trị). Amount < 0 -> KHÔNG kéo kết luận (là điều
    # chỉnh/kiểm kê hợp lệ), chuyển sang thống kê C1.7.
    df = tao_df([{"Amount": 0}, {"Amount": -1}, {"Amount": -2}, {"Amount": 5}])
    kq = _kq(df, ctx)
    assert kq["C1.5"].muc_do == "do" and kq["C1.5"].so_loi == 1        # chỉ dòng = 0


def test_c17_so_tien_am_la_thong_ke_khong_chan(ctx):
    df = tao_df([{"Amount": 0}, {"Amount": -1}, {"Amount": -2}, {"Amount": 5}])
    c17 = _kq(df, ctx)["C1.7"]
    assert c17.la_thong_ke is True and c17.so_loi == 0                 # không kéo kết luận
    assert len(c17.chi_tiet) == 2                                      # liệt kê 2 dòng âm


def test_c16_thieu_so_hoac_ngay(ctx):
    df = tao_df([{"DocNo": None}, {"DocDate": None}, {}])
    assert _kq(df, ctx)["C1.6"].so_loi == 2
