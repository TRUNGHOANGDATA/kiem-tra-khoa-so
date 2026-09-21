"""Nhiều chi nhánh & nhiều file bảng kê.

Quy tắc trung tâm: đơn vị kiểm tra là CHI NHÁNH, suy từ cột BranchCode — không
phải file. Một file có thể chứa nhiều chi nhánh; một chi nhánh có thể trải trên
nhiều file. 30 bộ kiểm tra và 11 bước luôn chạy trên sổ của riêng một chi nhánh,
vì kết chuyển của chi nhánh này không bù được phần thiếu của chi nhánh kia.
"""
import pandas as pd
import pytest

from app.api import JsApi
from app.loader import (CHI_NHANH_KHONG_RO, doc_nhieu_bang_ke, tach_theo_chi_nhanh,
                        tim_file_excel)
from tests.conftest import tao_df


def _ghi(tmp_path, ten: str, rows: list[dict]) -> str:
    """Ghi một bảng kê nhỏ ra .xlsx — mỗi dict chỉ nêu cột khác mặc định."""
    df = tao_df(rows)
    p = tmp_path / ten
    df.to_excel(p, index=False)
    return str(p)


# ---------------------------------------------------------------- tách chi nhánh
def test_tach_mot_file_thanh_nhieu_chi_nhanh():
    df = tao_df([{"BranchCode": "A01"}, {"BranchCode": "B02"}, {"BranchCode": "A01"}])
    ds = tach_theo_chi_nhanh(df)
    assert [(cn, len(con)) for cn, con in ds] == [("A01", 2), ("B02", 1)]


def test_dong_thieu_ma_chi_nhanh_khong_bien_mat():
    """Dòng không có mã chi nhánh vẫn phải thuộc một đơn vị — bỏ rơi chúng là để
    phát sinh biến mất khỏi mọi kiểm tra mà không một dòng cảnh báo nào."""
    df = tao_df([{"BranchCode": "A01"}, {"BranchCode": None}, {"BranchCode": "  "}])
    ds = dict((cn, len(con)) for cn, con in tach_theo_chi_nhanh(df))
    assert ds == {"A01": 1, CHI_NHANH_KHONG_RO: 2}
    assert sum(ds.values()) == 3


def test_khong_co_cot_chi_nhanh_van_chay_duoc():
    df = tao_df([{}, {}]).drop(columns=["BranchCode"], errors="ignore")
    assert [(cn, len(con)) for cn, con in tach_theo_chi_nhanh(df)] == [(CHI_NHANH_KHONG_RO, 2)]


# ----------------------------------------------------------------- đọc nhiều file
def test_gop_cung_chi_nhanh_tu_hai_file(tmp_path):
    a = _ghi(tmp_path, "a.xlsx", [{"BranchCode": "A01", "Amount": 100.0}])
    b = _ghi(tmp_path, "b.xlsx", [{"BranchCode": "A01", "Amount": 250.0}])
    ds = doc_nhieu_bang_ke([a, b])
    assert len(ds) == 1
    df, tt = ds[0]
    assert len(df) == 2 and tt.chi_nhanh == "A01"
    assert tt.tong_ps == 350.0
    assert sorted(tt.cac_file) == ["a.xlsx", "b.xlsx"]


def test_mot_file_hai_chi_nhanh_thanh_hai_don_vi(tmp_path):
    p = _ghi(tmp_path, "gop.xlsx", [{"BranchCode": "A01"}, {"BranchCode": "B02"},
                                    {"BranchCode": "B02"}])
    ds = doc_nhieu_bang_ke([p])
    assert [(tt.chi_nhanh, tt.so_dong) for _, tt in ds] == [("A01", 1), ("B02", 2)]
    assert all(tt.cac_file == ["gop.xlsx"] for _, tt in ds)


def test_file_trung_duong_dan_khong_nhan_doi_phat_sinh(tmp_path):
    """Chọn nhầm cùng một file hai lần không được nhân đôi phát sinh của cả chi
    nhánh — sai số đó không lộ ra ở đâu cho tới lúc đối chiếu với sổ cái."""
    p = _ghi(tmp_path, "a.xlsx", [{"BranchCode": "A01", "Amount": 100.0}])
    ds = doc_nhieu_bang_ke([p, p, p])
    assert len(ds) == 1
    _, tt = ds[0]
    assert tt.so_dong == 1 and tt.tong_ps == 100.0
    assert any("trùng" in m for m in tt.nhat_ky)


