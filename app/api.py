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

from . import cau_hinh, cdps, chan_doan, checks, chot_so, duong_dan, report
from .checks.base import (COT_SO_LE, THU_TU_MUC_DO, BoiCanh, CheckResult, cot_so_cua,
                          doi_bool, ten_cot)
from .kho import KhoChotSo, PhienBanMoiHon, sao_luu as kho_sao_luu
from .loader import ThongTinFile, doc_nhieu_bang_ke, tim_file_excel, tim_file_moi_nhat
from .trang_thai import BuocKhoaSo, suy_trang_thai, tinh_ket_luan

# Gốc DỮ LIỆU (cấu hình/kho/báo cáo). Bản đóng gói trỏ sang thư mục người dùng;
# chạy mã nguồn trỏ vào repo. Test vẫn patch được `app.api.GOC` như cũ.
GOC = duong_dan.thu_muc_du_lieu()


def _dinh_dang_ngay(df: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hoá bảng trước khi cho người dùng xem: ngày dd/mm/yyyy, lô-gic Có/Không.

    Một chỗ duy nhất cho mọi bảng chứng minh — tìm kiếm cũng chạy trên bản đã đổi nên
    gõ "Có" tìm được đúng dòng.
    """
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].dt.strftime("%d/%m/%Y")
    return doi_bool(df)


def _dinh_dang_so(n: int) -> str:
    """1234567 -> '1.234.567' (kiểu Việt Nam), dùng cho thông báo tiến trình."""
    return f"{n:,}".replace(",", ".")


def _khoa_ky(ma: str, nam: int, thang: int) -> str:
    """Khóa nhận dạng một (chi nhánh × kỳ) để tick chọn ghi đè từng dòng."""
    return f"{ma}|{thang:02d}/{nam}"


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
        self._ovr_thu_muc: dict[str, str] = {}   # thư mục gán đè (test/phiên tạm) — thắng cấu hình
        self._ovr_quy_doi: dict | None = None    # bảng quy đổi gán đè (test) — thắng cấu hình
        self._cache_quy_doi: dict | None = None  # nhớ map đọc từ kho (xóa khi lưu)

    def _tm(self, khoa: str) -> str:
        d = self._ovr_thu_muc.get(khoa) or cau_hinh.doc_cau_hinh(str(GOC))[khoa]
        # TỰ TẠO khi chưa có — thư mục rỗng (vd "2. Report") hay bị bỏ rơi lúc đóng
        # gói, và người dùng có thể xóa; không có thì mở/ghi sẽ lỗi "Location is not
        # available". Mọi nơi dùng thư mục (kho/nguồn/xuất, mở thư mục, sao lưu) đều
        # đi qua đây nên vá một chỗ là đủ.
        try:
            Path(d).mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        return d

    @property
    def _quy_doi(self) -> dict:
        """Mã chi nhánh -> tên hiển thị. Đọc từ kho SQLite (nhớ tạm trên instance,
        xóa nhớ khi lưu). Kho lỗi/không mở được -> map rỗng: tên chỉ để hiển thị,
        `_ten` về đúng mã gốc, không làm chết luồng."""
        if self._ovr_quy_doi is not None:
            return self._ovr_quy_doi
        if self._cache_quy_doi is None:
            self._cache_quy_doi = self._doc_quy_doi_kho()
        return self._cache_quy_doi

    @_quy_doi.setter
    def _quy_doi(self, m: dict): self._ovr_quy_doi = m

    def _doc_quy_doi_kho(self) -> dict:
        """Đọc bản đồ quy đổi từ kho; di trú 1 lần từ cau-hinh.json (bản cũ) sang kho.
        KHÔNG tạo file kho rỗng chỉ để đọc map rỗng (người chưa từng đặt tên)."""
        cu = cau_hinh.doc_quy_doi(str(GOC))
        if not cu and not Path(self._duong_dan_kho()).exists():
            return {}
        try:
            kho = self._kho()
        except Exception:  # noqa: BLE001 (kho lỗi không được làm chết màn hình)
            return cu
        try:
            m = kho.doc_quy_doi()
            if not m and cu:                 # di trú JSON -> kho, rồi dọn JSON
                kho.ghi_quy_doi(cu)
                cau_hinh.xoa_quy_doi(str(GOC))
                m = cu
            return m
        except Exception:  # noqa: BLE001
            return cu
        finally:
            kho.dong()

    def _ten(self, ma: str) -> str:
        """Tên hiển thị của một mã chi nhánh — về đúng mã khi chưa quy đổi."""
        return self._quy_doi.get(ma, ma)

    @property
    def thu_muc_source(self) -> str: return self._tm("thu_muc_nguon")
    @thu_muc_source.setter
    def thu_muc_source(self, v: str): self._ovr_thu_muc["thu_muc_nguon"] = v

    @property
    def thu_muc_report(self) -> str: return self._tm("thu_muc_xuat")
    @thu_muc_report.setter
    def thu_muc_report(self, v: str): self._ovr_thu_muc["thu_muc_xuat"] = v

    @property
    def _thu_muc_kho(self) -> str: return self._tm("thu_muc_kho")
    @_thu_muc_kho.setter
    def _thu_muc_kho(self, v: str): self._ovr_thu_muc["thu_muc_kho"] = v

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
            "ten": " · ".join(self._ten(d.nhan) for d in self._dv),
            "ky": " · ".join(dict.fromkeys(d.tt.ky for d in self._dv)),
            "so_dong": sum(d.tt.so_dong for d in self._dv),
            "tong_ps": sum(d.tt.tong_ps for d in self._dv),
            "don_vi": [{"ma": d.nhan, "ten_hien": self._ten(d.nhan), "ky": d.tt.ky,
                        "so_dong": d.tt.so_dong,
                        "tong_ps": d.tt.tong_ps, "nguon": d.tt.ten,
                        "ngoai_ky": d.tt.so_dong_ngoai_ky,
                        "ngoai_ky_ct": d.tt.ngoai_ky} for d in self._dv],
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

    def _lo_luy_ke_dau(self, d: "DonVi") -> float | None:
        """Dư đầu 421x (Nợ − Có) từ CĐPS của (chi nhánh × kỳ) — lỗ lũy kế đầu kỳ.
        None = CHƯA nhập CĐPS (không tạo kho thừa chỉ để tra)."""
        if not Path(self._duong_dan_kho()).exists():
            return None
        try:
            kho = self._kho()
        except Exception:  # noqa: BLE001
            return None
        try:
            if not kho.co_cdps(d.nhan, d.tt.ky_nam, d.tt.ky_thang):
                return None
            no, co = kho.du_dau_theo_prefix(d.nhan, d.tt.ky_nam, d.tt.ky_thang, "421")
            return no - co
        finally:
            kho.dong()

    def _cdps_neu_co(self, doc):
        """Đọc một bảng CĐPS từ kho; None nếu chưa nạp.
        Không tạo kho rỗng chỉ để tra (giống _lo_luy_ke_dau)."""
        if not Path(self._duong_dan_kho()).exists():
            return None
        try:
            kho = self._kho()
        except Exception:  # noqa: BLE001 (kho lỗi không được làm chết luồng kiểm tra)
            return None
        try:
            df = doc(kho)
            return df if len(df) else None
        except Exception:  # noqa: BLE001
            return None
        finally:
            kho.dong()

    def _cdps_cua(self, d: "DonVi"):
        """CĐPS của đúng (chi nhánh × kỳ) cho G9/G10/C7; None nếu chưa nạp."""
        return self._cdps_neu_co(lambda kho: kho.doc_cdps(d.nhan, d.tt.ky_nam, d.tt.ky_thang))

    def _cdps_truoc(self, d: "DonVi"):
        """CĐPS của kỳ liền trước — để so biến động hai kỳ; None nếu chưa nạp."""
        return self._cdps_neu_co(lambda kho: kho.doc_cdps_ky_truoc(d.nhan, d.tt.ky_nam, d.tt.ky_thang))

    def _chay_mot_don_vi(self, d: DonVi, on_progress=None) -> None:
        """Chạy toàn bộ check + suy 18 bước cho MỘT chi nhánh, trên frame của riêng nó."""
        ctx = BoiCanh(d.tt.ky_thang, d.tt.ky_nam, lo_luy_ke_dau=self._lo_luy_ke_dau(d),
                      cdps=self._cdps_cua(d), cdps_truoc=self._cdps_truoc(d))
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

    def _thu_muc_dialog(self, path: str) -> str:
        """Thư mục ban đầu AN TOÀN cho hộp thoại chọn file/thư mục.

        Hộp thoại native mở với `directory` KHÔNG tồn tại thì Windows bật dialog
        "Location is not available" — dialog đó nằm trong tiến trình webview, Python
        không bắt được. Nên tự tạo nếu tạo được; tạo không được thì trả "" để OS tự
        chọn thư mục mặc định, TUYỆT ĐỐI không đẩy đường dẫn hỏng vào hộp thoại.
        """
        if not path:
            return ""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return path
        except OSError:
            return ""

    def chon_file(self, nhieu: bool = False):
        if self._window is None:
            return {"loi": "Chưa có cửa sổ"}
        try:
            import webview
            loai = getattr(getattr(webview, "FileDialog", None), "OPEN", None) or webview.OPEN_DIALOG
            chon = self._window.create_file_dialog(loai, directory=self._thu_muc_dialog(self.thu_muc_source),
                                                   allow_multiple=bool(nhieu),
                                                   file_types=("Excel (*.xlsx;*.xls;*.xlsm)",))
            if not chon:
                return None
            return self.nap_nhieu_file(list(chon))
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không mở được hộp thoại chọn file: {e}"}

    def chon_nhieu_file(self):
        return self.chon_file(nhieu=True)

    def chon_file_sqlite(self):
        """Hộp thoại chọn một file .sqlite/.db — dùng cho phục hồi/nhập-gộp kho ở
        tab Lịch sử chốt sổ. Cùng khuôn với chon_file: None khi mở được hộp thoại
        nhưng người dùng bấm Huỷ, {huy: True} khi hộp thoại trả về rỗng."""
        if self._window is None:
            return {"loi": "Chưa có cửa sổ"}
        try:
            import webview
            loai = getattr(getattr(webview, "FileDialog", None), "OPEN", None) or webview.OPEN_DIALOG
            chon = self._window.create_file_dialog(loai, directory=self._thu_muc_dialog(self._thu_muc_kho),
                                                   file_types=("SQLite (*.sqlite;*.db)",))
            return {"path": chon[0]} if chon else {"huy": True}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không mở được hộp thoại: {e}"}

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
            if ds and (self._duong_dan != ds or self._co_don_vi_da_chot()):
                self._nap_nhieu(ds)
                vua_doc_lai = True
            if not self._dv:
                return {"loi": "Chưa chọn file bảng kê"}
            # Nếu vừa đọc lại file, phần đọc đã chiếm 0-85% thanh tiến trình —
            # phần kiểm tra chỉ còn 85-100%. Nếu file đã có sẵn (trường hợp thường
            # gặp khi bấm "Kiểm tra" ngay sau khi màn 1 đã nạp xong), kiểm tra là
            # toàn bộ việc của lần gọi này nên được trọn 0-100%.
            dau = 85 if vua_doc_lai else 0
            n = len(self._dv)
            tong_dong = max(1, sum(d.tt.so_dong for d in self._dv))

            # CHẠY KIỂM TRA TRONG LUỒNG NỀN + ĐẬP NHỊP TỪ LUỒNG JS_API — giống hệt
            # phần đọc file ở _nap_nhieu. Trước đây vòng lặp check chạy thẳng trên
            # luồng js_api và gọi evaluate_js (qua on_progress) ngay giữa lúc pandas
            # đang bận: WebView2 phải marshal evaluate_js về luồng UI, mà luồng UI lại
            # đang chờ chính lệnh js_api này trả về -> TREO CỨNG (CPU 0%, thanh đứng ở
            # 85% "Đã đọc…"). Nay on_progress CHỈ ghi trạng thái vào tt_kt, còn nhịp
            # tiến trình (evaluate_js) do luồng js_api rảnh phát ra mỗi ~0,3s — nên vừa
            # hết treo, vừa hiện được "đã xử lý bao nhiêu / tổng bao nhiêu dòng".
            tt_kt: dict = {"i": 0, "dong_xong": 0}
            ket_kt: dict = {}

            def _lam():
                try:
                    dong_truoc = 0
                    for i, d in enumerate(self._dv):
                        tt_kt["i"] = i
                        base, sodong = dong_truoc, d.tt.so_dong

                        def _op(_ten, pct, base=base, sodong=sodong):
                            tt_kt["dong_xong"] = base + sodong * pct // 100

                        self._chay_mot_don_vi(d, _op)
                        dong_truoc += sodong
                        tt_kt["dong_xong"] = dong_truoc
                except Exception as e:  # noqa: BLE001  (ném lại ở luồng chính)
                    ket_kt["loi"] = e

            luong = threading.Thread(target=_lam, daemon=True)
            self._tien_trinh("Đang kiểm tra…", dau)
            luong.start()
            t0 = time.monotonic()
            while luong.is_alive():
                luong.join(timeout=0.3)
                giay = int(time.monotonic() - t0)
                dong = min(tong_dong, tt_kt["dong_xong"])
                pct = dau + (100 - dau) * dong // tong_dong
                nhan_dv = f"[{self._dv[tt_kt['i']].nhan}] " if n > 1 else ""
                nhan = (f"Đang kiểm tra {nhan_dv}· {_dinh_dang_so(dong)}/"
                        f"{_dinh_dang_so(tong_dong)} dòng · {giay}s")
                self._tien_trinh(nhan, min(99, pct))
            if "loi" in ket_kt:
                raise ket_kt["loi"]
            self._i = min(self._i, n - 1)
            self._tien_trinh("Hoàn tất", 100)
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

    # ---- chốt sổ / kho ----
    def _kho(self) -> KhoChotSo:
        return KhoChotSo(str(Path(self._thu_muc_kho) / "kho_chot_so.sqlite"))

    def _duong_dan_kho(self) -> str:
        return str(Path(self._thu_muc_kho) / "kho_chot_so.sqlite")

    def _doc_thu_muc_cdps(self, thu_muc: str):
        """Đọc mọi file CĐPS hợp lệ trong thư mục -> [(df, meta, tên file)] + danh sách bỏ qua."""
        hop_le, bo_qua = [], []
        for p in tim_file_excel(thu_muc or self.thu_muc_source):
            ten = Path(p).name
            if cdps.suy_branch_ky(p) is None:
                bo_qua.append(ten)
                continue
            try:
                df, m = cdps.doc_cdps(p)
            except cdps.KhongPhaiCdps:
                bo_qua.append(ten)
                continue
            hop_le.append((df, m, ten))
        return hop_le, bo_qua

    def xem_truoc_cdps(self, thu_muc: str = ""):
        """CHỈ ĐỌC: thư mục này sẽ nạp mới những gì, và đè lên kỳ nào đã có.

        Ghi đè là mất số liệu cũ (luu_cdps thay sạch cả kỳ), nên người dùng phải
        thấy trước danh sách kỳ trùng rồi mới quyết — không ghi đè im lặng.
        """
        try:
            hop_le, bo_qua = self._doc_thu_muc_cdps(thu_muc)
            moi, trung = [], []
            kho = self._kho()
            try:
                for df, m, ten in hop_le:
                    mo_ta = {"chi_nhanh": m.ma, "chi_nhanh_ten": self._ten(m.ma),
                             "ky": f"{m.thang:02d}/{m.nam}", "file": ten,
                             "khoa": _khoa_ky(m.ma, m.nam, m.thang)}
                    if kho.doc_cdps(m.ma, m.nam, m.thang).empty:
                        moi.append(mo_ta)
                        continue
                    doi = kho.so_sanh_cdps(m.ma, m.nam, m.thang, df)
                    trung.append({**mo_ta, "khac": doi is not None,
                                  "so_doi": (doi or {}).get("so_doi", 0),
                                  "so_them": (doi or {}).get("so_them", 0),
                                  "so_bot": (doi or {}).get("so_bot", 0),
                                  "dong": (doi or {}).get("dong", [])[:20]})
            finally:
                kho.dong()
            return {"moi": moi, "trung": trung, "bo_qua": bo_qua}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không đọc được CĐPS: {e}"}

    def nap_cdps_thu_muc(self, thu_muc: str = "", ghi_de=False):
        """Nạp CĐPS trong `thu_muc` vào kho. Kỳ CHƯA CÓ luôn nạp; kỳ ĐÃ CÓ chỉ bị đè
        khi được chọn.

        `ghi_de`: False = không đè kỳ nào · True = đè hết · danh sách khóa
        ("MA|MM/YYYY", lấy từ `xem_truoc_cdps`) = chỉ đè đúng những kỳ được tick.
        """
        cho_de = None if ghi_de in (True, False, None) else set(ghi_de)
        try:
            hop_le, bo_qua = self._doc_thu_muc_cdps(thu_muc)
            nap, thay_doi, bo_qua_trung = [], [], []
            kho = self._kho()
            try:
                for df, m, ten in hop_le:
                    mo_ta = {"chi_nhanh": m.ma, "chi_nhanh_ten": self._ten(m.ma),
                             "ky": f"{m.thang:02d}/{m.nam}", "file": ten,
                             "khoa": _khoa_ky(m.ma, m.nam, m.thang)}
                    da_co = not kho.doc_cdps(m.ma, m.nam, m.thang).empty
                    duoc_de = ghi_de is True if cho_de is None else (mo_ta["khoa"] in cho_de)
                    if da_co and not duoc_de:
                        bo_qua_trung.append(mo_ta)
                        continue
                    # Soi TRƯỚC khi ghi đè: nạp lại là thay sạch, không so trước thì
                    # số liệu kế toán đã xem hôm qua đổi lặng lẽ.
                    doi = kho.so_sanh_cdps(m.ma, m.nam, m.thang, df) if da_co else None
                    kho.luu_cdps(m.ma, m.nam, m.thang, df)
                    nap.append(mo_ta)
                    if doi:
                        doi.update(chi_nhanh_ten=mo_ta["chi_nhanh_ten"], ky=mo_ta["ky"])
                        doi["dong"] = doi["dong"][:20]     # đủ để nhìn, không ngập UI
                        thay_doi.append(doi)
            finally:
                kho.dong()
            return {"nap": nap, "bo_qua": bo_qua, "bo_qua_trung": bo_qua_trung,
                    "thay_doi": thay_doi, "trang_thai": self.trang_thai_cdps()}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không nạp được CĐPS: {e}"}

    def thieu_cdps(self):
        """Chi nhánh đang nạp (bảng kê) mà kỳ tương ứng CHƯA có CĐPS trong kho —
        dùng để CHẶN CỨNG nút Kiểm tra (bắt buộc có CĐPS mới được kiểm)."""
        if not self._dv:
            return []
        def _mo():
            return [{"chi_nhanh": d.nhan, "chi_nhanh_ten": self._ten(d.nhan),
                     "ky": f"{d.tt.ky_thang:02d}/{d.tt.ky_nam}"} for d in self._dv]
        if not Path(self._duong_dan_kho()).exists():
            return _mo()                       # chưa có kho -> mọi chi nhánh đều thiếu
        try:
            kho = self._kho()
        except Exception:  # noqa: BLE001
            return _mo()
        try:
            return [{"chi_nhanh": d.nhan, "chi_nhanh_ten": self._ten(d.nhan),
                     "ky": f"{d.tt.ky_thang:02d}/{d.tt.ky_nam}"}
                    for d in self._dv if not kho.co_cdps(d.nhan, d.tt.ky_nam, d.tt.ky_thang)]
        finally:
            kho.dong()

    def chi_tiet_cdps(self, chi_nhanh, ky_nam, ky_thang):
        """Chi tiết các tài khoản của một CĐPS (chi nhánh × kỳ) — cho màn xem CĐPS."""
        if not Path(self._duong_dan_kho()).exists():
            return {"dong": []}
        try:
            kho = self._kho()
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không mở được kho: {e}"}
        try:
            df = kho.doc_cdps(chi_nhanh, int(ky_nam), int(ky_thang))
            return {"dong": df.to_dict("records") if not df.empty else []}
        finally:
            kho.dong()

    def trang_thai_cdps(self):
        """Danh sách (chi nhánh × kỳ) đã nhập CĐPS — cho màn nhập hiện trạng thái."""
        if not Path(self._duong_dan_kho()).exists():
            return []
        try:
            kho = self._kho()
        except Exception:  # noqa: BLE001
            return []
        try:
            return [{"chi_nhanh": r["chi_nhanh"], "chi_nhanh_ten": self._ten(r["chi_nhanh"]),
                     "ky": f'{int(r["ky_thang"]):02d}/{r["ky_nam"]}', "thoi_diem_nap": r["thoi_diem_nap"]}
                    for r in kho.trang_thai_cdps()]
        finally:
            kho.dong()

    def _co_don_vi_da_chot(self) -> bool:
        """True nếu có chi nhánh đang nạp đã được chốt (có snapshot hiệu lực) — dùng
        để buộc đọc lại file: kỳ đã chốt phải đối chiếu với ĐĨA hiện tại, không phải
        df cũ trong bộ nhớ, nếu không người dùng sửa file rồi bấm lại sẽ thấy KHỚP giả."""
        if not self._dv:
            return False
        try:
            kho = self._kho()
        except Exception:  # noqa: BLE001 (kho lỗi không được làm chết luồng kiểm tra)
            return False
        try:
            return any(kho.doc_hieu_luc(d.tt.ky_nam, d.tt.ky_thang, d.nhan) for d in self._dv)
        finally:
            kho.dong()

    def _trang_thai_chot(self, d: "DonVi") -> dict:
        """Trạng thái chốt + đối chiếu cho một chi nhánh. Không có snapshot → CHUA_CHOT (im lặng)."""
        try:
            kho = self._kho()
        except PhienBanMoiHon as e:
            return {"trang_thai": "CHUA_CHOT", "doi_chieu": chot_so.CHUA_CHOT, "loi_kho": str(e)}
        except Exception:  # noqa: BLE001 (kho lỗi khác không được làm chết màn kết quả)
            return {"trang_thai": "CHUA_CHOT", "doi_chieu": chot_so.CHUA_CHOT}
        try:
            h = kho.doc_hieu_luc(d.tt.ky_nam, d.tt.ky_thang, d.nhan)
            if h is None:
                return {"trang_thai": "CHUA_CHOT", "doi_chieu": chot_so.CHUA_CHOT}
            vt = chot_so.VanTay(h["so_dong"], h["tong_ps"], h["van_tay"])
            df_chot = kho.doc_du_lieu(h["id"])
            kq = chot_so.doi_chieu(vt, d.df, df_chot=df_chot)
            return {"trang_thai": "DA_CHOT", "ngay_chot": h["thoi_diem_chot"], "ghi_chu": h["ghi_chu"],
                    "ket_luan_ma": h["ket_luan_ma"], "doi_chieu": kq.trang_thai,
                    "tom_tat_lech": {"delta_dong": kq.delta_dong, "delta_ps": kq.delta_ps,
                                     "so_ct_anh_huong": kq.so_ct_anh_huong}}
        finally:
            kho.dong()

    def _dem_ket_luan(self, kl: dict) -> dict:
        return {k: kl.get(k, 0) for k in ("so_do", "so_vang", "so_chua_lam", "so_can_ra")}

    def chot_so(self, ghi_chu: str = ""):
        d = self._hien
        if d is None or not d.ket_qua:
            return {"loi": "Chưa chạy kiểm tra cho chi nhánh này"}
        try:
            vt = chot_so.van_tay(d.df)
            kl = tinh_ket_luan(d.ket_qua, d.trang_thai)
            checks_ = [{"ma": r.ma, "ten": r.ten, "muc_do": r.muc_do_thuc,
                        "so_loi": r.so_loi, "la_thong_ke": r.la_thong_ke} for r in d.ket_qua]
            kho = self._kho()
            try:
                kho.luu_snapshot(ky_nam=d.tt.ky_nam, ky_thang=d.tt.ky_thang, chi_nhanh=d.nhan,
                                 van_tay_hash=vt.ma_bam, so_dong=vt.so_dong, tong_ps=vt.tong_ps,
                                 ket_luan_ma=kl["muc_do_ket_luan"], dem=self._dem_ket_luan(kl),
                                 checks=checks_, df=d.df, ghi_chu=ghi_chu)
            finally:
                kho.dong()
            return {"chot": self._trang_thai_chot(d)}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không chốt được kỳ: {e}"}

    def mo_lai_ky(self):
        d = self._hien
        if d is None:
            return {"loi": "Chưa có chi nhánh đang xem"}
        try:
            kho = self._kho()
            try:
                kho.mo_lai(d.tt.ky_nam, d.tt.ky_thang, d.nhan)
            finally:
                kho.dong()
            return {"chot": self._trang_thai_chot(d)}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không mở lại được kỳ: {e}"}

    def lich_su_chot(self, chi_nhanh=None):
        try:
            kho = self._kho()
            try:
                dong = kho.liet_ke(chi_nhanh=chi_nhanh)
            finally:
                kho.dong()
            # Gắn tên hiển thị theo bảng quy đổi hiện tại (mã lưu trong kho vẫn giữ nguyên).
            for r in dong:
                r["chi_nhanh_ten"] = self._ten(r.get("chi_nhanh", ""))
            return {"dong": dong}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không đọc được lịch sử chốt: {e}"}

    def lay_diff_chot(self, trang: int = 1, kich_thuoc: int = 100, tim_kiem: str = ""):
        d = self._hien
        if d is None or not d.ket_qua:
            return {"loi": "Chưa chạy kiểm tra"}
        try:
            kho = self._kho()
            try:
                h = kho.doc_hieu_luc(d.tt.ky_nam, d.tt.ky_thang, d.nhan)
                if h is None:
                    return {"loi": "Kỳ này chưa chốt"}
                df_chot = kho.doc_du_lieu(h["id"])
            finally:
                kho.dong()
            diff = chot_so.dien_diff(df_chot, d.df)
            them = _dinh_dang_ngay(diff["them"]).assign(**{"Thay đổi": "＋ Thêm"})
            bot = _dinh_dang_ngay(diff["bot"]).assign(**{"Thay đổi": "－ Bớt"})
            df = pd.concat([them, bot], ignore_index=True) if len(them) or len(bot) else them
            if tim_kiem:
                tk = tim_kiem.lower()
                df = df[df.astype(str).apply(lambda s: s.str.lower().str.contains(tk, regex=False)).any(axis=1)]
            tong = int(len(df)); kich_thuoc = max(1, min(int(kich_thuoc), 500))
            a = max(0, (int(trang) - 1) * kich_thuoc); cot = list(df.columns)
            return {"tong": tong, "trang": int(trang), "cot": cot, "nhan": ten_cot(cot),
                    "cot_so": cot_so_cua(df),
                    "cot_so_le": [c for c in cot if c in COT_SO_LE],
                    "tom_tat": diff["tom_tat"],
                    "dong": json.loads(df.iloc[a:a + kich_thuoc].to_json(orient="records", force_ascii=False))}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không lấy được thay đổi: {e}"}

    def sao_luu_kho(self):
        try:
            p = kho_sao_luu.sao_luu(self._duong_dan_kho(), str(Path(self._thu_muc_kho) / "backup"))
            return {"path": p}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không sao lưu được kho: {e}"}

    def tom_tat_kho(self, path: str):
        """Xem trước nội dung một file kho trước khi phục hồi/nhập-gộp (chỉ đọc)."""
        try:
            return kho_sao_luu.tom_tat_kho(path)
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không đọc được file kho: {e}"}

    def phuc_hoi_kho(self, path: str):
        try:
            bk = kho_sao_luu.phuc_hoi(self._duong_dan_kho(), path, str(Path(self._thu_muc_kho) / "backup"))
            return {"da_sao_luu": bk}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không phục hồi được kho: {e}"}

    def nhap_gop_kho(self, path: str):
        try:
            return kho_sao_luu.nhap_gop(self._duong_dan_kho(), path)
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không nhập/gộp được kho: {e}"}

    def mo_thu_muc_kho(self):
        return self.mo_thu_muc(self._thu_muc_kho)

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
                       "chi_nhanh": self._hien.nhan, "chi_nhanh_ten": self._ten(self._hien.nhan),
                       **ket_luan,
                       "chan_doan": chan_doan.chan_doan(self._ket_qua),
                       "chot": self._trang_thai_chot(self._hien)},
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
            ds.append({"i": i, "ma": d.nhan, "ten_hien": self._ten(d.nhan), "ky": d.tt.ky,
                       "so_dong": d.tt.so_dong,
                       "tong_ps": d.tt.tong_ps, "nguon": d.tt.ten, "da_chay": bool(d.ket_qua),
                       **kl, "chot": self._trang_thai_chot(d) if d.ket_qua else {"trang_thai": "CHUA_CHOT"}})
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
                "cot_so": cot_so_cua(df),
                "cot_so_le": [c for c in cot if c in COT_SO_LE],
                "dong": json.loads(df.iloc[a:a + kich_thuoc].to_json(orient="records", force_ascii=False))}

    # ---- xuất & mở ----
    def xuat_bao_cao(self):
        if not self._ket_qua:
            return {"loi": "Chưa chạy kiểm tra"}
        try:
            p = report.xuat_bao_cao(self._ket_qua, self._trang_thai, self._tt, self.thu_muc_report,
                                    ten_hien=self._ten(self._hien.nhan))
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
                [(d.nhan, self._ten(d.nhan), d.ket_qua, d.trang_thai, d.tt) for d in self._dv],
                self.thu_muc_report)
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

    # ---- cài đặt thư mục ----
    def lay_cau_hinh(self) -> dict:
        """Giá trị thô (để hiện trong ô nhập) + đường dẫn đã giải (để hiển thị) +
        bảng quy đổi hiện có và danh sách mã chi nhánh gợi ý (lấy từ file đang nạp,
        để màn Cài đặt điền sẵn hàng, người dùng chỉ việc gõ tên)."""
        tho = cau_hinh._doc_tho(str(GOC))
        giai = cau_hinh.doc_cau_hinh(str(GOC))
        quy_doi = self._quy_doi                 # đọc từ kho (đã di trú nếu cần)
        goi_y = list(dict.fromkeys([d.nhan for d in self._dv] + list(quy_doi)))
        return {"tho": {k: str(tho.get(k, cau_hinh.MAC_DINH[k])) for k in cau_hinh.KHOA},
                "giai": giai, "quy_doi": quy_doi, "ma_goi_y": goi_y}

    def luu_cau_hinh(self, cfg: dict):
        try:
            c = cfg or {}
            payload: dict = {}
            for k in cau_hinh.KHOA:
                if k in c:
                    payload[k] = str(c.get(k, "")).strip() or cau_hinh.MAC_DINH[k]
            if payload:
                cau_hinh.ghi_cau_hinh(str(GOC), payload)   # thư mục vẫn ở JSON
            if cau_hinh.KHOA_MAP in c:
                m = cau_hinh._lam_sach_map(c.get(cau_hinh.KHOA_MAP))
                kho = self._kho()
                try:
                    kho.ghi_quy_doi(m)                     # bản đồ quy đổi ở kho SQLite
                finally:
                    kho.dong()
                self._cache_quy_doi = None                 # buộc đọc lại lần sau
            return {"ok": True}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không lưu được cấu hình: {e}"}

    def chon_thu_muc(self, directory: str = ""):
        if self._window is None:
            return {"loi": "Chưa có cửa sổ"}
        try:
            import webview
            bat_dau = ""
            if directory:
                p = Path(directory)
                bat_dau = str(p if p.is_absolute() else (GOC / directory))  # mở đúng thư mục hiện tại
            loai = getattr(getattr(webview, "FileDialog", None), "FOLDER", None) or webview.FOLDER_DIALOG
            chon = self._window.create_file_dialog(loai, directory=self._thu_muc_dialog(bat_dau))
            return {"path": chon[0]} if chon else {"huy": True}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không mở được hộp thoại thư mục: {e}"}
