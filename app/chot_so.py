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

    Cùng dữ liệu → cùng chuỗi, kể cả sau khi lưu/đọc lại qua JSON (lớp lưu trữ
    dùng `orient="table"`, giữ nguyên dtype khi đọc lại — nên ở đây không cần
    "đoán" kiểu cho cột dạng chuỗi). Số thực làm tròn 4 chữ số (đủ phân biệt
    tiền/số lượng, tránh nhiễu số dấu phẩy động); ngày về 'yyyy-mm-dd'; NaN về
    rỗng. Cột chuỗi giữ NGUYÊN VĂN — vd DocNo "0001" phải khác "1" (số 0 đầu
    có ý nghĩa với số chứng từ), nên tuyệt đối không ép cột chuỗi về số/ngày.
    """
    if len(df) == 0:
        return pd.Series([], dtype="string")
    cols = sorted(map(str, df.columns))
    phan = []
    for c in cols:
        s = df[c]
        if pd.api.types.is_datetime64_any_dtype(s):
            gt = s.dt.strftime("%Y-%m-%d").fillna("")
        elif pd.api.types.is_float_dtype(s):
            gt = s.map(lambda x: "" if pd.isna(x) else f"{x:.4f}")
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