def test_doc_nhieu_khong_co_file_nao_bao_loi():
    with pytest.raises(ValueError, match="Chưa chọn file"):
        doc_nhieu_bang_ke([])


def test_ky_suy_rieng_cho_tung_chi_nhanh(tmp_path):
    p = _ghi(tmp_path, "hai-ky.xlsx", [{"BranchCode": "A01", "DocDate": "2026-08-10"},
                                       {"BranchCode": "B02", "DocDate": "2026-07-10"}])
    ds = doc_nhieu_bang_ke([p])
    assert [(tt.chi_nhanh, tt.ky) for _, tt in ds] == [("A01", "08/2026"), ("B02", "07/2026")]


def test_tim_file_excel_bo_qua_file_tam_cua_excel(tmp_path):
    _ghi(tmp_path, "that.xlsx", [{}])
    (tmp_path / "~$that.xlsx").write_text("rac", encoding="utf-8")
    (tmp_path / "ghi-chu.txt").write_text("rac", encoding="utf-8")
    assert [p.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]
            for p in tim_file_excel(str(tmp_path))] == ["that.xlsx"]


# ------------------------------------------------------------------------- JsApi
def _api_hai_chi_nhanh(tmp_path) -> JsApi:
    p = _ghi(tmp_path, "gop.xlsx", [
        {"BranchCode": "A01", "DocNo": "A1", "Description": None},
        {"BranchCode": "B02", "DocNo": "B1"},
        {"BranchCode": "B02", "DocNo": "B2", "Description": None},
    ])
    api = JsApi()
    api.thu_muc_report = str(tmp_path / "out")
    api.nap_nhieu_file([p])
    return api


def test_quy_doi_ten_hien_khong_dung_ma_goc(tmp_path):
    """Quy đổi chỉ đổi tên HIỂN THỊ (ten_hien / chi_nhanh_ten); mã gốc vẫn nguyên
    làm danh tính — đây là điều giữ cho chốt sổ/đối chiếu kỳ cũ không vỡ."""
    api = _api_hai_chi_nhanh(tmp_path)
    api._quy_doi = {"A01": "Nhà máy Hải Phòng"}   # gán đè (thắng cấu hình)
    kq = api.chay_kiem_tra()
    dv = kq["don_vi"]
    assert [u["ma"] for u in dv] == ["A01", "B02"]                 # mã gốc: KHÔNG đổi
    assert dv[0]["ten_hien"] == "Nhà máy Hải Phòng"
    assert dv[1]["ten_hien"] == "B02"                              # chưa quy đổi -> về mã
    assert kq["tomtat"]["chi_nhanh"] == "A01"                      # danh tính giữ nguyên
    assert kq["tomtat"]["chi_nhanh_ten"] == "Nhà máy Hải Phòng"


def test_moi_chi_nhanh_co_ket_qua_rieng(tmp_path):
    api = _api_hai_chi_nhanh(tmp_path)
    kq = api.chay_kiem_tra()
    assert [u["ma"] for u in kq["don_vi"]] == ["A01", "B02"]
    assert kq["dang_xem"] == 0 and kq["tomtat"]["chi_nhanh"] == "A01"
    # C1.1 (thiếu diễn giải) đếm riêng từng chi nhánh: 1 dòng ở A01, 1 dòng ở B02
    assert api._dv[0].kq["C1.1"].so_loi == 1
    assert api._dv[1].kq["C1.1"].so_loi == 1
    assert api._dv[0].df is not api._dv[1].df


def test_chon_don_vi_doi_toan_bo_ket_qua_dang_xem(tmp_path):
    api = _api_hai_chi_nhanh(tmp_path)
    api.chay_kiem_tra()
    kq = api.chon_don_vi(1)
    assert kq["tomtat"]["chi_nhanh"] == "B02" and kq["dang_xem"] == 1
    assert kq["tomtat"]["so_dong"] == 2
    # lay_chi_tiet bám theo chi nhánh đang xem, không trả dòng của chi nhánh khác
    ct = api.lay_chi_tiet("C1.1")
    assert ct["tong"] == 1 and ct["dong"][0]["DocNo"] == "B2"


