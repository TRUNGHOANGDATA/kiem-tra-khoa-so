"""Kiểm thử end-to-end trên file thật (Bang ke chung tu 082027.xlsx).

Bỏ qua tự động nếu không có file thật trong '1. Source' — máy CI/máy khác không
có file này vẫn chạy được toàn bộ suite còn lại.
"""
import os
import time

import pytest

from app.api import JsApi

FILE = "1. Source/Bang ke chung tu 082027.xlsx"
pytestmark = pytest.mark.skipif(not os.path.exists(FILE), reason="không có file thật")


def test_pipeline_file_that_chay_nhanh_va_hop_ly(tmp_path):
    api = JsApi()
    api.thu_muc_report = str(tmp_path)
    # Cô lập KHO: nếu dùng kho thật của máy dev, CĐPS đã nạp ở đó sẽ bật G9/G10 và
    # con_viec đổi theo dữ liệu từng máy -> test mất tính tất định.
    api._thu_muc_kho = str(tmp_path / "kho")
    t = time.time()
    kq = api.chay_kiem_tra(FILE)
    assert "loi" not in kq, kq.get("loi")
    thoi_gian = time.time() - t
    assert kq["tomtat"]["ky"] == "08/2026" and kq["tomtat"]["so_dong"] == 79450
    assert len(kq["trang_thai"]) == 18
    # G4/G5 phải phản ánh dữ liệu thật: có phát sinh 621/632 nên không "không áp dụng"
    tt = {b["buoc"]: b for b in kq["trang_thai"]}
    assert tt["Tập hợp CP NVL trực tiếp 621 → 154"]["trang_thai"] != "khong_ap_dung"
    assert tt["Kết chuyển giá vốn 632 → 911"]["trang_thai"] != "khong_ap_dung"
    # C4.1: 10 dòng cuối nó còn báo trên sổ này đều mang số tiền ÂM (bút toán
    # điều chỉnh "TĐ từ phiếu TP số: TP2608-…"), tức là ĐÃ có giá trị. Vị từ
    # Amount == 0 phải đưa về 0 dòng và bước tính giá xuất kho về "đã làm".
    # C1.5 nay chỉ ĐỎ khi Amount == 0 (dòng không giá trị); các dòng ÂM (điều chỉnh/
    # kiểm kê) chuyển sang C1.7 THỐNG KÊ, không kéo kết luận.
    c41 = next(c for n in kq["nhom"] for c in n["checks"] if c["ma"] == "C4.1")
    c15 = next(c for n in kq["nhom"] for c in n["checks"] if c["ma"] == "C1.5")
    c17 = next(c for n in kq["nhom"] for c in n["checks"] if c["ma"] == "C1.7")
    assert c41["so_loi"] == 0 and c41["ghi_chu"] == ""
    assert c15["so_loi"] == 1              # đúng 1 dòng Amount = 0 trên sổ này
    assert c17["la_thong_ke"] is True and c17["so_loi"] == 0   # số âm chỉ để soát
    assert tt["Tính giá xuất kho (mọi dòng xuất có giá trị)"]["trang_thai"] == "da_lam"
    assert kq["tomtat"]["con_viec"] == 2 and kq["tomtat"]["so_chua_lam"] == 0
    # chi tiết theo trang không đổ toàn bộ
    ct = api.lay_chi_tiet("C1.1", 1, 100)
    assert len(ct["dong"]) <= 100 and ct["tong"] > 0
    path = api.xuat_bao_cao()["path"]
    assert os.path.exists(path)
    print(f"\nThời gian kiểm tra: {thoi_gian:.1f}s")
    assert thoi_gian < 60
