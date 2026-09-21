"""Logic chốt sổ: vân tay dữ liệu, đối chiếu bản đã chốt, sinh diff.

Thuần logic — không chạm SQLite (lớp kho ở app/kho) hay UI. Nhận DataFrame,
trả kết quả để api.py bơm ra giao diện. Dùng chung MỘT cách canonical hóa dòng
cho cả vân tay lẫn diff, nên 'giống nhau' được định nghĩa nhất quán ở một chỗ.
"""
from __future__ import annotations

import hashlib
from collections import Counter
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


KHOP, LECH, CHUA_CHOT = "KHOP", "LECH", "CHUA_CHOT"


@dataclass
class KetQuaDoiChieu:
    trang_thai: str
    delta_dong: int = 0
    delta_ps: float = 0.0
    so_ct_anh_huong: int = 0


def _so_ct(df: pd.DataFrame) -> pd.Series:
    """Nhãn chứng từ để gom hiển thị: DocCode+DocNo (chấp nhận thiếu cột)."""
    dc = df["DocCode"].astype("string").fillna("") if "DocCode" in df.columns \
        else pd.Series("", index=df.index, dtype="string")
    dn = df["DocNo"].astype("string").fillna("") if "DocNo" in df.columns \
        else pd.Series("", index=df.index, dtype="string")
    return dc.astype(str) + "·" + dn.astype(str)


def doi_chieu(vt_chot, df_hien_tai, df_chot=None) -> KetQuaDoiChieu:
    """So dữ liệu hiện tại với bản đã chốt. vt_chot=None → CHƯA_CHỐT (im lặng)."""
    if vt_chot is None:
        return KetQuaDoiChieu(CHUA_CHOT)
    vt_moi = van_tay(df_hien_tai)
    if vt_moi.ma_bam == vt_chot.ma_bam:
        return KetQuaDoiChieu(KHOP)
    delta_dong = vt_moi.so_dong - vt_chot.so_dong
    delta_ps = round(vt_moi.tong_ps - vt_chot.tong_ps, 2)
    so_ct = 0
    if df_chot is not None:
        d = dien_diff(df_chot, df_hien_tai)
        so_ct = d["tom_tat"]["so_ct_anh_huong"]
    return KetQuaDoiChieu(LECH, delta_dong, delta_ps, so_ct)


def dien_diff(df_chot: pd.DataFrame, df_hien_tai: pd.DataFrame) -> dict:
    """Dòng THÊM (có ở hiện tại, không ở bản chốt) và BỚT (ngược lại) theo hiệu đa tập.

    Băm cả dòng (không phụ thuộc khóa chứng từ — vốn có known-issue ghép không dấu
    tách), rồi gom hiển thị theo chứng từ để chỉ đúng chỗ.
    """
    df_chot = df_chot.reset_index(drop=True)
    df_hien_tai = df_hien_tai.reset_index(drop=True)
    key_chot = chuoi_dong(df_chot)
    key_moi = chuoi_dong(df_hien_tai)
    dem_chot, dem_moi = Counter(key_chot.tolist()), Counter(key_moi.tolist())
    du_moi = dem_moi - dem_chot   # thêm
    du_chot = dem_chot - dem_moi  # bớt

    def _lay(df, keys_series, con: Counter) -> pd.DataFrame:
        if not con:
            return df.iloc[0:0].copy()
        can = Counter(con)
        idx = []
        for i, k in enumerate(keys_series.tolist()):
            if can.get(k, 0) > 0:
                idx.append(keys_series.index[i])
                can[k] -= 1
        return df.loc[idx].reset_index(drop=True)

    them = _lay(df_hien_tai, key_moi, du_moi)
    bot = _lay(df_chot, key_chot, du_chot)
    ct = set(_so_ct(them).tolist()) | set(_so_ct(bot).tolist())
    tom_tat = {"so_them": int(len(them)), "so_bot": int(len(bot)),
               "so_ct_anh_huong": int(len([c for c in ct if c and c != "·"]))}
    return {"them": them, "bot": bot, "tom_tat": tom_tat}


def dien_diff_ct(df_chot: pd.DataFrame, df_hien_tai: pd.DataFrame) -> dict:
    """Phân loại thay đổi theo CHỨNG TỪ: thêm hẳn / bớt hẳn / bị SỬA.

    `dien_diff` trả về dòng thêm và dòng bớt rời rạc, nên một chứng từ bị sửa hiện ra
    thành "1 bớt + 1 thêm" và người đọc phải tự ghép lại. Ở đây gom theo DocCode+DocNo:
    chứng từ có mặt ở CẢ hai phía nghĩa là nó vẫn tồn tại nhưng nội dung đã đổi — đó là
    MỘT việc để rà, không phải hai.

    Dòng cũ/mới của chứng từ bị sửa chỉ gồm các DÒNG LỆCH (hiệu đa tập), không phải
    toàn bộ chứng từ — đúng chỗ kế toán cần soi. Không đoán cặp từng dòng nên không bao
    giờ ghép nhầm hai dòng vốn không liên quan (bảng kê không có số thứ tự dòng).
    """
    d = dien_diff(df_chot, df_hien_tai)
    ct_them, ct_bot = _so_ct(d["them"]), _so_ct(d["bot"])
    # Xét sự tồn tại trên FRAME ĐẦY ĐỦ, không trên kết quả diff: chứng từ chỉ được THÊM
    # một dòng (không bớt dòng nào) chỉ hiện ở phía "thêm" của diff, nhưng nó vẫn có mặt
    # trong bản chốt — đó là chứng từ bị SỬA, không phải chứng từ mới.
    co_o_chot, co_o_moi = set(_so_ct(df_chot)), set(_so_ct(df_hien_tai))
    # Chứng từ rỗng khóa ("·") không gom được -> để nguyên bên thêm/bớt, đừng ghép bừa.
    chung = {c for c in set(ct_them) | set(ct_bot)
             if c and c != "·" and c in co_o_chot and c in co_o_moi}
    sua = [{"so_ct": c,
            "dong_cu": d["bot"][ct_bot == c].reset_index(drop=True),
            "dong_moi": d["them"][ct_them == c].reset_index(drop=True)}
           for c in sorted(chung)]
    them = d["them"][~ct_them.isin(chung)].reset_index(drop=True)
    bot = d["bot"][~ct_bot.isin(chung)].reset_index(drop=True)
    return {"them": them, "bot": bot, "sua": sua,
            "tom_tat": {"ct_them": int(_so_ct(them).nunique()),
                        "ct_bot": int(_so_ct(bot).nunique()),
                        "ct_sua": len(chung)}}
