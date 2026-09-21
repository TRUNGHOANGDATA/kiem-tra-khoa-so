from app.api import JsApi
from app import cap_nhat


def test_kiem_tra_danh_dau_co_moi(monkeypatch):
    monkeypatch.setattr(cap_nhat, "lay_ban_moi_nhat",
                        lambda *a, **k: {"phien_ban": "1.2.0", "url_tai": "u", "mo_ta": "m"})
    r = JsApi().kiem_tra_cap_nhat("1.1.3")
    assert r["co_moi"] is True and r["phien_ban"] == "1.2.0"


def test_kiem_tra_khi_dang_moi_nhat(monkeypatch):
    monkeypatch.setattr(cap_nhat, "lay_ban_moi_nhat",
                        lambda *a, **k: {"phien_ban": "1.1.3", "url_tai": "u", "mo_ta": ""})
    assert JsApi().kiem_tra_cap_nhat("1.1.3")["co_moi"] is False


def test_kiem_tra_chuyen_tiep_loi(monkeypatch):
    monkeypatch.setattr(cap_nhat, "lay_ban_moi_nhat", lambda *a, **k: {"loi": "x"})
    assert JsApi().kiem_tra_cap_nhat("1.1.3") == {"loi": "x"}


def test_tai_va_cai_loi_thi_khong_dong_app(monkeypatch):
    def _no(url): raise OSError("dut")
    monkeypatch.setattr(cap_nhat, "tai_bo_cai", _no)
    api = JsApi()
    dong = []
    api._window = type("W", (), {"destroy": lambda self: dong.append(1)})()
    r = api.tai_va_cai("u")
    assert "loi" in r and dong == []            # tuyệt đối không đóng app khi lỗi
