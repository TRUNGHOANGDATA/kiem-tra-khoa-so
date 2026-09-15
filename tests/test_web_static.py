import re
from pathlib import Path

WEB = Path("app/web")


def test_index_tham_chieu_file_local_va_du_id():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert 'href="style.css"' in html and 'src="app.js"' in html
    assert "http://" not in html and "https://" not in html   # offline
    for i in ["man-hinh-1", "man-hinh-2", "btn-kiem-tra", "tab-a", "tab-b", "ds-buoc",
              "luoi-nhom", "bang-chi-tiet", "btn-xuat", "toast", "vung-keo-tha"]:
        assert f'id="{i}"' in html, i


def test_css_segoe_ui_light_mode():
    css = (WEB / "style.css").read_text(encoding="utf-8")
    assert "Segoe UI" in css and "#1F4E79" in css and "#DC2626" in css
    assert "prefers-color-scheme: dark" not in css


def test_app_js_co_ham_tien_trinh_va_goi_api():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert "function onTienTrinh" in js
    for f in ["lay_file_moi_nhat", "chon_file", "nap_file", "chay_kiem_tra", "lay_chi_tiet", "xuat_bao_cao", "mo_file", "mo_thu_muc"]:
        assert f"api.{f}(" in js, f
    assert "pywebviewFullPath" in js   # kéo-thả lấy đường dẫn thật


def test_moi_id_app_js_dung_deu_ton_tai_trong_html():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    html = (WEB / "index.html").read_text(encoding="utf-8")
    ids = set(re.findall(r'\$\("([a-z0-9\-]+)"\)', js))
    assert len(ids) >= 30, f"Chỉ tìm thấy {len(ids)} id trong app.js — regex có thể sai"
    thieu = sorted(i for i in ids if f'id="{i}"' not in html)
    assert thieu == [], f"app.js tham chiếu id không có trong index.html: {thieu}"


def test_du_lieu_duoc_escape_truoc_khi_vao_innerhtml():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert "const esc" in js or "function esc" in js
    for raw in ("${r[c]}", "${b.buoc}", "${b.tom_tat}", "${c.ten}", "${n.ten}", "${c.ma}"):
        assert raw not in js, f"{raw} phải đi qua esc() trước khi vào innerHTML"
