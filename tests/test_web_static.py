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
