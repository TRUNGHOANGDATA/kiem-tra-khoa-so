"""Điểm vào: mở cửa sổ pywebview. Chạy: python -m app.main (từ thư mục gốc)."""
from pathlib import Path

import webview

from .api import JsApi

WEB_DIR = Path(__file__).resolve().parent / "web"


def main():
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
    window = webview.create_window(
        "Kiểm tra khóa sổ cuối kỳ", url=str(WEB_DIR / "index.html"), js_api=api,
        width=1100, height=750, min_size=(1000, 700), background_color="#F5F7FA",
        text_select=True,
    )
    api.gan_window(window)
    webview.start()


if __name__ == "__main__":
    main()
