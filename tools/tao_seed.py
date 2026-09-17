"""Dựng thư mục _seed đóng kèm bộ cài: kho CĐPS + tên chi nhánh + khung thư mục.

"Cài xong là vận hành được luôn": bản cài không kèm bảng kê chứng từ (file thật
121–132 MB, là dữ liệu hằng tháng của người dùng), nhưng kho CHỐT SỔ đã có sẵn:
- bảng quy đổi mã chi nhánh -> tên,
- toàn bộ CĐPS đã nạp (đủ các kỳ trong thư mục nguồn),
để mở lên đã thấy "Đã có CĐPS cho N kỳ/chi nhánh", chỉ cần thả bảng kê vào là kiểm.

Chạy: python -m tools.tao_seed   (từ thư mục gốc repo)
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

from app import cdps                                  # noqa: E402
from app.cau_hinh import KHOA_MAP, MAC_DINH           # noqa: E402
from app.kho import KhoChotSo                         # noqa: E402

# Tên hiển thị 8 chi nhánh — nguồn sự thật của bản cài (khớp cấu hình đang dùng).
QUY_DOI = {"A01": "Hà Nội", "A02": "Vĩnh Phúc", "A03": "Bắc Giang", "A04": "Hồ Chí Minh",
           "A05": "Long An", "A06": "An Giang", "A07": "Đắc Lắc", "A08": "Nhựa Long An"}
THU_MUC_CDPS = GOC / "1. Source" / "BANG CAN DOI PHAT SINH"


def dung(seed: Path) -> None:
    if seed.exists():
        shutil.rmtree(seed)
    for ten in MAC_DINH.values():                      # 1. Source / 2. Report / 3. Chot so
        (seed / ten).mkdir(parents=True, exist_ok=True)

    duong_kho = seed / MAC_DINH["thu_muc_kho"] / "kho_chot_so.sqlite"
    kho = KhoChotSo(str(duong_kho))
    try:
        kho.ghi_quy_doi(QUY_DOI)
        n = 0
        for p in sorted(THU_MUC_CDPS.glob("*.xlsx")):
            if cdps.suy_branch_ky(str(p)) is None:
                continue
            df, m = cdps.doc_cdps(str(p))
            kho.luu_cdps(m.ma, m.nam, m.thang, df)
            n += 1
    finally:
        kho.dong()

    # cau-hinh.json: thư mục mặc định + bảng quy đổi (app di trú JSON->kho nếu cần).
    cfg = dict(MAC_DINH); cfg[KHOA_MAP] = QUY_DOI
    (seed / "cau-hinh.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2),
                                        encoding="utf-8")

    # Kèm CĐPS gốc để người dùng thử lại luồng "nạp lại CĐPS" (nhẹ, ~450 KB).
    dich_cdps = seed / MAC_DINH["thu_muc_nguon"] / "BANG CAN DOI PHAT SINH"
    dich_cdps.mkdir(parents=True, exist_ok=True)
    for p in THU_MUC_CDPS.glob("*.xlsx"):
        shutil.copy2(p, dich_cdps / p.name)

    (seed / MAC_DINH["thu_muc_nguon"] / "ĐỌC TRƯỚC.txt").write_text(
        "Thả file Bảng kê chứng từ (xuất từ Bravo) vào thư mục này rồi bấm Kiểm tra.\n"
        "Kho đã có sẵn Cân đối phát sinh của các kỳ — không cần nạp lại.\n",
        encoding="utf-8")
    print(f"Seed xong: {seed}  ({n} CĐPS, {len(QUY_DOI)} chi nhánh)")


if __name__ == "__main__":
    dung(GOC / "build" / "_seed")
