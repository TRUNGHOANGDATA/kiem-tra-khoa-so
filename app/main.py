"""Điểm vào: mở cửa sổ pywebview. Chạy: python -m app.main (từ thư mục gốc)."""
from pathlib import Path

import webview

from . import duong_dan
from .api import JsApi

# webapp/ và app.ico là TÀI NGUYÊN (chỉ đọc) — bản đóng gói lấy từ bundle, chạy mã
# nguồn lấy trong app/. Bản React build được commit sẵn nên chỉ cần Python, không Node.
_TN = duong_dan.thu_muc_tai_nguyen()
_APP = _TN / "app" if (_TN / "app" / "main.py").exists() else _TN
WEB_DIR = _APP / "webapp" if (_APP / "webapp" / "index.html").exists() else _APP / "web"
ICON = _APP / "app.ico"


def main():
    duong_dan.bay_seed_neu_can()   # lần đầu (bản đóng gói): bày sẵn kho + cấu hình
    api = JsApi()
    # text_select=True là BẮT BUỘC, không phải tuỳ chọn thẩm mỹ.
    # pywebview mặc định text_select=False và khi đó tiêm thẳng vào <head> lúc chạy:
    #     body {-webkit-user-select: none; …; user-select: none; cursor: default;}
    # (webview/js/customize.js). Thẻ <style> đó được nối vào cuối <head>, sau
    # style.css của ứng dụng, nên không một dòng CSS nào của chúng ta thắng được ở
    # cùng độ ưu tiên — kết quả là không bôi đen được chữ trong bảng chi tiết và
    # Ctrl+C không có gì để chép. Đúng việc khách báo: mở bảng ra nhưng không lấy
    # được số chứng từ (PX2608-000366) để sang Bravo tra.
    # style.css còn khoá thêm một lớp phòng thủ bằng "html body" (đặc trưng cao hơn
    # "body") để dù bản pywebview khác có đổi mặc định thì bảng vẫn chọn được chữ.
    # maximized=True: mở ra là phóng to hết màn hình (vẫn còn thanh tiêu đề / nút
    # đóng — không phải fullscreen kiểu kiosk che mất nút đóng). width/height là kích
    # thước khi người dùng bấm thu nhỏ lại, min_size chặn không cho kéo nhỏ quá.
    window = webview.create_window(
        "Kiểm tra khóa sổ cuối kỳ", url=str(WEB_DIR / "index.html"), js_api=api,
        width=1100, height=750, min_size=(1000, 700), background_color="#F1EFE9",
        text_select=True, maximized=True,
    )
    api.gan_window(window)
    # icon=.ico cho cửa sổ/taskbar (pywebview 6.x hỗ trợ ở webview.start); thiếu file thì bỏ qua.
    webview.start(icon=str(ICON)) if ICON.exists() else webview.start()


if __name__ == "__main__":
    main()
