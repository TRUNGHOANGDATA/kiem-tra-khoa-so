"""Chẩn đoán: gộp nhiều cảnh báo CÙNG MỘT GỐC thành một thông điệp.

Ví dụ thật (A02): C5.x + C9.4 + C11.2 đều là hệ quả của việc CHƯA KẾT CHUYỂN hết
TK 5–9. Thay vì bắt kế toán đọc rời từng cái, nêu một câu: làm kết chuyển xong rồi
kiểm tra lại. C9.5 (bảng kê ≠ CĐPS) là gốc KHÁC nên KHÔNG gộp vào.
"""
import pandas as pd

from app import chan_doan
from app.checks.base import DO, VANG, CheckResult


def _kq(ma_co_loi: dict[str, int]) -> list[CheckResult]:
    """Dựng danh sách CheckResult: mã -> số dòng vi phạm (0 = đạt)."""
    ds = []
    for ma, so in ma_co_loi.items():
        bang = pd.DataFrame([{"x": i} for i in range(so)])
        ds.append(CheckResult(ma, ma, ma.split(".")[0].replace("C", "G"), DO, bang))
    return ds


def test_khong_co_gi_thi_khong_chan_doan():
    assert chan_doan.chan_doan(_kq({"C1.1": 0, "C3.2": 3})) == []


def test_chua_ket_chuyen_gop_c5_c94_c112():
    kq = _kq({"C5.1": 34, "C5.2": 1, "C9.4": 24, "C11.2": 0, "C3.2": 5})
    kq_c112 = next(r for r in kq if r.ma == "C11.2")
    kq_c112.la_thong_ke = True                       # C11.2 tự hạ vì chưa kết chuyển
    cd = chan_doan.chan_doan(kq)
    assert len(cd) == 1
    d = cd[0]
    assert d["ma"] == "chua_ket_chuyen"
    # gộp đúng các mã cùng gốc, KHÔNG kéo C3.2 (gốc khác) vào
    assert set(d["ma_check"]) == {"C5.1", "C5.2", "C9.4", "C11.2"}
    assert "kết chuyển" in d["thong_diep"].lower()


def test_chi_kich_hoat_khi_co_bang_chung_truc_tiep_c94():
    """C11.2 biên cao MỘT MÌNH chưa đủ kết luận 'chưa kết chuyển' — cần C9.4 hoặc C5.x
    làm bằng chứng trực tiếp TK 5–9 còn dư. Không thì đừng đoán."""
    kq = _kq({"C11.2": 1})
    assert chan_doan.chan_doan(kq) == []


def test_khong_gop_c95_vao_ket_chuyen():
    """C9.5 (bảng kê thiếu chứng từ) là vấn đề riêng, phải đứng một mình."""
    kq = _kq({"C9.4": 24, "C9.5": 4})
    cd = chan_doan.chan_doan(kq)
    assert len(cd) == 1 and "C9.5" not in cd[0]["ma_check"]
