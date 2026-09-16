"""Đăng ký các nhóm kiểm tra và chạy tuần tự."""
from collections.abc import Callable

import pandas as pd

from . import (g1_chung_tu, g2_dinh_khoan, g3_thue_gtgt, g4_kho_gia_von, g5_ket_chuyen,
               g6_tong_quan, g7_phan_bo_trich_lap, g8_bao_cao_quan_tri)
from .base import DO, VANG, XANH, BoiCanh, CheckResult  # noqa: F401  (re-export)

TEN_NHOM = {
    "G1": "Hình thức chứng từ",
    "G2": "Định khoản bất thường",
    "G3": "Thuế GTGT",
    "G4": "Kho & giá vốn",
    "G5": "Kết chuyển cuối kỳ",
    "G6": "Thống kê & soát xét",
    "G7": "Phân bổ & trích lập cuối kỳ",
    "G8": "Sẵn sàng báo cáo quản trị",
}
DANH_SACH = [
    ("G1", g1_chung_tu.kiem_tra), ("G2", g2_dinh_khoan.kiem_tra), ("G3", g3_thue_gtgt.kiem_tra),
    ("G4", g4_kho_gia_von.kiem_tra), ("G5", g5_ket_chuyen.kiem_tra), ("G6", g6_tong_quan.kiem_tra),
    ("G7", g7_phan_bo_trich_lap.kiem_tra), ("G8", g8_bao_cao_quan_tri.kiem_tra),
]


def chay_tat_ca(df: pd.DataFrame, ctx: BoiCanh,
                on_progress: Callable[[str, int], None] | None = None) -> list[CheckResult]:
    kq: list[CheckResult] = []
    n = len(DANH_SACH)
    for i, (ma, fn) in enumerate(DANH_SACH):
        if on_progress:
            on_progress(TEN_NHOM[ma], int(i * 100 / n))
        kq.extend(fn(df, ctx))
    if on_progress:
        on_progress("Hoàn tất", 100)
    return kq
