from app.api import JsApi
from app import cau_hinh


def test_thu_muc_doc_tu_cau_hinh(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)   # ep GOC ve tmp
    cau_hinh.ghi_cau_hinh(str(tmp_path), {"thu_muc_nguon": "Nguon", "thu_muc_xuat": "Xuat", "thu_muc_kho": "Kho"})
    api = JsApi()
    assert api.thu_muc_source == str(tmp_path / "Nguon")
    assert api.thu_muc_report == str(tmp_path / "Xuat")
    assert api._thu_muc_kho == str(tmp_path / "Kho")


def test_gan_de_van_thang_cau_hinh(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    api.thu_muc_source = str(tmp_path / "ghi_de")     # gan thang -> override
    assert api.thu_muc_source == str(tmp_path / "ghi_de")
    api._thu_muc_kho = str(tmp_path / "kho_de")
    assert api._thu_muc_kho == str(tmp_path / "kho_de")


def test_luu_roi_doc_lai_phan_anh_ngay(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    k = api.luu_cau_hinh({"thu_muc_nguon": "A", "thu_muc_xuat": "B", "thu_muc_kho": "C"})
    assert k["ok"] is True
    assert api.thu_muc_source == str(tmp_path / "A")   # doc lai moi lan dung -> thay ngay


def test_luu_gia_tri_trong_dung_mac_dinh(tmp_path, monkeypatch):
    # O trong/toan khoang trang khong duoc luu nguyen (se giai thanh GOC) -> phai
    # bi thay bang thu muc con mac dinh truoc khi ghi.
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    k = api.luu_cau_hinh({"thu_muc_nguon": "A", "thu_muc_xuat": "  ", "thu_muc_kho": ""})
    assert k["ok"] is True
    assert api.thu_muc_report == str(tmp_path / "2. Report")
    assert api._thu_muc_kho == str(tmp_path / "3. Chot so")


def test_thu_muc_tu_tao_khi_chua_co(tmp_path, monkeypatch):
    """Chưa có folder thì app phải TỰ TẠO, không để lỗi "Location is not available".

    Thư mục rỗng (vd 2. Report) hay bị bỏ rơi khi đóng gói; app không được dựa vào
    seed mà phải tự dựng khi cần.
    """
    monkeypatch.setattr("app.api.GOC", tmp_path)
    from app.api import JsApi
    api = JsApi()
    for thu_muc in (api.thu_muc_source, api.thu_muc_report, api._thu_muc_kho):
        from pathlib import Path
        assert Path(thu_muc).is_dir(), f"chưa tự tạo: {thu_muc}"


def test_thu_muc_mo_hop_thoai_luon_ton_tai(tmp_path, monkeypatch):
    """Hộp thoại chọn file mở với thư mục ban đầu KHÔNG tồn tại -> Windows hiện
    dialog native 'Location is not available' mà Python không bắt được. Helper phải
    tự tạo thư mục và không bao giờ trả về đường dẫn không tồn tại."""
    monkeypatch.setattr("app.api.GOC", tmp_path)
    from app.api import JsApi
    from pathlib import Path
    api = JsApi()
    d = api._thu_muc_dialog(str(tmp_path / "3. Chot so"))
    assert Path(d).is_dir()
    # đường dẫn rác không tạo được -> trả "" để OS tự chọn, KHÔNG đẩy path hỏng vào dialog
    assert api._thu_muc_dialog(r"Z:\khong_ton_taibc\def") == ""
    assert api._thu_muc_dialog("") == ""
