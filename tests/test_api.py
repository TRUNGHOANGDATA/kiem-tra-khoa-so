import json

import pandas as pd

import app.api as api_module
from app.api import DonVi, JsApi
from app.checks.base import CheckResult
from app.loader import ThongTinFile


def _thong_tin_gia() -> ThongTinFile:
    return ThongTinFile(path="", ten="gia-lap.xlsx", ky="08/2026", ky_thang=8, ky_nam=2026,
                        so_dong=0, tong_ps=0.0, chi_nhanh="A01")


def _xlsx(tmp_path):
    rows = [
        {"DocNo": "A", "DocDate": "2026-08-01", "DebitAccount": "6214", "CreditAccount": "1521", "Amount": 100, "Description": "x"},
        {"DocNo": "B", "DocDate": "2026-08-02", "DebitAccount": "154", "CreditAccount": "6214", "Amount": 100, "Description": None},
        {"DocNo": "C", "DocDate": "2026-08-03", "DebitAccount": "632111", "CreditAccount": "1551", "Amount": 70, "Description": "gv"},
    ]
    p = tmp_path / "bk.xlsx"
    pd.DataFrame(rows).to_excel(p, sheet_name="Table1", index=False)
    return str(p)


def test_chay_kiem_tra_tra_json_hop_le(tmp_path):
    api = JsApi()
    kq = api.chay_kiem_tra(_xlsx(tmp_path))
    json.dumps(kq)  # không numpy scalar
    assert kq["tomtat"]["ky"] == "08/2026" and kq["tomtat"]["so_dong"] == 3
    assert kq["tomtat"]["san_sang"] is False           # 632 chưa kết chuyển -> C5.2 đỏ
    assert len(kq["trang_thai"]) == 16 and len(kq["nhom"]) == 7
    g5 = next(n for n in kq["nhom"] if n["ma"] == "G5")
    assert g5["muc_do"] == "do"


def test_lay_chi_tiet_phan_trang_va_tim_kiem(tmp_path):
    api = JsApi()
    api.chay_kiem_tra(_xlsx(tmp_path))
    ct = api.lay_chi_tiet("C1.1")
    assert ct["tong"] == 1 and ct["dong"][0]["DocNo"] == "B" and ct["dong"][0]["DocDate"] == "02/08/2026"
    assert api.lay_chi_tiet("C1.1", tim_kiem="zzz")["tong"] == 0
    assert "TK" in api.lay_chi_tiet("C5.2")["cot"]


def test_xuat_bao_cao_va_loi_khi_chua_chay(tmp_path, monkeypatch):
    api = JsApi()
    assert "loi" in api.xuat_bao_cao()
    api.chay_kiem_tra(_xlsx(tmp_path))
    monkeypatch.setattr(api, "thu_muc_report", str(tmp_path / "out"))
    kq = api.xuat_bao_cao()
    assert kq["path"].endswith(".xlsx") and (tmp_path / "out").exists()


def test_file_khong_ton_tai_tra_loi():
    assert "loi" in JsApi().chay_kiem_tra("khong/co/file.xlsx")


def test_nap_file_hop_le_va_khong_hop_le(tmp_path):
    api = JsApi()
    kq = api.nap_file(_xlsx(tmp_path))
    assert kq["so_dong"] == 3 and kq["ky"] == "08/2026"
    assert "loi" in api.nap_file("khong/co/file.xlsx")


def test_lay_file_moi_nhat_none_khi_khong_co_file(tmp_path):
    api = JsApi()
    api.thu_muc_source = str(tmp_path)
    assert api.lay_file_moi_nhat() is None


def test_lay_file_moi_nhat_tra_ve_file_moi_nhat(tmp_path):
    api = JsApi()
    api.thu_muc_source = str(tmp_path)
    p = _xlsx(tmp_path)
    kq = api.lay_file_moi_nhat()
    assert kq["path"] == p and kq["so_dong"] == 3


class _FakeWindow:
    def __init__(self):
        self.evaluate_js_calls = []

    def evaluate_js(self, script):
        self.evaluate_js_calls.append(script)


def test_gan_window_day_tien_trinh_qua_evaluate_js(tmp_path):
    api = JsApi()
    fw = _FakeWindow()
    api.gan_window(fw)
    api.chay_kiem_tra(_xlsx(tmp_path))
    assert fw.evaluate_js_calls
    assert fw.evaluate_js_calls[-1].endswith(", 100)")


def test_chon_file_loi_dialog_tra_ve_loi():
    class _FakeWindowLoi:
        def create_file_dialog(self, *a, **kw):
            raise RuntimeError("boom")

    api = JsApi()
    api.gan_window(_FakeWindowLoi())
    kq = api.chon_file()
    assert "loi" in kq


def test_mo_file_goi_os_startfile(monkeypatch):
    calls = []
    monkeypatch.setattr(api_module.os, "startfile", lambda p: calls.append(p), raising=False)
    api = JsApi()
    assert api.mo_file("C:/mot/file.xlsx") is True
    assert calls == ["C:/mot/file.xlsx"]


