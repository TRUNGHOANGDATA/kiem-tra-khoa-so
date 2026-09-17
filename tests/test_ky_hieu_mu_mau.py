"""Người dùng MÙ MÀU: mức độ phải đọc được bằng KÝ HIỆU, màu chỉ là lớp phụ.

Nếu nhãn chỉ khác nhau về màu tô (hoặc emoji 🔴/🟡 khác nhau mỗi sắc), người dùng
không phân biệt được -> báo cáo vô dụng với chính chủ phần mềm.
"""
from pathlib import Path

from app import report

GOC = Path(__file__).resolve().parents[1]


def _dau(nhan: str) -> str:
    return nhan.split(" ", 1)[0]


def test_moi_muc_do_co_ky_hieu_rieng():
    dau = [_dau(v) for v in report.TEN_MUC_DO.values()]
    assert len(set(dau)) == len(report.TEN_MUC_DO)
    assert all(not d[0].isalnum() for d in dau), dau


def test_moi_trang_thai_buoc_co_ky_hieu_rieng():
    dau = [_dau(v) for v in report.TEN_TRANG_THAI.values()]
    assert len(set(dau)) == len(report.TEN_TRANG_THAI)
    assert all(not d[0].isalnum() for d in dau), dau


def test_khong_dung_emoji_phan_biet_bang_mau():
    """🔴/🟡/🟢 cùng hình tròn, chỉ khác sắc -> không được dùng."""
    for f in (GOC / "app").rglob("*.py"):
        src = f.read_text(encoding="utf-8")
        assert not (set("🔴🟡🟢🟠") & set(src)), f
