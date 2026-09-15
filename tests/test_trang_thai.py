from app import checks, trang_thai as tt
from tests.conftest import tao_df


def _suy(df, ctx):
    kq = {r.ma: r for r in checks.chay_tat_ca(df, ctx)}
    return {b.buoc: b for b in tt.suy_trang_thai(df, kq)}, tt.suy_trang_thai(df, kq)


def test_du_11_buoc_dung_thu_tu(ctx):
    _, ds = _suy(tao_df([{}]), ctx)
    assert len(ds) == 11
    assert ds[0].buoc.startswith("Tập hợp CP NVL") and ds[-1].buoc.startswith("TK đầu 5/6/7/8")


def test_khong_phat_sinh_thi_khong_ap_dung(ctx):
    b, _ = _suy(tao_df([{"DebitAccount": "1111", "CreditAccount": "1121"}]), ctx)
    assert b["Tập hợp CP NVL trực tiếp 621 → 154"].trang_thai == tt.KHONG_AP_DUNG
    assert b["Kết chuyển giá vốn 632 → 911"].trang_thai == tt.KHONG_AP_DUNG


def test_621_da_lam_can_ra_chua_lam(ctx):
    da = tao_df([{"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100},
                 {"DebitAccount": "154", "CreditAccount": "6214", "Amount": 100}])
    ra = tao_df([{"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100},
                 {"DebitAccount": "154", "CreditAccount": "6214", "Amount": 60}])
    chua = tao_df([{"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100}])
    k = "Tập hợp CP NVL trực tiếp 621 → 154"
    assert _suy(da, ctx)[0][k].trang_thai == tt.DA_LAM
    assert _suy(ra, ctx)[0][k].trang_thai == tt.CAN_RA and "40" in _suy(ra, ctx)[0][k].tom_tat
    assert _suy(chua, ctx)[0][k].trang_thai == tt.CHUA_LAM and b_ma(_suy(chua, ctx)[0][k]) == "C4.4"


def b_ma(b):
    return b.ma_check


def test_xuat_kho_gia_va_tk_pl_ve_0(ctx):
    df = tao_df([{"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 1, "UnitCost": 0, "Amount": 0},
                 {"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 10}])
    b, _ = _suy(df, ctx)
    assert b["Xuất kho có đầy đủ giá"].trang_thai == tt.CAN_RA
    assert b["TK đầu 5/6/7/8 đã về 0 (kết chuyển hết)"].trang_thai == tt.CAN_RA


def test_lai_lo_va_thue(ctx):
    df = tao_df([{"DebitAccount": "911", "CreditAccount": "6421"},
                 {"DebitAccount": "911", "CreditAccount": "4212"},
                 {"DebitAccount": "1331", "CreditAccount": "3311"},
                 {"DebitAccount": "1311", "CreditAccount": "33311"}])
    b, _ = _suy(df, ctx)
    assert b["Kết chuyển lãi/lỗ 911 ↔ 421"].trang_thai == tt.DA_LAM
    assert b["Khấu trừ thuế GTGT 3331 ↔ 1331"].trang_thai == tt.CHUA_LAM


def test_vat_bare_3331_da_lam_va_chua_lam(ctx):
    """F3: check C5.6 dùng prefix '3331' (khớp cả sub-account 33311), step 9 phải khớp theo."""
    co_bu_tru = tao_df([{"DebitAccount": "1331", "CreditAccount": "3311", "Amount": 500},
                        {"DebitAccount": "1311", "CreditAccount": "3331", "Amount": 500},
                        {"DebitAccount": "3331", "CreditAccount": "1331", "Amount": 500}])
    khong_bu_tru = tao_df([{"DebitAccount": "1331", "CreditAccount": "3311", "Amount": 500},
                           {"DebitAccount": "1311", "CreditAccount": "3331", "Amount": 500}])
    k = "Khấu trừ thuế GTGT 3331 ↔ 1331"
    assert _suy(co_bu_tru, ctx)[0][k].trang_thai == tt.DA_LAM
    assert _suy(khong_bu_tru, ctx)[0][k].trang_thai == tt.CHUA_LAM


def test_622_va_627_da_lam(ctx):
    """F7: bao phủ bước 2 (622 → 154) và bước 3 (627 → 154), trước đây không có assertion."""
    df = tao_df([{"DebitAccount": "6221", "CreditAccount": "3341", "Amount": 100},
                 {"DebitAccount": "154", "CreditAccount": "6221", "Amount": 100},
                 {"DebitAccount": "6271", "CreditAccount": "2141", "Amount": 50},
                 {"DebitAccount": "154", "CreditAccount": "6271", "Amount": 50}])
    b, _ = _suy(df, ctx)
    assert b["Tập hợp CP nhân công trực tiếp 622 → 154"].trang_thai == tt.DA_LAM
    assert b["Tập hợp & phân bổ CP SXC 627 → 154"].trang_thai == tt.DA_LAM


def test_154_dong_qua_632_va_157_da_lam(ctx):
    """F4/F7: bước 4 chấp nhận Nợ 632 hoặc Nợ 157 (không chỉ 155) đối ứng Có 154."""
    qua_632 = tao_df([{"DebitAccount": "154", "CreditAccount": "621", "Amount": 100},
                      {"DebitAccount": "632", "CreditAccount": "154", "Amount": 100}])
    qua_157 = tao_df([{"DebitAccount": "154", "CreditAccount": "622", "Amount": 50},
                      {"DebitAccount": "157", "CreditAccount": "154", "Amount": 50}])
    k = "Nhập kho thành phẩm 154 → 155 (tính giá thành)"
    assert _suy(qua_632, ctx)[0][k].trang_thai == tt.DA_LAM
    assert _suy(qua_157, ctx)[0][k].trang_thai == tt.DA_LAM


def test_nhom_ve_911_con_lai_thi_can_ra(ctx):
    """F1/F7: đóng một phần doanh thu/chi phí về 911 phải báo can_ra kèm số tiền còn lại."""
    doanh_thu_du = tao_df([{"DebitAccount": "1311", "CreditAccount": "511", "Amount": 1_000_000_000},
                           {"DebitAccount": "511", "CreditAccount": "911", "Amount": 600_000_000}])
    chi_phi_du = tao_df([{"DebitAccount": "642", "CreditAccount": "1111", "Amount": 1000},
                         {"DebitAccount": "911", "CreditAccount": "642", "Amount": 700}])
    b_dt, _ = _suy(doanh_thu_du, ctx)
    b_cp, _ = _suy(chi_phi_du, ctx)
    kdt = "Kết chuyển doanh thu 511/515/711 → 911"
    kcp = "Kết chuyển chi phí 635/641/642/811 → 911"
    assert b_dt[kdt].trang_thai == tt.CAN_RA and "400.000.000" in b_dt[kdt].tom_tat
    assert b_cp[kcp].trang_thai == tt.CAN_RA and "300" in b_cp[kcp].tom_tat


def test_nhom_ve_911_dong_het_thi_da_lam(ctx):
    """F1/F7: đảo ngược chiều kiểm tra (Nợ/Có) trong _nhom_ve_911 phải làm test này fail."""
    doanh_thu_het = tao_df([{"DebitAccount": "1311", "CreditAccount": "511", "Amount": 1000},
                            {"DebitAccount": "511", "CreditAccount": "911", "Amount": 1000}])
    chi_phi_het = tao_df([{"DebitAccount": "642", "CreditAccount": "1111", "Amount": 500},
                          {"DebitAccount": "911", "CreditAccount": "642", "Amount": 500}])
    b_dt, _ = _suy(doanh_thu_het, ctx)
    b_cp, _ = _suy(chi_phi_het, ctx)
    assert b_dt["Kết chuyển doanh thu 511/515/711 → 911"].trang_thai == tt.DA_LAM
    assert b_cp["Kết chuyển chi phí 635/641/642/811 → 911"].trang_thai == tt.DA_LAM


def test_c41_co_ghi_chu_thi_khong_ap_dung(ctx):
    """F2/F7: C4.1 không kiểm tra được (thiếu dữ liệu số lượng) phải báo không_áp_dụng, không phải đã làm."""
    df = tao_df([{"DebitAccount": "155", "CreditAccount": "154", "Amount": 100}])
    b, _ = _suy(df, ctx)
    buoc = b["Xuất kho có đầy đủ giá"]
    assert buoc.trang_thai == tt.KHONG_AP_DUNG
    assert "không kiểm tra được" in buoc.tom_tat


def test_thieu_ket_qua_kiem_tra_thi_khong_ap_dung(ctx):
    """F5/F7: nếu ket_qua không có C4.1/C5.1 (chưa chạy kiểm tra), không được coi là đã làm."""
    df = tao_df([{}])
    b = {buoc.buoc: buoc for buoc in tt.suy_trang_thai(df, {})}
    assert b["Xuất kho có đầy đủ giá"].trang_thai == tt.KHONG_AP_DUNG
    assert b["TK đầu 5/6/7/8 đã về 0 (kết chuyển hết)"].trang_thai == tt.KHONG_AP_DUNG