def test_mo_file_tra_loi_khi_file_da_bi_xoa(tmp_path):
    """B3: JS không bắt reject — ném ở đây là người dùng bấm nút và không thấy gì."""
    p = tmp_path / "da-xoa.xlsx"
    p.write_text("x")
    p.unlink()
    kq = JsApi().mo_file(str(p))
    assert isinstance(kq, dict) and "loi" in kq


def test_mo_thu_muc_tra_loi_khi_duong_dan_khong_ton_tai(tmp_path):
    kq = JsApi().mo_thu_muc(str(tmp_path / "khong-co" / "bao-cao.xlsx"))
    assert isinstance(kq, dict) and "loi" in kq


def test_moi_phuong_thuc_nhan_duong_dan_deu_tra_loi_thay_vi_nem(tmp_path):
    """B3: cầu nối pywebview phải trả {loi}, không ném — JS phía kia không bắt reject."""
    api = JsApi()
    khong_co = str(tmp_path / "khong-co.xlsx")
    for ten in ("nap_file", "chay_kiem_tra", "mo_file", "mo_thu_muc"):
        kq = getattr(api, ten)(khong_co)          # ném là test đỏ ngay tại đây
        assert isinstance(kq, dict) and "loi" in kq, ten


def test_mo_thu_muc_goi_popen_khi_la_file(monkeypatch, tmp_path):
    p = tmp_path / "bk.xlsx"
    p.write_text("x")
    calls = []
    monkeypatch.setattr(api_module.subprocess, "Popen", lambda args: calls.append(args))
    api = JsApi()
    assert api.mo_thu_muc(str(p)) is True
    assert calls == [["explorer", "/select,", str(p)]]


