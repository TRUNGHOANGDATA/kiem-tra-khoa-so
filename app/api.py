"""Cầu nối JS ↔ Python cho pywebview (js_api)."""
from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from . import checks, report
from .checks.base import COT_SO_HIEN_THI, COT_SO_LE, THU_TU_MUC_DO, BoiCanh, CheckResult, ten_cot
from .loader import ThongTinFile, doc_nhieu_bang_ke, tim_file_excel, tim_file_moi_nhat
from .trang_thai import BuocKhoaSo, suy_trang_thai, tinh_ket_luan

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


def _dinh_dang_so(n: int) -> str:
    """1234567 -> '1.234.567' (kiểu Việt Nam), dùng cho thông báo tiến trình."""
    return f"{n:,}".replace(",", ".")


@dataclass
class DonVi:
    """Một đơn vị kế toán (một chi nhánh) cùng toàn bộ kết quả kiểm tra của riêng nó.

    Mỗi chi nhánh khóa sổ trên sổ của chính mình, nên mỗi đơn vị giữ frame riêng,
    30 kết quả kiểm tra riêng và 11 bước riêng — không có chỗ nào dùng chung.
    """
    df: pd.DataFrame
    tt: ThongTinFile
    kq: dict[str, CheckResult] = field(default_factory=dict)
    ket_qua: list[CheckResult] = field(default_factory=list)
    trang_thai: list[BuocKhoaSo] = field(default_factory=list)

    @property
    def nhan(self) -> str:
        """Nhãn hiển thị: mã chi nhánh khi có, ngược lại tên file."""
        return self.tt.chi_nhanh or self.tt.ten


