"""Điểm vào cho bản đóng gói.

Không trỏ PyInstaller thẳng vào app/main.py: file đó dùng import tương đối
(`from . import ...`), chạy như __main__ sẽ vỡ "no known parent package". Ở đây
import GÓI `app` bằng đường tuyệt đối để mọi import tương đối bên trong còn hiệu lực
(khi chạy mã nguồn thì dùng `python -m app.main` nên không gặp).
"""
from app.main import main

if __name__ == "__main__":
    main()