def test_mo_thu_muc_goi_os_startfile_khi_la_thu_muc(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(api_module.os, "startfile", lambda p: calls.append(p), raising=False)
    api = JsApi()
    assert api.mo_thu_muc(str(tmp_path)) is True
    assert calls == [str(tmp_path)]


def test_tim_kiem_theo_ngay_hien_thi(tmp_path):
    api = JsApi()
    api.chay_kiem_tra(_xlsx(tmp_path))
    ct = api.lay_chi_tiet("C1.1", tim_kiem="02/08/2026")
    assert ct["tong"] == 1 and ct["dong"][0]["DocNo"] == "B"


def test_lay_chi_tiet_kem_nhan_tieng_viet_va_cot_so(tmp_path):
    """C4/C6: nhãn cột và danh sách cột số đi từ backend sang, JS không tự giữ bản sao."""
    api = JsApi()
    api.chay_kiem_tra(_xlsx(tmp_path))
    ct = api.lay_chi_tiet("C1.1")
    assert ct["cot"][:2] == ["DocNo", "DocDate"]          # khóa dữ liệu giữ tên gốc
    assert ct["nhan"][:2] == ["Số CT", "Ngày CT"]         # nhãn hiển thị tiếng Việt
    assert ct["nhan"][-1] == "Lý do" and "Số tiền" in ct["nhan"]
    assert ct["cot_so"] == ["Amount"]

    th = api.lay_chi_tiet("C6.3")
    assert th["nhan"] == ["Loại CT", "Số dòng", "Tổng tiền"]
    assert set(th["cot_so"]) == {"so_dong", "tong"}       # so_dong từng bị bỏ sót ở báo cáo


def test_moi_cot_cac_check_sinh_ra_deu_co_nhan_tieng_viet(tmp_path):
    """C4: quét toàn bộ 37 check — không cột nào rơi lại tên tiếng Anh."""
    api = JsApi()
    api.chay_kiem_tra(_xlsx(tmp_path))
    thieu = {}
    for ma in api._kq:
        ct = api.lay_chi_tiet(ma)
        for c, nhan in zip(ct["cot"], ct["nhan"]):
            if c == nhan:
                thieu.setdefault(ma, []).append(c)
    assert thieu == {}, f"cột chưa có trong TEN_COT: {thieu}"


def test_lay_chi_tiet_tu_phuc_hoi_khi_kq_bi_xoa(tmp_path):
    """B1: _kq có thể bị xóa (nạp file khác) trong khi màn hình vẫn hiển thị kết quả
    cũ — lay_chi_tiet phải tự chạy lại kiểm tra từ self._df thay vì báo lỗi mã nội bộ."""
    api = JsApi()
    api.chay_kiem_tra(_xlsx(tmp_path))
    api._dv[0].kq = {}  # mô phỏng đúng triệu chứng: cache bị xóa nhưng vẫn còn dữ liệu
    ct = api.lay_chi_tiet("C1.1")
    assert "loi" not in ct
    assert ct["tong"] == 1 and ct["dong"][0]["DocNo"] == "B"
    assert "C1.1" in api._kq and api._ket_qua and api._trang_thai  # đã dựng lại toàn bộ


def test_lay_chi_tiet_bao_loi_ro_rang_khi_chua_co_du_lieu():
    """B1: chưa từng chọn/kiểm tra file nào — lỗi phải hướng dẫn hành động, không nêu mã nội bộ."""
    kq = JsApi().lay_chi_tiet("C4.1")
    assert kq["loi"] == "Chưa có dữ liệu — hãy chọn file và bấm Kiểm tra"


def test_lay_chi_tiet_ma_khong_ton_tai_sau_khi_chay_lai_khong_lap_vo_han(tmp_path):
    """B1: bảo vệ khỏi vòng lặp dựng lại vô ích — mã không tồn tại thì báo lỗi rõ ràng
    một lần, không tự gọi lại chính nó."""
    api = JsApi()
    api.chay_kiem_tra(_xlsx(tmp_path))
    api._dv[0].kq = {}
    kq = api.lay_chi_tiet("KHONG_TON_TAI")
    assert kq["loi"] == "Không tìm thấy kết quả KHONG_TON_TAI sau khi chạy lại kiểm tra"


def test_chay_kiem_tra_lan_2_cung_duong_dan_khong_doc_lai_file(tmp_path, monkeypatch):
    """B3: đường dẫn không đổi thì không được đọc lại Excel lần hai."""
    p = _xlsx(tmp_path)
    goc = api_module.doc_nhieu_bang_ke
    so_lan_doc = []

    def dem(paths, on_file=None):
        so_lan_doc.extend(paths)
        return goc(paths, on_file=on_file)

    monkeypatch.setattr(api_module, "doc_nhieu_bang_ke", dem)
    api = JsApi()
    api.chay_kiem_tra(p)
    api.chay_kiem_tra(p)  # y hệt path đã trả về trước đó — mô phỏng nút "Kiểm tra"
    assert len(so_lan_doc) == 1


def test_man_hinh_1_roi_kiem_tra_khong_doc_lai_file(tmp_path, monkeypatch):
    """B3: mô phỏng đúng luồng thật — lay_file_moi_nhat() nạp file, JS lưu lại info.path
    rồi trả nguyên văn cho chay_kiem_tra() khi bấm 'Kiểm tra'. Vì JsApi luôn gán path đầu
    vào y hệt vào self._tt.path, và JSON round-trip qua JS không đổi nội dung chuỗi, hai
    lần gọi này không được đọc Excel hai lần."""
    _xlsx(tmp_path)  # tạo sẵn file trong thư mục nguồn giả lập
    goc = api_module.doc_nhieu_bang_ke
    so_lan_doc = []

    def dem(paths, on_file=None):
        so_lan_doc.extend(paths)
        return goc(paths, on_file=on_file)

    monkeypatch.setattr(api_module, "doc_nhieu_bang_ke", dem)
    api = JsApi()
    api.thu_muc_source = str(tmp_path)
    info = api.lay_file_moi_nhat()
    kq = api.chay_kiem_tra(info["path"])  # đúng chuỗi JS nhận lại và gửi lên
    assert "loi" not in kq
    assert len(so_lan_doc) == 1


def test_kich_thuoc_gioi_han_toi_da_500():
    api = JsApi()
    df = pd.DataFrame({"DocNo": [f"D{i}" for i in range(600)]})
    api._dv = [DonVi(df, _thong_tin_gia())]
    api._dv[0].kq = {"CX": CheckResult(ma="CX", ten="t", nhom="G1", muc_do="do", chi_tiet=df)}
    ct = api.lay_chi_tiet("CX", kich_thuoc=10_000)
    assert ct["tong"] == 600 and len(ct["dong"]) == 500
    ct2 = api.lay_chi_tiet("CX", trang=2, kich_thuoc=10_000)
    assert len(ct2["dong"]) == 100


def test_cot_so_luong_giu_phan_thap_phan(tmp_path):
    """Số lượng 0,059 làm tròn 0 chữ số thành "0" — đọc đúng thành "không có số
    lượng", ngược hẳn với dòng đang được nêu. Giao diện và Excel phải biết cột nào
    có phần thập phân, không thể đoán từ giá trị."""
    from app.checks.base import COT_SO_LE
    api = JsApi()
    df = pd.DataFrame({"DocNo": ["X"], "Quantity9": [0.059], "Amount": [450878.0]})
    api._dv = [DonVi(df, _thong_tin_gia())]
    api._dv[0].kq = {"CX": CheckResult(ma="CX", ten="t", nhom="G4", muc_do="vang", chi_tiet=df)}
    ct = api.lay_chi_tiet("CX")
    assert "Quantity9" in COT_SO_LE
    assert ct["cot_so_le"] == ["Quantity9"]
    assert ct["dong"][0]["Quantity9"] == 0.059      # không bị làm tròn ở backend
    assert "Amount" not in ct["cot_so_le"]          # tiền vẫn làm tròn về đồng