class JsApi:
    def __init__(self):
        self._window = None
        self._dv: list[DonVi] = []
        self._i = 0
        self._duong_dan: list[str] = []
        self.thu_muc_source = THU_MUC_SOURCE
        self.thu_muc_report = THU_MUC_REPORT

    # ---- đơn vị đang xem ----
    # _df/_tt/_kq/… là khung nhìn vào đơn vị đang chọn: mọi phương thức viết cho
    # một chi nhánh (lay_chi_tiet, xuat_bao_cao, _tom_tat) chạy nguyên vẹn ở chế
    # độ nhiều chi nhánh mà không phải mang theo chỉ số đơn vị.
    @property
    def _hien(self) -> DonVi | None:
        return self._dv[self._i] if 0 <= self._i < len(self._dv) else None

    def _lay(self, ten: str, mac_dinh=None):
        d = self._hien
        return getattr(d, ten) if d else mac_dinh

    # Chỉ đọc, không có setter: gán vào một khung nhìn khi chưa nạp đơn vị nào sẽ
    # phải rơi vào hư không — đúng loại lỗi im lặng mà nhánh này đã trả giá nhiều
    # lần. Muốn đổi trạng thái thì đổi trên DonVi trong self._dv.
    _df = property(lambda self: self._lay("df"))
    _tt = property(lambda self: self._lay("tt"))
    _kq = property(lambda self: self._lay("kq", {}))
    _ket_qua = property(lambda self: self._lay("ket_qua", []))
    _trang_thai = property(lambda self: self._lay("trang_thai", []))

    # ---- cửa sổ & tiến trình ----
    def gan_window(self, window):
        self._window = window

    def _tien_trinh(self, ten: str, pct: int):
        if self._window is not None:
            self._window.evaluate_js(f"window.onTienTrinh && onTienTrinh({json.dumps(ten, ensure_ascii=False)}, {pct})")

    # ---- nạp file ----
    def _thong_tin_nap(self) -> dict:
        """Tóm tắt sau khi nạp — màn hình 1 dựng thẻ file/chi nhánh từ đây."""
        return {
            "path": self._duong_dan[0] if self._duong_dan else "",
            "cac_path": list(self._duong_dan),
            "so_file": len(self._duong_dan),
            "ten": " · ".join(d.nhan for d in self._dv),
            "ky": " · ".join(dict.fromkeys(d.tt.ky for d in self._dv)),
            "so_dong": sum(d.tt.so_dong for d in self._dv),
            "tong_ps": sum(d.tt.tong_ps for d in self._dv),
            "don_vi": [{"ma": d.nhan, "ky": d.tt.ky, "so_dong": d.tt.so_dong,
                        "tong_ps": d.tt.tong_ps, "nguon": d.tt.ten} for d in self._dv],
        }

    def _nap_nhieu(self, paths: list[str]) -> dict:
        # Đọc Excel là phần chậm (~85% thời gian chờ) và là MỘT lệnh pandas chặn luồng
        # — trong lúc nó chạy không thể tự báo tiến độ con. Vì vậy đọc trong luồng nền
        # còn luồng js_api ở đây đập nhịp mỗi ~0,35s: hiện tên file + ĐỒNG HỒ GIÂY để
        # người dùng thấy rõ đang chạy chứ không treo (trước đây chỉ có vệt sáng CSS
        # quay mà không một chữ nào đổi suốt 8-10 giây).
        tong = max(1, len(paths))
        tt_doc: dict = {"ten": "", "i": 0}

        def _bao(ten: str):
            tt_doc["i"] += 1
            tt_doc["ten"] = ten

        ket: dict = {}

        def _chay():
            try:
                ket["ds"] = doc_nhieu_bang_ke(paths, on_file=_bao)
            except Exception as e:  # noqa: BLE001  (chuyển lỗi về luồng chính để ném lại)
                ket["loi"] = e

        luong = threading.Thread(target=_chay, daemon=True)
        self._tien_trinh("Đang đọc dữ liệu từ Excel…", 0)
        luong.start()
        t0 = time.monotonic()
        while luong.is_alive():
            luong.join(timeout=0.35)
            giay = int(time.monotonic() - t0)
            if tong > 1 and tt_doc["ten"]:
                nhan = f"Đang đọc {tt_doc['ten']} ({tt_doc['i']}/{tong}) · {giay}s"
            else:
                nhan = f"Đang đọc dữ liệu từ Excel… · {giay}s"
            self._tien_trinh(nhan, 0)   # 0 -> chế độ không xác định (vệt sáng CSS chạy)
        if "loi" in ket:
            raise ket["loi"]

        self._dv = [DonVi(df, tt) for df, tt in ket["ds"]]
        self._i = 0
        self._duong_dan = list(paths)
        n = sum(d.tt.so_dong for d in self._dv)
        don_vi = f" · {len(self._dv)} chi nhánh" if len(self._dv) > 1 else ""
        self._tien_trinh(f"Đã đọc {_dinh_dang_so(n)} dòng{don_vi}", 85)
        return self._thong_tin_nap()

    def _nap_file(self, path: str) -> dict:
        return self._nap_nhieu([path])

    def _chay_mot_don_vi(self, d: DonVi, on_progress=None) -> None:
        """Chạy 30 check + suy 11 bước cho MỘT chi nhánh, trên frame của riêng nó."""
        ctx = BoiCanh(d.tt.ky_thang, d.tt.ky_nam)
        d.ket_qua = checks.chay_tat_ca(d.df, ctx, on_progress=on_progress)
        d.kq = {r.ma: r for r in d.ket_qua}
        d.trang_thai = suy_trang_thai(d.df, d.kq)

    def _chay_lai_kiem_tra(self, on_progress=None) -> None:
        """Chạy lại kiểm tra cho chi nhánh đang xem — dùng bởi cơ chế tự phục hồi
        của lay_chi_tiet khi cache kết quả bị xóa nhưng dữ liệu vẫn còn."""
        if self._hien is not None:
            self._chay_mot_don_vi(self._hien, on_progress=on_progress)

    def _tien_trinh_kiem_tra(self, ti_le_bat_dau: int, khoang: int | None = None, nhan_them: str = ""):
        """Bọc on_progress của chay_tat_ca (0..100 theo 6 nhóm) vào khoảng
        [ti_le_bat_dau, ti_le_bat_dau + khoang] của thanh tiến trình tổng — để phần
        đọc file (nếu vừa đọc lại) và từng chi nhánh cùng chia sẻ một thanh theo
        đúng tỉ lệ thời gian, thay vì mỗi chi nhánh lại kéo thanh về 0."""
        rong = (100 - ti_le_bat_dau) if khoang is None else khoang

        def _goi(ten: str, pct: int):
            xong = ti_le_bat_dau + rong >= 100 and pct >= 100
            nhan = "Hoàn tất" if xong else f"Đang kiểm tra: {nhan_them}{ten}…"
            self._tien_trinh(nhan, ti_le_bat_dau + pct * rong // 100)
        return _goi

    def lay_file_moi_nhat(self):
        p = tim_file_moi_nhat(self.thu_muc_source)
        if not p:
            return None
        try:
            return self._nap_file(p)
        except Exception as e:  # noqa: BLE001
            return {"loi": str(e), "path": p}

    def nap_file(self, path: str):
        return self.nap_nhieu_file([path])

    def nap_nhieu_file(self, paths):
        try:
            ds = [p for p in (paths or []) if p]
            if not ds:
                return {"loi": "Chưa chọn file bảng kê nào"}
            return self._nap_nhieu(ds)
        except Exception as e:  # noqa: BLE001
            return {"loi": str(e)}

    def quet_thu_muc(self):
        """Nạp mọi bảng kê trong '1. Source' — lối vào nhanh khi mỗi chi nhánh một file."""
        ds = tim_file_excel(self.thu_muc_source)
        if not ds:
            return {"loi": "Thư mục '1. Source' chưa có file bảng kê nào"}
        return self.nap_nhieu_file(ds)

    def chon_file(self, nhieu: bool = False):
        if self._window is None:
            return {"loi": "Chưa có cửa sổ"}
        try:
            import webview
            loai = getattr(getattr(webview, "FileDialog", None), "OPEN", None) or webview.OPEN_DIALOG
            chon = self._window.create_file_dialog(loai, directory=self.thu_muc_source,
                                                   allow_multiple=bool(nhieu),
                                                   file_types=("Excel (*.xlsx;*.xls;*.xlsm)",))
            if not chon:
                return None
            return self.nap_nhieu_file(list(chon))
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không mở được hộp thoại chọn file: {e}"}

    def chon_nhieu_file(self):
        return self.chon_file(nhieu=True)

    # ---- kiểm tra ----
    def chay_kiem_tra(self, path=None):
        """`path` là một đường dẫn hoặc cả danh sách đường dẫn mà màn hình 1 đang giữ."""
        try:
            # Đã xác nhận trên file thật: chuỗi path do lay_file_moi_nhat/chon_file/nap_file
            # trả về luôn được _nap_nhieu lưu y hệt vào self._duong_dan, và JS chỉ lưu rồi trả
            # lại nguyên văn (JSON round-trip không đổi nội dung chuỗi) — nên so sánh chuỗi
            # trực tiếp là đủ, không cần chuẩn hóa (xem docs/ket-qua/sua-tien-trinh-va-trang-thai.md).
            #
            # So sánh CẢ DANH SÁCH: nhận mỗi đường dẫn đầu rồi nạp lại một mình nó sẽ
            # lặng lẽ vứt bỏ các chi nhánh còn lại mà màn hình 1 vừa báo là đã nạp.
            ds = [path] if isinstance(path, str) else list(path or [])
            vua_doc_lai = False
            if ds and self._duong_dan != ds:
                self._nap_nhieu(ds)
                vua_doc_lai = True
            if not self._dv:
                return {"loi": "Chưa chọn file bảng kê"}
            # Nếu vừa đọc lại file, phần đọc đã chiếm 0-85% thanh tiến trình —
            # phần kiểm tra chỉ còn 85-100%. Nếu file đã có sẵn (trường hợp thường
            # gặp khi bấm "Kiểm tra" ngay sau khi màn 1 đã nạp xong), kiểm tra là
            # toàn bộ việc của lần gọi này nên được trọn 0-100%.
            dau = 85 if vua_doc_lai else 0
            # Nhiều chi nhánh: mỗi chi nhánh chiếm một lát bằng nhau của phần còn lại,
            # để thanh không nhảy về 0 mỗi lần sang chi nhánh mới.
            n = len(self._dv)
            for i, d in enumerate(self._dv):
                rong = (100 - dau) // n
                nhan = f"[{d.nhan}] " if n > 1 else ""
                self._chay_mot_don_vi(d, self._tien_trinh_kiem_tra(dau + rong * i, rong, nhan))
            self._i = min(self._i, n - 1)
            return self._tom_tat()
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không đọc/kiểm tra được file: {e}"}

    def chon_don_vi(self, chi_so: int):
        """Chuyển sang xem chi nhánh khác — trả về đúng gói dữ liệu như chay_kiem_tra."""
        try:
            i = int(chi_so)
        except (TypeError, ValueError):
            return {"loi": "Chỉ số chi nhánh không hợp lệ"}
        if not 0 <= i < len(self._dv):
            return {"loi": "Không có chi nhánh này"}
        self._i = i
        if not self._dv[i].ket_qua:
            self._chay_mot_don_vi(self._dv[i])
        return self._tom_tat()

    def _tom_tat(self) -> dict:
        ket_luan = tinh_ket_luan(self._ket_qua, self._trang_thai)
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
                       "chi_nhanh": self._hien.nhan, **ket_luan},
            "trang_thai": [{"buoc": b.buoc, "trang_thai": b.trang_thai, "tom_tat": b.tom_tat,
                            "ma_check": b.ma_check, "co_chung_cu": b.co_chung_cu}
                           for b in self._trang_thai],
            "nhom": nhom,
            "don_vi": self._danh_sach_don_vi(),
            "dang_xem": self._i,
        }

    def _danh_sach_don_vi(self) -> list[dict]:
        """Một dòng kết luận cho mỗi chi nhánh — thanh chọn chi nhánh và sheet tổng
        hợp cùng đọc từ đây, nên hai nơi không thể nói lệch nhau."""
        ds = []
        for i, d in enumerate(self._dv):
            kl = tinh_ket_luan(d.ket_qua, d.trang_thai) if d.ket_qua else {}
            ds.append({"i": i, "ma": d.nhan, "ky": d.tt.ky, "so_dong": d.tt.so_dong,
                       "tong_ps": d.tt.tong_ps, "nguon": d.tt.ten, "da_chay": bool(d.ket_qua),
                       **kl})
        return ds

    def lay_chi_tiet(self, ma_check: str, trang: int = 1, kich_thuoc: int = 100, tim_kiem: str = ""):
        r = self._kq.get(ma_check)
        if r is None:
            # _kq có thể đã bị xóa (nạp file khác) trong khi màn hình vẫn còn hiển thị
            # kết quả cũ — tự chạy lại kiểm tra từ dữ liệu đã đọc sẵn thay vì báo lỗi
            # bằng mã nội bộ mà người dùng không hiểu được.
            if self._df is None or self._tt is None:
                return {"loi": "Chưa có dữ liệu — hãy chọn file và bấm Kiểm tra"}
            self._chay_lai_kiem_tra()
            r = self._kq.get(ma_check)
            if r is None:
                return {"loi": f"Không tìm thấy kết quả {ma_check} sau khi chạy lại kiểm tra"}
        df = _dinh_dang_ngay(r.chi_tiet)
        if tim_kiem:
            tk = tim_kiem.lower()
            mask = df.astype(str).apply(lambda s: s.str.lower().str.contains(tk, regex=False)).any(axis=1)
            df = df[mask]
        tong = int(len(df))
        kich_thuoc = max(1, min(int(kich_thuoc), 500))
        a = max(0, (int(trang) - 1) * kich_thuoc)
        cot = list(df.columns)
        # Nhãn tiếng Việt và danh sách cột số đi kèm dữ liệu, không nhân bản sang JS.
        return {"tong": tong, "trang": int(trang), "cot": cot, "nhan": ten_cot(cot),
                "cot_so": [c for c in cot if c in COT_SO_HIEN_THI],
                "cot_so_le": [c for c in cot if c in COT_SO_LE],
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

    def xuat_tong_hop(self):
        """Một workbook cho toàn bộ chi nhánh: sheet so sánh + tổng quan & 11 bước
        của từng chi nhánh. Chi tiết từng dòng vi phạm vẫn nằm ở báo cáo riêng của
        chi nhánh — 30 check × N chi nhánh vượt xa giới hạn sheet của Excel."""
        chua = [d.nhan for d in self._dv if not d.ket_qua]
        if not self._dv or chua:
            return {"loi": "Chưa chạy kiểm tra" + (f" cho: {', '.join(chua)}" if chua else "")}
        try:
            p = report.xuat_tong_hop(
                [(d.nhan, d.ket_qua, d.trang_thai, d.tt) for d in self._dv], self.thu_muc_report)
            return {"path": p}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không xuất được báo cáo tổng hợp: {e}"}

    # Mọi phương thức công khai đều trả lỗi thay vì ném — phía JS không bắt reject,
    # người dùng đã xóa/di chuyển file mà bấm "Mở file Excel" sẽ im lặng hoàn toàn.
    def mo_file(self, path: str):
        try:
            os.startfile(path)  # noqa: S606
            return True
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không mở được file: {e}"}

    def mo_thu_muc(self, path: str):
        try:
            p = Path(path)
            if p.is_file():
                subprocess.Popen(["explorer", "/select,", str(p)])  # noqa: S603,S607
            else:
                os.startfile(str(p))  # noqa: S606
            return True
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không mở được thư mục: {e}"}
