"""Cầu nối JS ↔ Python cho pywebview (js_api)."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pandas as pd

from . import checks, report
from .checks.base import DO, VANG, THU_TU_MUC_DO, BoiCanh, CheckResult
from .loader import ThongTinFile, doc_bang_ke, tim_file_moi_nhat
from .trang_thai import suy_trang_thai

GOC = Path(__file__).resolve().parents[1]
THU_MUC_SOURCE = str(GOC / "1. Source")
THU_MUC_REPORT = str(GOC / "2. Report")


def _dinh_dang_ngay(df: pd.DataFrame) -> pd.DataFrame:
    """Đổi cột ngày sang dd/mm/yyyy — dùng chung cho cả tìm kiếm và hiển thị."""
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].dt.strftime("%d/%m/%Y")
    return df


def _records(df: pd.DataFrame) -> list[dict]:
    return json.loads(_dinh_dang_ngay(df).to_json(orient="records", force_ascii=False))


class JsApi:
    def __init__(self):
        self._window = None
        self._df: pd.DataFrame | None = None
        self._tt: ThongTinFile | None = None
        self._kq: dict[str, CheckResult] = {}
        self._ket_qua: list[CheckResult] = []
        self._trang_thai = []
        self.thu_muc_source = THU_MUC_SOURCE
        self.thu_muc_report = THU_MUC_REPORT

    # ---- cửa sổ & tiến trình ----
    def gan_window(self, window):
        self._window = window

    def _tien_trinh(self, ten: str, pct: int):
        if self._window is not None:
            self._window.evaluate_js(f"window.onTienTrinh && onTienTrinh({json.dumps(ten, ensure_ascii=False)}, {pct})")

    # ---- nạp file ----
    def _nap_file(self, path: str) -> dict:
        self._df, self._tt = doc_bang_ke(path)
        self._kq, self._ket_qua, self._trang_thai = {}, [], []
        t = self._tt
        return {"path": t.path, "ten": t.ten, "ky": t.ky, "so_dong": t.so_dong, "tong_ps": t.tong_ps}

    def lay_file_moi_nhat(self):
        p = tim_file_moi_nhat(self.thu_muc_source)
        if not p:
            return None
        try:
            return self._nap_file(p)
        except Exception as e:  # noqa: BLE001
            return {"loi": str(e), "path": p}

    def nap_file(self, path: str):
        try:
            return self._nap_file(path)
        except Exception as e:  # noqa: BLE001
            return {"loi": str(e)}

    def chon_file(self):
        if self._window is None:
            return {"loi": "Chưa có cửa sổ"}
        try:
            import webview
            loai = getattr(getattr(webview, "FileDialog", None), "OPEN", None) or webview.OPEN_DIALOG
            chon = self._window.create_file_dialog(loai, directory=self.thu_muc_source,
                                                   file_types=("Excel (*.xlsx;*.xls;*.xlsm)",))
            if not chon:
                return None
            return self.nap_file(chon[0])
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không mở được hộp thoại chọn file: {e}"}

    # ---- kiểm tra ----
    def chay_kiem_tra(self, path: str | None = None):
        try:
            if path and (self._tt is None or self._tt.path != path):
                self._nap_file(path)
            if self._df is None:
                return {"loi": "Chưa chọn file bảng kê"}
            ctx = BoiCanh(self._tt.ky_thang, self._tt.ky_nam)
            self._ket_qua = checks.chay_tat_ca(self._df, ctx, on_progress=self._tien_trinh)
            self._kq = {r.ma: r for r in self._ket_qua}
            self._trang_thai = suy_trang_thai(self._df, self._kq)
            return self._tom_tat()
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không đọc/kiểm tra được file: {e}"}

    def _tom_tat(self) -> dict:
        loi = [r for r in self._ket_qua if not r.la_thong_ke]
        so_do = sum(r.muc_do_thuc == DO for r in loi)
        so_vang = sum(r.muc_do_thuc == VANG for r in loi)
        chua = sum(b.trang_thai == "chua_lam" for b in self._trang_thai)
        nhom = []
        for ma, ten in checks.TEN_NHOM.items():
            cs = [r for r in self._ket_qua if r.nhom == ma]
            khong_tk = [r for r in cs if not r.la_thong_ke]
            muc = min((r.muc_do_thuc for r in khong_tk), key=THU_TU_MUC_DO.get, default="xanh")
            nhom.append({"ma": ma, "ten": ten, "so_loi": sum(r.so_loi for r in khong_tk), "muc_do": muc,
                         "checks": [{"ma": r.ma, "ten": r.ten, "muc_do": r.muc_do_thuc, "so_loi": r.so_loi,
                                     "la_thong_ke": r.la_thong_ke, "ghi_chu": r.ghi_chu} for r in cs]})
        t = self._tt
        return {
            "tomtat": {"ky": t.ky, "ten": t.ten, "so_dong": t.so_dong, "tong_ps": t.tong_ps,
                       "so_do": so_do, "so_vang": so_vang, "so_chua_lam": chua,
                       "con_viec": so_do + chua, "san_sang": so_do == 0 and chua == 0},
            "trang_thai": [{"buoc": b.buoc, "trang_thai": b.trang_thai, "tom_tat": b.tom_tat,
                            "ma_check": b.ma_check} for b in self._trang_thai],
            "nhom": nhom,
        }

    def lay_chi_tiet(self, ma_check: str, trang: int = 1, kich_thuoc: int = 100, tim_kiem: str = ""):
        r = self._kq.get(ma_check)
        if r is None:
            return {"loi": f"Không có kết quả {ma_check}"}
        df = _dinh_dang_ngay(r.chi_tiet)
        if tim_kiem:
            tk = tim_kiem.lower()
            mask = df.astype(str).apply(lambda s: s.str.lower().str.contains(tk, regex=False)).any(axis=1)
            df = df[mask]
        tong = int(len(df))
        kich_thuoc = max(1, min(int(kich_thuoc), 500))
        a = max(0, (int(trang) - 1) * kich_thuoc)
        return {"tong": tong, "trang": int(trang), "cot": list(df.columns),
                "dong": json.loads(df.iloc[a:a + kich_thuoc].to_json(orient="records", force_ascii=False))}

    # ---- xuất & mở ----
    def xuat_bao_cao(self):
        if not self._ket_qua:
            return {"loi": "Chưa chạy kiểm tra"}
        try:
            p = report.xuat_bao_cao(self._ket_qua, self._trang_thai, self._tt, self.thu_muc_report)
            return {"path": p}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không xuất được báo cáo: {e}"}

    def mo_file(self, path: str):
        os.startfile(path)  # noqa: S606
        return True

    def mo_thu_muc(self, path: str):
        p = Path(path)
        if p.is_file():
            subprocess.Popen(["explorer", "/select,", str(p)])  # noqa: S603,S607
        else:
            os.startfile(str(p))  # noqa: S606
        return True
