"""Chẩn đoán: gộp nhiều cảnh báo CÙNG MỘT GỐC thành một thông điệp cho kế toán.

Nhiều check là các TRIỆU CHỨNG khác nhau của cùng một nguyên nhân. Bắt kế toán đọc
rời từng cái rồi tự nối lại là bắt họ làm việc của tool. Lớp này nhận diện các mẫu
đã biết và nêu một câu hành động.

Luật thiết kế giữ nguyên: chỉ gộp khi có BẰNG CHỨNG TRỰC TIẾP cho gốc chung (không
suy từ một triệu chứng mơ hồ), và không kéo check thuộc gốc KHÁC vào cho đủ số.
"""
from __future__ import annotations

from .checks.base import CheckResult

# Kết chuyển cuối kỳ: C5.x là bằng chứng trực tiếp (thiếu bút toán kết chuyển),
# C9.4 là bằng chứng trực tiếp (TK 5–9 còn dư cuối kỳ). C11.2 (biên gộp cao) chỉ là
# HỆ QUẢ — chỉ gộp khi đã có ít nhất một bằng chứng trực tiếp, không tự đứng làm gốc.
_KET_CHUYEN_TRUC_TIEP = ("C5.1", "C5.2", "C5.3", "C5.4", "C5.5", "C5.6", "C9.4")
_KET_CHUYEN_HE_QUA = ("C11.2",)


def _co_loi(kq: dict[str, CheckResult], ma: str) -> bool:
    r = kq.get(ma)
    return r is not None and r.so_loi > 0


def chan_doan(ket_qua: list[CheckResult]) -> list[dict]:
    """Trả các chẩn đoán khớp. Mỗi cái: {ma, thong_diep, ma_check, muc_do}."""
    kq = {r.ma: r for r in ket_qua}
    ds = []

    truc_tiep = [m for m in _KET_CHUYEN_TRUC_TIEP if _co_loi(kq, m)]
    if truc_tiep:
        # Hệ quả chỉ tính khi TK 5–9 thật sự còn dư/thiếu kết chuyển (đã có bằng chứng).
        he_qua = [m for m in _KET_CHUYEN_HE_QUA if m in kq]
        ds.append({
            "ma": "chua_ket_chuyen",
            "muc_do": "do",
            "ma_check": truc_tiep + he_qua,
            "thong_diep": (
                "Kỳ CHƯA thực hiện xong bút toán kết chuyển cuối kỳ — nhiều cảnh báo dưới "
                "đây cùng một nguyên nhân này (TK doanh thu/chi phí loại 5–9 còn số dư, biên "
                "lợi nhuận gộp vì thế cao bất thường). Làm kết chuyển 5→911, 6→154/911, "
                "9→421 cho xong rồi kiểm tra lại; phần lớn cảnh báo sẽ tự hết."),
        })
    return ds
