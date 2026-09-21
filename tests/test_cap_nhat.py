from app import cap_nhat as cn
import json
import urllib.error


def test_moi_hon_theo_tung_so():
    assert cn.moi_hon("1.1.4", "1.1.3") is True
    assert cn.moi_hon("1.2.0", "1.1.9") is True
    assert cn.moi_hon("1.1.3", "1.1.3") is False
    assert cn.moi_hon("1.1.2", "1.1.3") is False


def test_moi_hon_bo_tien_to_v_va_do_dai_lech():
    assert cn.moi_hon("v1.2.0", "1.1.5") is True      # có 'v'
    assert cn.moi_hon("1.2", "1.1.9") is True          # thiếu số cuối -> (1,2) > (1,1,9)
    assert cn.moi_hon("1.2.0", "1.2") is False         # (1,2,0) == (1,2,0)


_JSON_MAU = json.dumps({
    "tag_name": "v1.2.0",
    "body": "Sửa C4.6, thêm nút cập nhật",
    "assets": [
        {"name": "note.txt", "browser_download_url": "https://x/note.txt"},
        {"name": "KiemTraKhoaSo-Setup-1.2.0.exe",
         "browser_download_url": "https://x/KiemTraKhoaSo-Setup-1.2.0.exe"},
    ],
}).encode("utf-8")


class _GiaResp:
    def __init__(self, data): self._d = data
    def read(self): return self._d
    def __enter__(self): return self
    def __exit__(self, *a): return False


def test_lay_ban_moi_nhat_parse_dung(monkeypatch):
    monkeypatch.setattr(cn.urllib.request, "urlopen", lambda *a, **k: _GiaResp(_JSON_MAU))
    r = cn.lay_ban_moi_nhat()
    assert r["phien_ban"] == "1.2.0"                       # đã bỏ 'v'
    assert r["url_tai"].endswith("KiemTraKhoaSo-Setup-1.2.0.exe")
    assert "C4.6" in r["mo_ta"]


def test_lay_ban_moi_nhat_loi_mang_thi_tra_loi(monkeypatch):
    def _no(*a, **k): raise urllib.error.URLError("khong co mang")
    monkeypatch.setattr(cn.urllib.request, "urlopen", _no)
    r = cn.lay_ban_moi_nhat()
    assert "loi" in r and "phien_ban" not in r


def test_lay_ban_moi_nhat_404_coi_nhu_da_moi_nhat(monkeypatch):
    def _404(*a, **k):
        raise urllib.error.HTTPError("u", 404, "Not Found", {}, None)
    monkeypatch.setattr(cn.urllib.request, "urlopen", _404)
    r = cn.lay_ban_moi_nhat()
    assert r.get("khong_co_release") is True and "loi" not in r


def test_lay_ban_moi_nhat_thieu_asset_exe(monkeypatch):
    data = json.dumps({"tag_name": "v1.2.0", "body": "", "assets": []}).encode()
    monkeypatch.setattr(cn.urllib.request, "urlopen", lambda *a, **k: _GiaResp(data))
    r = cn.lay_ban_moi_nhat()
    assert "loi" in r
