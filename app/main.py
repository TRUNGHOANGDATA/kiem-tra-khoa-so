"""Điểm vào: mở cửa sổ pywebview. Chạy: python -m app.main (từ thư mục gốc)."""
from pathlib import Path

import webview

from .api import JsApi

WEB_DIR = Path(__file__).resolve().parent / "web"


def main():
    api = JsApi()
    window = webview.create_window(
        "Kiểm tra khóa sổ cuối kỳ", url=str(WEB_DIR / "index.html"), js_api=api,
        width=1100, height=750, min_size=(1000, 700), background_color="#F5F7FA",
    )
    api.gan_window(window)
    webview.start()


if __name__ == "__main__":
    main()
