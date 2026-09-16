import re
from pathlib import Path

WEB = Path("app/web")


def test_index_tham_chieu_file_local_va_du_id():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert 'href="style.css"' in html and 'src="app.js"' in html
    assert "http://" not in html and "https://" not in html   # offline
    for i in ["man-hinh-1", "man-hinh-2", "btn-kiem-tra", "tab-a", "tab-b", "ds-buoc",
              "luoi-nhom", "bang-chi-tiet", "btn-xuat", "toast", "vung-keo-tha",
              "vung-cuon", "btn-chep-trang", "btn-dong-chi-tiet"]:
        assert f'id="{i}"' in html, i


def test_css_segoe_ui_light_mode():
    css = (WEB / "style.css").read_text(encoding="utf-8")
    assert "Segoe UI" in css and "#1F4E79" in css and "#DC2626" in css
    assert "prefers-color-scheme: dark" not in css


def test_app_js_co_ham_tien_trinh_va_goi_api():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert "function onTienTrinh" in js
    for f in ["chon_nhieu_file", "nap_nhieu_file", "quet_thu_muc",
              "chay_kiem_tra", "chon_don_vi", "lay_chi_tiet", "xuat_bao_cao",
              "xuat_tong_hop", "mo_file", "mo_thu_muc"]:
        assert f"api.{f}(" in js, f
    assert "pywebviewFullPath" in js   # kéo-thả lấy đường dẫn thật
    # Mọi phương thức JS gọi phải thật sự tồn tại trên JsApi — pywebview không báo
    # lỗi khi gọi tên không có, lời gọi chỉ lặng lẽ trả về undefined.
    from app.api import JsApi
    for f in sorted(set(re.findall(r"api\.([a-z_]+)\(", js))):
        assert callable(getattr(JsApi, f, None)), f"JsApi thiếu phương thức {f}"


def test_keo_nhieu_file_va_thanh_chi_nhanh():
    """Nhiều chi nhánh: kéo-thả phải nhận CẢ danh sách file, và nút 'Kiểm tra' phải
    gửi lại cả danh sách — gửi mỗi file đầu sẽ vứt mất các chi nhánh còn lại."""
    js = (WEB / "app.js").read_text(encoding="utf-8")
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "[...ev.dataTransfer.files]" in js          # không chỉ files[0]
    assert "api.chay_kiem_tra(fileHienTai?.cac_path" in js
    assert "function veThanhDonVi" in js and "doiDonVi" in js
    for i in ("thanh-don-vi", "ds-don-vi-nap", "btn-quet-thu-muc", "btn-xuat-tong-hop"):
        assert f'id="{i}"' in html, i


def test_moi_id_app_js_dung_deu_ton_tai_trong_html():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    html = (WEB / "index.html").read_text(encoding="utf-8")
    ids = set(re.findall(r'\$\("([a-z0-9\-]+)"\)', js))
    assert len(ids) >= 30, f"Chỉ tìm thấy {len(ids)} id trong app.js — regex có thể sai"
    thieu = sorted(i for i in ids if f'id="{i}"' not in html)
    assert thieu == [], f"app.js tham chiếu id không có trong index.html: {thieu}"


def test_main_bat_text_select():
    """Nguyên nhân gốc của "không copy được": pywebview mặc định text_select=False
    và tiêm "body {user-select: none}" vào <head> lúc chạy. Bỏ tham số này đi là
    khách lại không lấy được số chứng từ mang sang Bravo."""
    main = Path("app/main.py").read_text(encoding="utf-8")
    assert "text_select=True" in main
    assert "maximized=True" in main   # mở ra phóng to hết màn hình


def test_css_khong_khoa_boi_den_bang():
    """Bảng chi tiết phải chọn được chữ, và lớp phòng thủ phải đủ đặc trưng để
    thắng thẻ <style> pywebview nối vào CUỐI <head> (sau style.css)."""
    css = (WEB / "style.css").read_text(encoding="utf-8")
    assert "html body" in css and "user-select: text" in css
    # không được có quy tắc tắt bôi đen trên toàn trang
    for xau in ("body { -webkit-user-select: none", "* { user-select: none",
                "html, body { user-select: none"):
        assert xau not in css, xau
    # bảng nêu đích danh là chọn được
    assert ".bang td" in css and ".bang td .o-chu" in css


def test_app_js_co_du_ba_loi_chep_va_duong_lui():
    """Ba lối chép (ô / dòng / cả trang), API chính + dự phòng, và KHÔNG được im
    lặng khi cả hai hỏng."""
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert "navigator.clipboard.writeText" in js
    assert 'document.execCommand("copy")' in js
    assert "Không chép được" in js                      # báo lỗi, không im lặng
    assert "btn-chep-trang" in js and "nut-chep" in js   # chép cả trang & chép cả dòng
    assert '"\\t"' in js and "Chép cả dòng" in js        # TSV + nhãn cho nút chỉ có biểu tượng
    # bấm-để-chép không được tranh chỗ với bôi đen
    assert "isCollapsed" in js and "mousedown" in js


def test_bo_cuc_man_hinh_2_lap_day_cua_so():
    """Bảng chi tiết nở theo cửa sổ, không còn khung cao cố định; vùng kết quả
    không phải một khung cuộn dài hơn cửa sổ."""
    css = (WEB / "style.css").read_text(encoding="utf-8")
    assert "clamp(180px, 36vh, 420px)" not in css       # chiều cao cố định cũ
    assert ".vung-cuon.co-chi-tiet .noi-dung" in css
    for quy_tac in (".bang-cuon", ".khung-chi-tiet", ".noi-dung"):
        assert quy_tac in css, quy_tac
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert "co-chi-tiet" in js
    # vùng kết quả không còn tự cuộn -> không được cuộn bảng vào tầm nhìn nữa
    assert "scrollIntoView" not in js


def test_du_lieu_duoc_escape_truoc_khi_vao_innerhtml():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert "const esc" in js or "function esc" in js
    for raw in ("${r[c]}", "${b.buoc}", "${b.tom_tat}", "${c.ten}", "${n.ten}", "${c.ma}"):
        assert raw not in js, f"{raw} phải đi qua esc() trước khi vào innerHTML"


def test_app_js_biet_trang_thai_tu_xac_nhan():
    """khoaTT() nuốt trạng thái lạ về 'không áp dụng' -> app.js phải biết tu_xac_nhan;
    css phải có class riêng để nó không bị đọc nhầm thành cảnh báo vàng."""
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert "tu_xac_nhan" in js
    css = (WEB / "style.css").read_text(encoding="utf-8")
    assert "tt-tu_xac_nhan" in css


def test_khoi_tao_khong_tu_nap_file_mac_dinh():
    """Người dùng luôn tự chọn file — khoiTao không được gọi lay_file_moi_nhat khi mở."""
    js = (WEB / "app.js").read_text(encoding="utf-8")
    than = re.search(r"async function khoiTao\(\) \{(.*?)\n\}", js, re.S).group(1)
    assert "lay_file_moi_nhat" not in than, "khoiTao vẫn còn tự nạp file mặc định"