def test_chon_don_vi_ngoai_pham_vi_bao_loi(tmp_path):
    api = _api_hai_chi_nhanh(tmp_path)
    api.chay_kiem_tra()
    assert api.chon_don_vi(5)["loi"] == "Không có chi nhánh này"
    assert api.chon_don_vi(-1)["loi"] == "Không có chi nhánh này"
    assert "loi" in api.chon_don_vi("x")
    assert api._i == 0     # lựa chọn hỏng không được đổi chi nhánh đang xem


def test_chay_kiem_tra_nhan_ca_danh_sach_duong_dan(tmp_path):
    """Màn hình 1 gửi lại CẢ danh sách đường dẫn; nhận mỗi file đầu rồi nạp lại
    một mình nó sẽ lặng lẽ vứt mất các chi nhánh còn lại."""
    a = _ghi(tmp_path, "a.xlsx", [{"BranchCode": "A01"}])
    b = _ghi(tmp_path, "b.xlsx", [{"BranchCode": "B02"}])
    api = JsApi()
    kq = api.chay_kiem_tra([a, b])
    assert [u["ma"] for u in kq["don_vi"]] == ["A01", "B02"]


def test_chay_kiem_tra_lan_2_cung_danh_sach_khong_doc_lai(tmp_path, monkeypatch):
    import app.api as api_module
    a = _ghi(tmp_path, "a.xlsx", [{"BranchCode": "A01"}])
    b = _ghi(tmp_path, "b.xlsx", [{"BranchCode": "B02"}])
    goc, so_lan = api_module.doc_nhieu_bang_ke, []

    def dem(paths, on_file=None):
        so_lan.append(list(paths))
        return goc(paths, on_file=on_file)

    monkeypatch.setattr(api_module, "doc_nhieu_bang_ke", dem)
    api = JsApi()
    api.chay_kiem_tra([a, b])
    api.chay_kiem_tra([a, b])
    assert len(so_lan) == 1


def test_quet_thu_muc_nap_moi_bang_ke(tmp_path):
    _ghi(tmp_path, "cn-a.xlsx", [{"BranchCode": "A01"}])
    _ghi(tmp_path, "cn-b.xlsx", [{"BranchCode": "B02"}])
    api = JsApi()
    api.thu_muc_source = str(tmp_path)
    info = api.quet_thu_muc()
    assert info["so_file"] == 2
    assert [u["ma"] for u in info["don_vi"]] == ["A01", "B02"]


def test_quet_thu_muc_rong_bao_loi_ro_rang(tmp_path):
    api = JsApi()
    api.thu_muc_source = str(tmp_path)
    assert "chưa có file" in api.quet_thu_muc()["loi"]


def test_nap_nhieu_file_danh_sach_rong(tmp_path):
    assert JsApi().nap_nhieu_file([])["loi"] == "Chưa chọn file bảng kê nào"


# ------------------------------------------------------------------------ báo cáo
def test_xuat_tong_hop_co_sheet_cho_tung_chi_nhanh(tmp_path):
    import openpyxl
    api = _api_hai_chi_nhanh(tmp_path)
    api.chay_kiem_tra()
    kq = api.xuat_tong_hop()
    assert "loi" not in kq
    ten = openpyxl.load_workbook(kq["path"], read_only=True).sheetnames
    # Khung cố định: so sánh chi nhánh -> danh sách lỗi phẳng -> cặp tab mỗi chi nhánh.
    # Sau đó là các sheet chi tiết đặt theo MÃ CHECK, tùy dữ liệu có lỗi gì nên không
    # khẳng định cứng ở đây (đã có test riêng trong test_report.py).
    assert ten[:6] == ["Tong hop chi nhanh", "Danh sach loi",
                       "A01 - TQ", "A01 - KS", "B02 - TQ", "B02 - KS"]
    assert all(t.startswith("C") for t in ten[6:]), ten[6:]


def test_xuat_tong_hop_doi_chay_kiem_tra_truoc(tmp_path):
    api = _api_hai_chi_nhanh(tmp_path)
    assert "Chưa chạy kiểm tra" in api.xuat_tong_hop()["loi"]


