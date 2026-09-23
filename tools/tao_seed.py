"""Dựng thư mục _seed đóng kèm bộ cài: bảng quy đổi tên chi nhánh + khung thư mục.

"Cài xong là vận hành được luôn" nhưng KHÔNG nhúng dữ liệu tài chính thật: bản cài
không kèm bảng kê chứng từ (file thật 121–132 MB, dữ liệu hằng tháng của người
dùng) và cũng không kèm CĐPS (số liệu thật của khách hàng). Kho CHỐT SỔ chỉ có sẵn
bảng quy đổi mã chi nhánh -> tên (đọc từ `chi_nhanh.json`, file local/gitignore).
Lần đầu mở app, người dùng tự nạp CĐPS của mình.

Chạy: python -m tools.tao_seed   (từ thư mục gốc repo)
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

from app.cau_hinh import KHOA_MAP, MAC_DINH           # noqa: E402
from app.kho import KhoChotSo                         # noqa: E402

# Tên chi nhánh thật KHÔNG nhúng vào mã public — đọc từ file local (gitignore).
FILE_CHI_NHANH = GOC / "chi_nhanh.json"


def _quy_doi() -> dict:
    """Tên chi nhánh đọc từ file local (gitignore) — không nhúng vào mã public."""
    return json.loads(FILE_CHI_NHANH.read_text(encoding="utf-8"))


def dung(seed: Path) -> None:
    if seed.exists():
        shutil.rmtree(seed)
    for ten in MAC_DINH.values():                      # 1. Source / 2. Report / 3. Chot so
        (seed / ten).mkdir(parents=True, exist_ok=True)

    quy_doi = _quy_doi()
    duong_kho = seed / MAC_DINH["thu_muc_kho"] / "kho_chot_so.sqlite"
    kho = KhoChotSo(str(duong_kho))
    try:
        kho.ghi_quy_doi(quy_doi)
    finally:
        kho.dong()

    # cau-hinh.json: thư mục mặc định + bảng quy đổi (app di trú JSON->kho nếu cần).
    cfg = dict(MAC_DINH); cfg[KHOA_MAP] = quy_doi
    (seed / "cau-hinh.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2),
                                        encoding="utf-8")

    # Thư mục rỗng bị PyInstaller/Inno bỏ rơi -> đặt một file ghi chú để "2. Report"
    # ship được ngay (app cũng tự tạo khi cần, đây chỉ để có sẵn từ lúc cài).
    (seed / MAC_DINH["thu_muc_xuat"] / "ĐỌC TRƯỚC.txt").write_text(
        "Báo cáo Excel khi bấm Xuất sẽ nằm ở đây.\n", encoding="utf-8")

    (seed / MAC_DINH["thu_muc_nguon"] / "ĐỌC TRƯỚC.txt").write_text(
        "Thả file Bảng kê chứng từ (xuất từ Bravo) vào thư mục này rồi bấm Kiểm tra.\n"
        "Lần đầu dùng: nạp Cân đối phát sinh (CĐPS) của bạn trước khi kiểm.\n",
        encoding="utf-8")
    print(f"Seed xong: {seed}  ({len(quy_doi)} chi nhánh, không kèm CĐPS)")


if __name__ == "__main__":
    # stdout mặc định của console Windows (cp1252) không mã hoá được 'Đ'/dấu tiếng
    # Việt trong dòng thông báo -> ép utf-8 để không rớt build vì một câu print.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    dung(GOC / "build" / "_seed")
