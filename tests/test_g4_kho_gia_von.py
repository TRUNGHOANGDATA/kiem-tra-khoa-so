from app.checks import g4_kho_gia_von as g4
from tests.conftest import tao_df


def _kq(df, ctx):
    return {r.ma: r for r in g4.kiem_tra(df, ctx)}


def test_du_6_ma(ctx):
    assert [r.ma for r in g4.kiem_tra(tao_df([{}]), ctx)] == [
        "C4.1", "C4.2", "C4.3", "C4.4", "C4.5", "C4.6"]


def test_c41_xuat_kho_gia_0(ctx):
    df = tao_df([
        {"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 10, "UnitCost": 0, "Amount": 0},
        {"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 10, "UnitCost": 5, "Amount": 50},
        {"DebitAccount": "6421", "CreditAccount": "1111", "Quantity9": 0, "UnitCost": 0, "Amount": 9},
    ])
    kq = _kq(df, ctx)["C4.1"]
    assert kq.so_loi == 1 and kq.muc_do_thuc == "do"
    assert kq.chi_tiet["Amount"].tolist() == [0]  # đúng dòng đầu tiên (giá 0) bị gắn cờ, không phải dòng thứ 2


def test_c41_khong_bao_khi_unitcost_0_nhung_amount_duong(ctx):
    """Hồi quy đúng nguyên nhân gốc: Bravo không ghi đơn giá trên dòng xuất kho
    (UnitCost=0) nhưng giá vốn bình quân cuối kỳ đã được ghi thẳng vào Amount —
    dòng này đã có giá trị, không được coi là "chưa tính giá xuất kho"."""
    df = tao_df([
        {"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 60, "UnitCost": 0, "Amount": 1_466_848},
    ])
    assert _kq(df, ctx)["C4.1"].so_loi == 0


def test_c41_bao_khi_amount_0_du_unitcost_0(ctx):
    """Cùng hình dạng dòng trên nhưng Amount = 0 — thật sự chưa có giá trị -> phải bắt."""
    df = tao_df([
        {"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 60, "UnitCost": 0, "Amount": 0},
    ])
    assert _kq(df, ctx)["C4.1"].so_loi == 1


def test_c41_tien_am_la_gia_tri_khong_phai_thieu_gia_tri(ctx):
    """Chốt vị từ mới: Amount == 0, KHÔNG phải Amount <= 0.

    10 dòng cuối C4.1 còn báo trên sổ 08/2026 đều là bút toán điều chỉnh âm
    (PX, Nợ 6214 / Có 1521, "TĐ từ phiếu TP số: TP2608-…", SL lẻ 0,16–2,429).
    Số tiền âm LÀ một giá trị — nói "chưa xác định giá trị" về chúng là sai.
    Cùng một dòng nhưng Amount = 0 thì mới thật sự chưa có giá trị và phải bị bắt.
    """
    am = tao_df([{"DebitAccount": "6214", "CreditAccount": "1521",
                  "Quantity9": 0.27, "UnitCost": 0, "Amount": -4638}])
    khong = tao_df([{"DebitAccount": "6214", "CreditAccount": "1521",
                     "Quantity9": 0.27, "UnitCost": 0, "Amount": 0}])
    assert _kq(am, ctx)["C4.1"].so_loi == 0
    assert _kq(khong, ctx)["C4.1"].so_loi == 1


def test_c41_ly_do_giu_so_luong_le(ctx):
    """SL 0,16 từng in ra "SL 0" — đọc thành "không có số lượng", đúng ngược với
    điều kiện đang báo ("có số lượng nhưng chưa có giá trị")."""
    df = tao_df([{"DebitAccount": "6214", "CreditAccount": "1521",
                  "Quantity9": 0.16, "UnitCost": 0, "Amount": 0}])
    ly_do = _kq(df, ctx)["C4.1"].chi_tiet["ly_do"].iloc[0]
    assert ly_do.startswith("Có SL 0,16 nhưng tiền = 0")


def test_nghi_chua_tinh_gia_khong_bao_tren_dong_dieu_chinh_am(ctx):
    """Quy tắc tỷ lệ hệ thống phải dùng cùng vị từ với C4.1: toàn bộ dòng xuất
    mang số tiền âm (điều chỉnh) không được kết luận "cả kỳ chưa chạy tính giá"."""
    df = tao_df([{"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 0.27,
                  "UnitCost": 0, "Amount": -4638} for _ in range(200)])
    assert g4.thong_ke_xuat_kho(df) == (0, 200)
    assert g4.nghi_chua_tinh_gia(df) is False
    assert _kq(df, ctx)["C4.1"].so_loi == 0 and _kq(df, ctx)["C4.1"].ghi_chu == ""


def test_c42_lech_tien_sl_x_don_gia(ctx):
    df = tao_df([
        {"CreditAccount": "1551", "Quantity9": 10, "UnitCost": 100.4, "Amount": 1004},
        {"CreditAccount": "1551", "Quantity9": 10, "UnitCost": 100, "Amount": 1500},
    ])
    c42 = _kq(df, ctx)["C4.2"]
    assert c42.la_thong_ke is True and len(c42.chi_tiet) == 1   # thống kê, vẫn liệt kê dòng lệch


def test_c41_c42_ghi_chu_khi_khong_co_du_lieu_sl(ctx):
    """File Bravo không có cột Quantity9/UnitCost — loader điền 0.0, không được báo xanh giả."""
    df = tao_df([{"DebitAccount": "6421", "CreditAccount": "1111", "Amount": 100}])
    kq41 = _kq(df, ctx)["C4.1"]
    kq42 = _kq(df, ctx)["C4.2"]
    assert kq41.so_loi == 0 and kq41.ghi_chu == g4.GHI_CHU_THIEU_SL
    assert kq42.so_loi == 0 and kq42.ghi_chu == g4.GHI_CHU_THIEU_SL


def dong_xuat(n, co_gia):
    """n dòng xuất kho có số lượng, có/không có đơn giá."""
    return [{"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 10,
             "UnitCost": 7 if co_gia else 0, "Amount": 70 if co_gia else 0} for _ in range(n)]


def test_c41_ghi_chu_chua_tinh_gia_khi_ty_le_dat_nguong(ctx):
    """A1: 80/100 dòng xuất không đơn giá = đúng ngưỡng 0,8 -> nghi chưa chạy tính giá."""
    df = tao_df(dong_xuat(80, False) + dong_xuat(20, True))
    kq = _kq(df, ctx)["C4.1"]
    assert kq.so_loi == 80 and kq.muc_do_thuc == "do"
    assert kq.ghi_chu == g4.GHI_CHU_CHUA_TINH_GIA


def test_c41_khong_ghi_chu_khi_ty_le_duoi_nguong(ctx):
    """79/100 = 0,79 < 0,8 -> chỉ là các dòng sót, không phải cả kỳ chưa tính giá."""
    df = tao_df(dong_xuat(79, False) + dong_xuat(21, True))
    kq = _kq(df, ctx)["C4.1"]
    assert kq.so_loi == 79 and kq.ghi_chu == ""


def test_c41_it_dong_thi_khong_ket_luan_theo_ty_le(ctx):
    """Dưới SO_DONG_XUAT_TOI_THIEU, tỷ lệ 100% cũng không đủ căn cứ."""
    df = tao_df(dong_xuat(g4.SO_DONG_XUAT_TOI_THIEU - 1, False))
    kq = _kq(df, ctx)["C4.1"]
    assert kq.so_loi == g4.SO_DONG_XUAT_TOI_THIEU - 1 and kq.ghi_chu == ""


def test_nghi_chua_tinh_gia_khong_bao_khi_co_gia_tri_du_khong_co_don_gia(ctx):
    """Rebase trên Amount: toàn bộ dòng xuất không có UnitCost nhưng đều có Amount
    dương (đúng hình dạng dữ liệu thật của Bravo) không được kết luận "nghi chưa
    chạy tính giá" — vì giá trị đã được xác định, chỉ là không restated đơn giá."""
    df = tao_df([{"DebitAccount": "6214", "CreditAccount": "1521", "Quantity9": 10,
                  "UnitCost": 0, "Amount": 264_000} for _ in range(200)])
    assert g4.thong_ke_xuat_kho(df) == (0, 200)
    assert g4.nghi_chua_tinh_gia(df) is False
    kq = _kq(df, ctx)["C4.1"]
    assert kq.so_loi == 0 and kq.ghi_chu == ""


def test_thong_ke_xuat_kho_chi_dem_dong_xuat(ctx):
    """Dòng nhập mang giá mua — gộp vào mẫu số sẽ pha loãng tỷ lệ."""
    df = tao_df(dong_xuat(90, False) + dong_xuat(10, True)
                + [{"DebitAccount": "1521", "CreditAccount": "3311", "Quantity9": 10,
                    "UnitCost": 7, "Amount": 70}] * 500)
    assert g4.thong_ke_xuat_kho(df) == (90, 100)
    assert g4.nghi_chua_tinh_gia(df) is True


def test_c43_gia_von_khong_di_kem_kho(ctx):
    df = tao_df([
        {"DebitAccount": "632111", "CreditAccount": "1551"},
        {"DebitAccount": "632111", "CreditAccount": "3311"},
    ])
    assert _kq(df, ctx)["C4.3"].so_loi == 1


def test_c44_chua_tap_hop_chi_phi_ve_154(ctx):
    df = tao_df([
        {"DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100},
        {"DebitAccount": "154", "CreditAccount": "6214", "Amount": 100},
        {"DebitAccount": "6221", "CreditAccount": "3341", "Amount": 50},     # 622 chưa kết chuyển
    ])
    kq = _kq(df, ctx)["C4.4"]
    assert kq.so_loi == 1 and kq.chi_tiet["TK"].iloc[0] == "622" and kq.muc_do_thuc == "do"


def test_c44_khong_ap_dung_khi_khong_phat_sinh(ctx):
    assert _kq(tao_df([{}]), ctx)["C4.4"].so_loi == 0


def test_c44_ket_chuyen_mot_phan_ve_154(ctx):
    """621 mới kết chuyển 40/100 — còn dở dang 60, phải bị báo dù đã có bút toán Nợ 154 / Có 621."""
    df = tao_df([
        {"DebitAccount": "6211", "CreditAccount": "1521", "Amount": 100},
        {"DebitAccount": "154", "CreditAccount": "6211", "Amount": 40},
    ])
    kq = _kq(df, ctx)["C4.4"]
    assert kq.so_loi == 1
    row = kq.chi_tiet.iloc[0]
    assert row["TK"] == "621" and "60" in row["ly_do"]


def test_c45_chua_nhap_kho_thanh_pham(ctx):
    co = tao_df([{"DebitAccount": "154", "CreditAccount": "6214"},
                 {"DebitAccount": "1551", "CreditAccount": "154"}])
    thieu = tao_df([{"DebitAccount": "154", "CreditAccount": "6214"}])
    assert _kq(co, ctx)["C4.5"].so_loi == 0
    assert _kq(thieu, ctx)["C4.5"].so_loi == 1


def test_c45_chap_nhan_ban_thang_va_gui_ban(ctx):
    """154 -> 632 (bán thẳng) và 154 -> 157 (gửi bán) cũng là hoàn tất, không chỉ 154 -> 155."""
    ban_thang = tao_df([{"DebitAccount": "154", "CreditAccount": "6214"},
                        {"DebitAccount": "632", "CreditAccount": "154"}])
    gui_ban = tao_df([{"DebitAccount": "154", "CreditAccount": "6214"},
                      {"DebitAccount": "157", "CreditAccount": "154"}])
    assert _kq(ban_thang, ctx)["C4.5"].so_loi == 0
    assert _kq(gui_ban, ctx)["C4.5"].so_loi == 0


def test_so_sach_sach_thi_xanh(ctx):
    df = tao_df([{}])
    kq = _kq(df, ctx)
    assert all(kq[ma].muc_do_thuc == "xanh" for ma in ["C4.1", "C4.2", "C4.3", "C4.4", "C4.5"])


# ============================ C4.6 — đơn giá xuất kho ============================
def _xuat(ma: str, sl: float, tien: float, **kw) -> dict:
    """Một dòng xuất kho (Có TK kho) của mã hàng `ma`."""
    return {"DebitAccount": "6214", "CreditAccount": "1521", "ItemCode": ma,
            "ItemName": f"Hàng {ma}" if ma else None,
            "Quantity9": sl, "Amount": tien, **kw}


def _c46(rows, ctx):
    return g4.don_gia_bat_thuong(tao_df(rows))


def test_c46_bat_don_gia_gap_nhieu_lan_mat_bang(ctx):
    """Mặt bằng của mã A là 10.000/đơn vị; một dòng ra 1.000.000 là gấp 100 lần."""
    rows = [_xuat("A", 10, 100_000) for _ in range(5)]
    rows.append(_xuat("A", 1, 1_000_000, DocNo="LECH"))
    kq = _c46(rows, ctx)
    assert kq.so_loi == 1
    r = kq.chi_tiet.iloc[0]
    assert r["DocNo"] == "LECH" and r["don_gia"] == 1_000_000 and r["don_gia_pho_bien"] == 10_000
    assert "gấp 100 lần" in r["ly_do"] and r["so_lan_xuat"] == 6


def test_c46_bat_ca_chieu_don_gia_qua_thap(ctx):
    rows = [_xuat("A", 1, 10_000) for _ in range(5)]
    rows.append(_xuat("A", 1000, 10_000, DocNo="RE"))
    kq = _c46(rows, ctx)
    assert kq.so_loi == 1
    assert "chỉ bằng 1/1.000" in kq.chi_tiet.iloc[0]["ly_do"]


def test_c46_trong_nguong_thi_khong_bao(ctx):
    """Chênh 9 lần vẫn dưới ngưỡng 10 — giá vốn bình quân dao động là chuyện thường."""
    rows = [_xuat("A", 1, 10_000) for _ in range(5)] + [_xuat("A", 1, 90_000)]
    assert _c46(rows, ctx).so_loi == 0


def test_c46_bo_qua_ma_hang_it_lan_xuat_va_noi_ro(ctx):
    """Mã hàng xuất 1-2 lần chưa có mặt bằng để so. TSCĐ 2,3 tỷ/đơn vị xuất đúng
    một lần trong kỳ là hợp lệ — không được gọi là bất thường chỉ vì số to."""
    rows = [_xuat("TSCD", 1, 2_347_789_345), _xuat("TSCD", 1, 10_000)]
    kq = _c46(rows, ctx)
    assert kq.so_loi == 0
    assert "2 dòng chưa đủ cơ sở so sánh" in kq.ghi_chu


def test_c46_moi_ma_hang_so_voi_mat_bang_cua_chinh_no(ctx):
    """Mã B đắt gấp 1.000 lần mã A nhưng nhất quán với chính nó -> không phải lỗi."""
    rows = ([_xuat("A", 1, 1_000) for _ in range(3)]
            + [_xuat("B", 1, 1_000_000) for _ in range(3)])
    assert _c46(rows, ctx).so_loi == 0


def test_c46_dung_trung_vi_khong_dung_trung_binh(ctx):
    """Một dòng lệch 251 lần kéo trung bình lên theo mình rồi tự che mất —
    trung vị thì không."""
    rows = [_xuat("A", 1, 1_000) for _ in range(4)] + [_xuat("A", 1, 251_000, DocNo="X")]
    kq = _c46(rows, ctx)
    assert kq.so_loi == 1 and kq.chi_tiet.iloc[0]["DocNo"] == "X"


def test_c46_bo_qua_dong_nhap_kho(ctx):
    """Chỉ soi dòng XUẤT (Có TK kho): dòng nhập mang giá mua, không phải giá vốn tính ra."""
    rows = ([_xuat("A", 1, 1_000) for _ in range(3)]
            + [{"DebitAccount": "1521", "CreditAccount": "331", "ItemCode": "A",
                "Quantity9": 1, "Amount": 900_000}])
    assert _c46(rows, ctx).so_loi == 0


def test_c46_bo_qua_dong_khong_co_ma_hang_hoac_khong_co_tien(ctx):
    rows = ([_xuat("A", 1, 1_000) for _ in range(3)]
            + [_xuat(None, 1, 900_000), _xuat("A", 1, 0), _xuat("A", 0, 900_000)])
    assert _c46(rows, ctx).so_loi == 0


def test_c46_frame_rong_khong_no(ctx):
    kq = _c46([], ctx)
    assert kq.so_loi == 0 and kq.muc_do_thuc == "xanh"
    assert list(kq.chi_tiet.columns) == g4.COT_C46


def test_c46_la_canh_bao_khong_phai_nghiem_trong(ctx):
    rows = [_xuat("A", 10, 100_000) for _ in range(5)] + [_xuat("A", 1, 1_000_000)]
    assert _c46(rows, ctx).muc_do_thuc == "vang"


# ------------------------------------------------ C4.6 gợi ý bội số tròn
def test_c46_boi_so_tron_goi_y_sai_don_vi_tinh(ctx):
    """Lệch đúng bội số nguyên = nghi sai đơn vị tính, không phải biến động giá.

    Trên sổ 08/2026 A01 có 5 mã rơi đúng vào ×75/×40/×25 (tròn tới 4 chữ số thập phân).
    """
    rows = [{"DebitAccount": "632", "CreditAccount": "1561", "ItemCode": "H1",
             "Quantity9": 10, "Amount": 1_000} for _ in range(4)]
    rows.append({"DebitAccount": "632", "CreditAccount": "1561", "ItemCode": "H1",
                 "Quantity9": 1, "Amount": 7_500, "DocNo": "SAI"})   # 7.500 = 75 × 100
    r = g4.don_gia_bat_thuong(tao_df(rows))
    assert r.so_loi == 1 and r.chi_tiet.iloc[0]["DocNo"] == "SAI"
    assert "bội số nguyên" in r.chi_tiet.iloc[0]["ly_do"] and "75" in r.chi_tiet.iloc[0]["ly_do"]


def test_c46_lech_so_le_khong_goi_y_boi_so(ctx):
    """Lệch 13,7 lần (số lẻ) thì không được gợi ý sai đơn vị tính."""
    rows = [{"DebitAccount": "632", "CreditAccount": "1561", "ItemCode": "H2",
             "Quantity9": 10, "Amount": 1_000} for _ in range(4)]
    rows.append({"DebitAccount": "632", "CreditAccount": "1561", "ItemCode": "H2",
                 "Quantity9": 10, "Amount": 13_700})
    r = g4.don_gia_bat_thuong(tao_df(rows))
    assert r.so_loi == 1 and "bội số nguyên" not in r.chi_tiet.iloc[0]["ly_do"]
