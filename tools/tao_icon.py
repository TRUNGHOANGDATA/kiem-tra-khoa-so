"""Sinh icon app (khiên thép + dòng sổ + lỗ khóa trên nền đồng thau) ra app/app.ico.

Biến thể TÔ ĐẶC (khác huy hiệu monoline trên header) để rõ nét ở cỡ 16–32px taskbar:
khiên tối trên badge đồng thau, dòng kẻ sổ + lỗ khóa "khoét" màu đồng sáng.

Chạy: python tools/tao_icon.py   (cần Pillow + numpy — đã có sẵn trong môi trường)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

GOC = Path(__file__).resolve().parent.parent
XUAT = GOC / "app" / "app.ico"

S = 1024                      # vẽ ở độ phân giải cao rồi thu nhỏ (khử răng cưa)
BRASS_HI = (214, 175, 87)     # #D6AF57 góc trên-trái
BRASS_LO = (138, 99, 32)      # #8A6320 góc dưới-phải
KHIEN = (10, 21, 33)          # #0A1521 thép mực
DONG_SANG = (232, 199, 110)   # nét đồng khoét trên khiên


def _nen_dong_thau_bo_goc() -> Image.Image:
    """Badge bo góc, tô gradient chéo đồng thau, ngoài badge trong suốt."""
    m = int(S * 0.055)
    bk = int(S * 0.225)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    t = ((xx + yy) / (2 * (S - 1)))[..., None]          # 0 (trên-trái) -> 1 (dưới-phải)
    grad = ((1 - t) * np.array(BRASS_HI) + t * np.array(BRASS_LO)).astype(np.uint8)
    img = Image.fromarray(np.dstack([grad, np.full((S, S), 255, np.uint8)]), "RGBA")
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([m, m, S - 1 - m, S - 1 - m], radius=bk, fill=255)
    img.putalpha(mask)
    return img


def _diem_khien(sc: float, ox: float, oy: float) -> list[tuple[float, float]]:
    """Đa giác khiên trong hệ 24-đơn vị (đỉnh trên, vai, bo cong xuống mũi), đã map ra px."""
    pts = [(12, 2.8), (19.5, 5.6), (19.5, 11.5), (18, 15.6), (15, 18.6),
           (12, 20.6), (9, 18.6), (6, 15.6), (4.5, 11.5), (4.5, 5.6)]
    return [((x - 12) * sc + ox, (y - 11.7) * sc + oy) for x, y in pts]


def _map(sc: float, ox: float, oy: float, x: float, y: float) -> tuple[float, float]:
    return (x - 12) * sc + ox, (y - 11.7) * sc + oy


def ve() -> Image.Image:
    img = _nen_dong_thau_bo_goc()
    d = ImageDraw.Draw(img)
    sc = (S * 0.66) / 17.8                 # khiên chiếm ~66% cạnh badge
    ox = oy = S / 2

    # Khiên tối
    d.polygon(_diem_khien(sc, ox, oy), fill=KHIEN)

    lw = int(0.9 * sc)                     # nét dày cho dòng kẻ sổ
    # Hai dòng kẻ sổ (đồng sáng) phía trên
    for yy in (8.2, 10.6):
        x1, y1 = _map(sc, ox, oy, 7.6, yy)
        x2, y2 = _map(sc, ox, oy, 16.4, yy)
        d.line([x1, y1, x2, y2], fill=DONG_SANG, width=lw)
    # Lỗ khóa: tròn + đuôi hình thang, khoét đồng sáng
    cx, cy = _map(sc, ox, oy, 12, 13.6)
    r = 1.75 * sc
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=DONG_SANG)
    t1 = _map(sc, ox, oy, 11.0, 17.6)
    t2 = _map(sc, ox, oy, 13.0, 17.6)
    d.polygon([(cx, cy), t1, t2], fill=DONG_SANG)

    return img.resize((256, 256), Image.LANCZOS)


def main() -> None:
    icon = ve()
    XUAT.parent.mkdir(parents=True, exist_ok=True)
    icon.save(XUAT, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("Da ghi", XUAT)


if __name__ == "__main__":
    main()