def test_bao_cao_tung_chi_nhanh_co_ten_file_rieng(tmp_path):
    api = _api_hai_chi_nhanh(tmp_path)
    api.chay_kiem_tra()
    a = api.xuat_bao_cao()["path"]
    api.chon_don_vi(1)
    b = api.xuat_bao_cao()["path"]
    assert "A01" in a and "B02" in b and a != b


def test_ten_sheet_dai_va_trung_van_hop_le(tmp_path):
    """Nhãn chi nhánh do người dùng đặt: Excel giới hạn 31 ký tự và đòi tên duy nhất."""
    from app import report
    da_dung: set[str] = set()
    dai = "Chi nhanh mien Trung - Nha may so 2"
    c1 = report._cap_ten_sheet(dai, da_dung)
    c2 = report._cap_ten_sheet(dai, da_dung)
    for t in c1 + c2:
        assert len(t) <= 31
    assert len(set(c1 + c2)) == 4


def test_khung_nhin_don_vi_chi_doc():
    """_kq/_df… là khung nhìn vào chi nhánh đang xem. Gán vào chúng khi chưa nạp
    đơn vị nào sẽ rơi vào hư không — phải nổ ngay thay vì im lặng."""
    api = JsApi()
    with pytest.raises(AttributeError):
        api._kq = {}
    assert api._kq == {} and api._df is None


def test_lay_chi_tiet_chua_co_du_lieu():
    assert "Chưa có dữ liệu" in JsApi().lay_chi_tiet("C1.1")["loi"]


def test_cot_branchcode_khong_lot_vao_bang_chi_tiet(tmp_path):
    """BranchCode là cột kỹ thuật để tách đơn vị, không phải thông tin kế toán —
    nó đã nằm trên thanh chọn chi nhánh, lặp lại ở mọi dòng chỉ tốn chỗ."""
    api = _api_hai_chi_nhanh(tmp_path)
    api.chay_kiem_tra()
    assert "BranchCode" not in api.lay_chi_tiet("C1.1")["cot"]


def test_tong_so_dong_bang_tong_cac_chi_nhanh(tmp_path):
    a = _ghi(tmp_path, "a.xlsx", [{"BranchCode": "A01"}, {"BranchCode": "B02"}])
    b = _ghi(tmp_path, "b.xlsx", [{"BranchCode": "B02"}, {"BranchCode": "C03"}])
    api = JsApi()
    info = api.nap_nhieu_file([a, b])
    assert info["so_dong"] == 4
    assert sum(u["so_dong"] for u in info["don_vi"]) == 4
    assert pd.Series([u["ma"] for u in info["don_vi"]]).tolist() == ["A01", "B02", "C03"]


# ---------------------------------------------- chi nhánh đa cột (cột "Đơn vị")
def test_nhan_chi_nhanh_tu_cot_don_vi_khi_khong_co_branchcode():
    from app.loader import ma_chi_nhanh
    df = pd.DataFrame({"DebitAccount": ["621", "621"], "Đơn vị": ["VXHN", "VXHO"]})
    assert list(ma_chi_nhanh(df)) == ["VXHN", "VXHO"]


def test_branchcode_uu_tien_hon_don_vi():
    from app.loader import ma_chi_nhanh
    df = pd.DataFrame({"BranchCode": ["A01", "A01"], "Đơn vị": ["VXHN", "VXHO"]})
    assert list(ma_chi_nhanh(df)) == ["A01", "A01"]


def test_cot_branchcode_rong_thi_roi_xuong_don_vi():
    from app.loader import ma_chi_nhanh, CHI_NHANH_KHONG_RO
    df = pd.DataFrame({"BranchCode": [None, None], "Đơn vị": ["VXHN", None]})
    assert list(ma_chi_nhanh(df)) == ["VXHN", CHI_NHANH_KHONG_RO]


def test_tach_theo_don_vi_thanh_hai_chi_nhanh(tmp_path):
    p = tmp_path / "vx.xlsx"
    tao_df([{"Đơn vị": "VXHN", "DocNo": "H1"}, {"Đơn vị": "VXHO", "DocNo": "O1"},
            {"Đơn vị": "VXHN", "DocNo": "H2"}]).to_excel(p, index=False)
    from app.loader import doc_nhieu_bang_ke
    ds = doc_nhieu_bang_ke([str(p)])
    assert [(tt.chi_nhanh, tt.so_dong) for _, tt in ds] == [("VXHN", 2), ("VXHO", 1)]
