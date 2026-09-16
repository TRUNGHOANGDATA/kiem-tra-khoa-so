"""Logic chốt sổ: vân tay dữ liệu, đối chiếu bản đã chốt, sinh diff.

Thuần logic — không chạm SQLite (lớp kho ở app/kho) hay UI. Nhận DataFrame,
trả kết quả để api.py bơm ra giao diện. Dùng chung MỘT cách canonical hóa dòng
cho cả vân tay lẫn diff, nên 'giống nhau' được định nghĩa nhất quán ở một chỗ.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import reduce

import pandas as pd

NGAN = "\x01"  # ngăn cách cột trong một dòng — ký tự không xuất hiện trong dữ liệu kế toán


def chuoi_dong(df: pd.DataFrame) -> pd.Series:
    """Chuỗi canonical cho từng dòng (vectorized, chịu được 80k dòng).

    Cùng dữ liệu → cùng chuỗi, kể cả sau khi lưu/đọc lại qua JSON. Số thực làm
    tròn 4 chữ số (đủ phân biệt tiền/số lượng, tránh nhiễu số dấu phẩy động);
    ngày về 'yyyy-mm-dd'; NaN về rỗng.

    Lưu ý round-trip JSON: `pd.read_json` mặc định tự suy luận kiểu cột — cột
    số thực toàn giá trị nguyên (vd Amount=100.0) đọc lại thành int64, cột
    ngày giờ đọc lại thành chuỗi ISO thô (không tự parse về datetime). Nếu chỉ
    xét theo dtype thì cùng một dữ liệu sẽ ra chuỗi khác nhau trước/sau khi
    lưu — nên với cột dạng chuỗi/object, thử ép về số rồi về ngày trước khi
    coi là văn bản thuần, để 'giống nhau' ổn định qua lưu/đọc.
    """
    if len(df) == 0:
        return pd.Series([], dtype="string")
    cols = sorted(map(str, df.columns))
    phan = []
    for c in cols:
        s = df[c]
        if pd.api.types.is_datetime64_any_dtype(s):
            gt = s.dt.strftime("%Y-%m-%d").fillna("")
        elif pd.api.types.is_numeric_dtype(s):
            gt = s.map(lambda x: "" if pd.isna(x) else f"{float(x):.4f}")
        else:
            so = pd.to_numeric(s, errors="coerce")
            if len(s) and so.notna().all():
                gt = so.map(lambda x: "" if pd.isna(x) else f"{float(x):.4f}")
            else:
                # format="ISO8601" tránh pandas phải "đoán" định dạng (gây UserWarning
                # khi -W error bật) — chỉ khớp đúng chuỗi ISO do to_json(date_format="iso") sinh ra.
                ngay = pd.to_datetime(s, errors="coerce", format="ISO8601")
                if len(s) and ngay.notna().all():
                    gt = ngay.dt.strftime("%Y-%m-%d").fillna("")
                else:
                    gt = s.astype("string").fillna("")
        phan.append(c + "=" + gt.astype("string"))
    return reduce(lambda a, b: a + NGAN + b, phan)


@dataclass
class VanTay:
    so_dong: int
    tong_ps: float
    ma_bam: str


def van_tay(df: pd.DataFrame) -> VanTay:
    """Vân tay của một frame: số dòng, tổng phát sinh, mã băm sha256 độc lập thứ tự dòng."""
    dong = sorted(chuoi_dong(df).tolist())
    ma = hashlib.sha256("\n".join(dong).encode("utf-8")).hexdigest()
    tong = float(df["Amount"].sum()) if "Amount" in df.columns and len(df) else 0.0
    return VanTay(so_dong=int(len(df)), tong_ps=tong, ma_bam=ma)
