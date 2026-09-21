# Nút "Kiểm tra cập nhật" — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thêm nút trong app để người dùng kiểm tra và tự cài bản mới, tải từ GitHub Releases công khai.

**Architecture:** Module Python thuần stdlib (`app/cap_nhat.py`) lo việc hỏi phiên bản / tải bộ cài; hai method mới trên `JsApi` (pywebview) làm cầu; UI React thêm nút + badge + Modal. Bộ cài thôi nhúng CĐPS thật để release được phép công khai.

**Tech Stack:** Python 3 stdlib (`urllib.request`, `json`, `os`, `tempfile`), pywebview, React + Vite, Inno Setup, `gh` CLI.

**Spec:** [docs/spec/2026-09-21-cap-nhat-trong-app-design.md](../spec/2026-09-21-cap-nhat-trong-app-design.md)

## Global Constraints

- **Không thêm phụ thuộc mới** cho phần cập nhật — chỉ stdlib.
- **Một nguồn VERSION**: phiên bản đang chạy lấy từ `__PHIEN_BAN__` (UI truyền vào), không đọc/bundle riêng.
- **Cập nhật không bao giờ được làm app treo/chết**: mọi lỗi mạng/HTTP/IO nuốt thành `{"loi": "..."}`.
- **Test không chạm mạng thật, không chạm kho/temp thật**: monkeypatch `urlopen`, ép thư mục ra `tmp_path`.
- **Mù màu**: trạng thái phân biệt bằng chữ + ký hiệu (dùng `KY_HIEU`/`Dau` sẵn có), không chỉ bằng màu.
- **Không phát hành dữ liệu tài chính thật**: bộ cài không nhúng CĐPS; tên chi nhánh ra file local gitignore.
- Tên method Python: snake_case, trả `dict`. Nếp lỗi: `return {"loi": str(e)}`.

---

### Task 1: So sánh phiên bản (`_bo`, `moi_hon`)

**Files:**
- Create: `app/cap_nhat.py`
- Test: `tests/test_cap_nhat.py`

**Interfaces:**
- Produces: `moi_hon(latest: str, hien_tai: str) -> bool`; `_bo(v: str) -> tuple[int, ...]`

- [ ] **Step 1: Viết test thất bại**

```python
# tests/test_cap_nhat.py
from app import cap_nhat as cn


def test_moi_hon_theo_tung_so():
    assert cn.moi_hon("1.1.4", "1.1.3") is True
    assert cn.moi_hon("1.2.0", "1.1.9") is True
    assert cn.moi_hon("1.1.3", "1.1.3") is False
    assert cn.moi_hon("1.1.2", "1.1.3") is False


def test_moi_hon_bo_tien_to_v_va_do_dai_lech():
    assert cn.moi_hon("v1.2.0", "1.1.5") is True      # có 'v'
    assert cn.moi_hon("1.2", "1.1.9") is True          # thiếu số cuối -> (1,2) > (1,1,9)
    assert cn.moi_hon("1.2.0", "1.2") is False         # (1,2,0) == (1,2,0)
```

- [ ] **Step 2: Chạy test cho thất bại**

Run: `python -m pytest tests/test_cap_nhat.py -q`
Expected: FAIL (`ModuleNotFoundError` hoặc `AttributeError: moi_hon`)

- [ ] **Step 3: Viết cài đặt tối thiểu**

```python
# app/cap_nhat.py
"""Kiểm tra & tải bản cập nhật từ GitHub Releases công khai. Chỉ stdlib.

Không auth (repo phát hành công khai). Mọi lỗi mạng/HTTP/IO được nuốt thành
{"loi": ...} — cập nhật là tính năng phụ, không bao giờ làm app chết.
"""
from __future__ import annotations


def _bo(v: str) -> tuple[int, ...]:
    """"v1.2.3" -> (1,2,3). Phần không phải số -> 0. So sánh tuple là đủ semver ở đây."""
    v = v.strip().lstrip("vV")
    ra = []
    for phan in v.split("."):
        try:
            ra.append(int(phan))
        except ValueError:
            ra.append(0)
    return tuple(ra)


def moi_hon(latest: str, hien_tai: str) -> bool:
    """latest > hien_tai theo từng số. Độ dài lệch: đệm 0 để so công bằng."""
    a, b = _bo(latest), _bo(hien_tai)
    n = max(len(a), len(b))
    a += (0,) * (n - len(a))
    b += (0,) * (n - len(b))
    return a > b
```

- [ ] **Step 4: Chạy test cho đạt**

Run: `python -m pytest tests/test_cap_nhat.py -q`
Expected: PASS (2 test)

- [ ] **Step 5: Commit**

```bash
git add app/cap_nhat.py tests/test_cap_nhat.py
git commit -m "feat(cap-nhat): so sanh phien ban semver (moi_hon)"
```

---

### Task 2: Hỏi bản mới nhất từ GitHub (`lay_ban_moi_nhat`)

**Files:**
- Modify: `app/cap_nhat.py`
- Test: `tests/test_cap_nhat.py`

**Interfaces:**
- Consumes: `_bo` (không trực tiếp)
- Produces: `lay_ban_moi_nhat(timeout: int = 6) -> dict` → `{"phien_ban","url_tai","mo_ta"}` hoặc `{"loi": "..."}`. Hằng module `KHO_PHAT_HANH`, `TEN_ASSET`, `API_LATEST`.

- [ ] **Step 1: Viết test thất bại**

```python
# them vao tests/test_cap_nhat.py
import json
import urllib.error


_JSON_MAU = json.dumps({
    "tag_name": "v1.2.0",
    "body": "Sửa C4.6, thêm nút cập nhật",
    "assets": [
        {"name": "note.txt", "browser_download_url": "https://x/note.txt"},
        {"name": "KiemTraKhoaSo-Setup-1.2.0.exe",
         "browser_download_url": "https://x/KiemTraKhoaSo-Setup-1.2.0.exe"},
    ],
}).encode("utf-8")


class _GiaResp:
    def __init__(self, data): self._d = data
    def read(self): return self._d
    def __enter__(self): return self
    def __exit__(self, *a): return False


def test_lay_ban_moi_nhat_parse_dung(monkeypatch):
    monkeypatch.setattr(cn.urllib.request, "urlopen", lambda *a, **k: _GiaResp(_JSON_MAU))
    r = cn.lay_ban_moi_nhat()
    assert r["phien_ban"] == "1.2.0"                       # đã bỏ 'v'
    assert r["url_tai"].endswith("KiemTraKhoaSo-Setup-1.2.0.exe")
    assert "C4.6" in r["mo_ta"]


def test_lay_ban_moi_nhat_loi_mang_thi_tra_loi(monkeypatch):
    def _no(*a, **k): raise urllib.error.URLError("khong co mang")
    monkeypatch.setattr(cn.urllib.request, "urlopen", _no)
    r = cn.lay_ban_moi_nhat()
    assert "loi" in r and "phien_ban" not in r


def test_lay_ban_moi_nhat_404_coi_nhu_da_moi_nhat(monkeypatch):
    def _404(*a, **k):
        raise urllib.error.HTTPError("u", 404, "Not Found", {}, None)
    monkeypatch.setattr(cn.urllib.request, "urlopen", _404)
    r = cn.lay_ban_moi_nhat()
    assert r.get("khong_co_release") is True and "loi" not in r


def test_lay_ban_moi_nhat_thieu_asset_exe(monkeypatch):
    data = json.dumps({"tag_name": "v1.2.0", "body": "", "assets": []}).encode()
    monkeypatch.setattr(cn.urllib.request, "urlopen", lambda *a, **k: _GiaResp(data))
    r = cn.lay_ban_moi_nhat()
    assert "loi" in r
```

- [ ] **Step 2: Chạy test cho thất bại**

Run: `python -m pytest tests/test_cap_nhat.py -q`
Expected: FAIL (`AttributeError: lay_ban_moi_nhat`)

- [ ] **Step 3: Viết cài đặt tối thiểu**

```python
# them dau app/cap_nhat.py (sau docstring)
import json
import urllib.error
import urllib.request

# Slug repo GitHub công khai chứa release. ĐIỀN khi tạo repo (tham số triển khai duy nhất).
KHO_PHAT_HANH = "owner/ten-repo"
TEN_ASSET = "KiemTraKhoaSo-Setup"        # tiền tố tên file cài để nhận đúng asset
API_LATEST = f"https://api.github.com/repos/{KHO_PHAT_HANH}/releases/latest"


def lay_ban_moi_nhat(timeout: int = 6) -> dict:
    """Hỏi release mới nhất. Trả {"phien_ban","url_tai","mo_ta"}; hoặc
    {"khong_co_release": True} khi 404; hoặc {"loi": ...} cho mọi trục trặc khác."""
    try:
        req = urllib.request.Request(API_LATEST, headers={"Accept": "application/vnd.github+json",
                                                          "User-Agent": "KiemTraKhoaSo"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"khong_co_release": True}
        return {"loi": f"Máy chủ trả lỗi {e.code}"}
    except Exception:
        return {"loi": "Không kết nối được để kiểm tra cập nhật"}

    tag = str(data.get("tag_name", "")).lstrip("vV")
    url = ""
    for a in data.get("assets", []):
        ten = str(a.get("name", ""))
        if ten.startswith(TEN_ASSET) and ten.lower().endswith(".exe"):
            url = a.get("browser_download_url", "")
            break
    if not tag or not url:
        return {"loi": "Bản phát hành thiếu file cài"}
    return {"phien_ban": tag, "url_tai": url, "mo_ta": str(data.get("body", "") or "")}
```

- [ ] **Step 4: Chạy test cho đạt**

Run: `python -m pytest tests/test_cap_nhat.py -q`
Expected: PASS (6 test)

- [ ] **Step 5: Commit**

```bash
git add app/cap_nhat.py tests/test_cap_nhat.py
git commit -m "feat(cap-nhat): hoi release moi nhat tu GitHub (public, khong token)"
```

---

### Task 3: Tải bộ cài về (`tai_bo_cai`)

**Files:**
- Modify: `app/cap_nhat.py`
- Test: `tests/test_cap_nhat.py`

**Interfaces:**
- Produces: `tai_bo_cai(url: str, thu_muc: str | None = None) -> str` → đường dẫn file .exe đã tải. `thu_muc=None` → `%TEMP%`. Ném ngoại lệ nếu lỗi (người gọi ở api.py bắt).

- [ ] **Step 1: Viết test thất bại**

```python
# them vao tests/test_cap_nhat.py
def test_tai_bo_cai_ghi_part_roi_doi_ten(monkeypatch, tmp_path):
    def _fake_urlretrieve(url, dich):
        assert dich.endswith(".part")                 # tải vào .part trước
        with open(dich, "wb") as f:
            f.write(b"noi-dung-bo-cai")
    monkeypatch.setattr(cn.urllib.request, "urlretrieve", _fake_urlretrieve)
    p = cn.tai_bo_cai("https://x/KiemTraKhoaSo-Setup-1.2.0.exe", str(tmp_path))
    assert p.endswith("KiemTraKhoaSo-Setup-1.2.0.exe")
    assert open(p, "rb").read() == b"noi-dung-bo-cai"
    assert not any(str(f).endswith(".part") for f in tmp_path.iterdir())   # không còn file dở


def test_tai_bo_cai_dut_giua_chung_khong_de_lai_file_dich(monkeypatch, tmp_path):
    def _no(url, dich):
        with open(dich, "wb") as f:
            f.write(b"mot-phan")
        raise OSError("dut mang")
    monkeypatch.setattr(cn.urllib.request, "urlretrieve", _no)
    try:
        cn.tai_bo_cai("https://x/KiemTraKhoaSo-Setup-1.2.0.exe", str(tmp_path))
        assert False, "phai nem loi"
    except OSError:
        pass
    assert list(tmp_path.iterdir()) == []              # dọn sạch .part, không có file đích
```

- [ ] **Step 2: Chạy test cho thất bại**

Run: `python -m pytest tests/test_cap_nhat.py -q`
Expected: FAIL (`AttributeError: tai_bo_cai`)

- [ ] **Step 3: Viết cài đặt tối thiểu**

```python
# them vao app/cap_nhat.py
import os
import tempfile


def tai_bo_cai(url: str, thu_muc: str | None = None) -> str:
    """Tải bộ cài về `thu_muc` (mặc định %TEMP%). Ghi ra .part rồi đổi tên để
    không để lại file dở nếu đứt mạng. Trả đường dẫn .exe. Ném lỗi khi thất bại."""
    thu_muc = thu_muc or tempfile.gettempdir()
    ten = url.rsplit("/", 1)[-1] or "KiemTraKhoaSo-Setup.exe"
    dich = os.path.join(thu_muc, ten)
    tam = dich + ".part"
    try:
        urllib.request.urlretrieve(url, tam)
        os.replace(tam, dich)
        return dich
    except Exception:
        for p in (tam, dich):
            try:
                os.remove(p)
            except OSError:
                pass
        raise
```

- [ ] **Step 4: Chạy test cho đạt**

Run: `python -m pytest tests/test_cap_nhat.py -q`
Expected: PASS (8 test)

- [ ] **Step 5: Commit**

```bash
git add app/cap_nhat.py tests/test_cap_nhat.py
git commit -m "feat(cap-nhat): tai bo cai ve %TEMP% (an toan dut mang)"
```

---

### Task 4: Cầu JsApi (`kiem_tra_cap_nhat`, `tai_va_cai`)

**Files:**
- Modify: `app/api.py` (thêm 2 method vào lớp `JsApi`; thêm `from . import cap_nhat` và `import os` nếu chưa có)
- Test: `tests/test_api_cap_nhat.py`

**Interfaces:**
- Consumes: `cap_nhat.lay_ban_moi_nhat`, `cap_nhat.tai_bo_cai`, `cap_nhat.moi_hon`, `self._window`
- Produces (method của `JsApi`):
  - `kiem_tra_cap_nhat(self, pb_hien_tai: str) -> dict` → `{"co_moi","phien_ban","url_tai","mo_ta"}` / `{"khong_co_release": True}` / `{"loi": ...}`
  - `tai_va_cai(self, url: str) -> dict` → chỉ trả `{"loi": ...}` khi lỗi (thành công thì đóng app, không trả)

- [ ] **Step 1: Viết test thất bại**

```python
# tests/test_api_cap_nhat.py
from app.api import JsApi
from app import cap_nhat


def test_kiem_tra_danh_dau_co_moi(monkeypatch):
    monkeypatch.setattr(cap_nhat, "lay_ban_moi_nhat",
                        lambda *a, **k: {"phien_ban": "1.2.0", "url_tai": "u", "mo_ta": "m"})
    r = JsApi().kiem_tra_cap_nhat("1.1.3")
    assert r["co_moi"] is True and r["phien_ban"] == "1.2.0"


def test_kiem_tra_khi_dang_moi_nhat(monkeypatch):
    monkeypatch.setattr(cap_nhat, "lay_ban_moi_nhat",
                        lambda *a, **k: {"phien_ban": "1.1.3", "url_tai": "u", "mo_ta": ""})
    assert JsApi().kiem_tra_cap_nhat("1.1.3")["co_moi"] is False


def test_kiem_tra_chuyen_tiep_loi(monkeypatch):
    monkeypatch.setattr(cap_nhat, "lay_ban_moi_nhat", lambda *a, **k: {"loi": "x"})
    assert JsApi().kiem_tra_cap_nhat("1.1.3") == {"loi": "x"}


def test_tai_va_cai_loi_thi_khong_dong_app(monkeypatch):
    def _no(url): raise OSError("dut")
    monkeypatch.setattr(cap_nhat, "tai_bo_cai", _no)
    api = JsApi()
    dong = []
    api._window = type("W", (), {"destroy": lambda self: dong.append(1)})()
    r = api.tai_va_cai("u")
    assert "loi" in r and dong == []            # tuyệt đối không đóng app khi lỗi
```

- [ ] **Step 2: Chạy test cho thất bại**

Run: `python -m pytest tests/test_api_cap_nhat.py -q`
Expected: FAIL (`AttributeError: kiem_tra_cap_nhat`)

- [ ] **Step 3: Viết cài đặt tối thiểu**

Thêm `from . import cap_nhat` vào phần import đầu `app/api.py` (và `import os` nếu file chưa có). Thêm 2 method vào lớp `JsApi`:

```python
    def kiem_tra_cap_nhat(self, pb_hien_tai: str) -> dict:
        r = cap_nhat.lay_ban_moi_nhat()
        if "loi" in r or r.get("khong_co_release"):
            return r
        r["co_moi"] = cap_nhat.moi_hon(r["phien_ban"], pb_hien_tai)
        return r

    def tai_va_cai(self, url: str) -> dict:
        try:
            duong = cap_nhat.tai_bo_cai(url)
        except Exception as e:
            return {"loi": f"Không tải được bản cài: {e}"}
        try:
            os.startfile(duong)                       # chạy Inno; noqa: chỉ có trên Windows
        except Exception as e:
            return {"loi": f"Không mở được bản cài: {e}"}
        if self._window is not None:
            self._window.destroy()                    # thoát để bộ cài đè file
        return {}
```

- [ ] **Step 4: Chạy test cho đạt**

Run: `python -m pytest tests/test_api_cap_nhat.py -q`
Expected: PASS (4 test)

- [ ] **Step 5: Commit**

```bash
git add app/api.py tests/test_api_cap_nhat.py
git commit -m "feat(api): cau JsApi kiem_tra_cap_nhat + tai_va_cai"
```

---

### Task 5: Nút + badge + Modal trong UI

**Files:**
- Modify: `ui/src/api.ts` (thêm 2 method vào interface `PyApi`)
- Modify: `ui/src/App.tsx` (nút trong banner + badge + Modal cập nhật)
- Modify: `app/webapp/*` (bản build commit lại)

**Interfaces:**
- Consumes: `goi("kiem_tra_cap_nhat", __PHIEN_BAN__)`, `goi("tai_va_cai", url)`, `Modal`, `Nut`, `useToast` (từ `ui/src/ui.tsx`), `laLoi` (từ `ui/src/api.ts`)

- [ ] **Step 1: Khai báo kiểu trong `ui/src/api.ts`**

Thêm vào interface `PyApi` (sau `mo_thu_muc_kho`):

```typescript
  kiem_tra_cap_nhat(pb_hien_tai: string): Promise<
    { co_moi: boolean; phien_ban: string; url_tai: string; mo_ta: string }
    | { khong_co_release: true } | Loi>;
  tai_va_cai(url: string): Promise<Record<string, never> | Loi>;
```

- [ ] **Step 2: Thêm state + kiểm tra nền + nút trong `ui/src/App.tsx`**

Trong component App, thêm state và effect kiểm tra nền (best-effort, im lặng khi lỗi):

```tsx
  const [banMoi, setBanMoi] = useState<{ phien_ban: string; url_tai: string; mo_ta: string } | null>(null);
  const [moModal, setMoModal] = useState(false);
  const [dangTai, setDangTai] = useState(false);
  const toast = useToast();

  const kiemTra = useCallback(async (imLang: boolean) => {
    const r = await A.goi("kiem_tra_cap_nhat", __PHIEN_BAN__);
    if (laLoi(r)) { if (!imLang) toast(r.loi); return; }
    if ("khong_co_release" in r || !r.co_moi) {
      if (!imLang) toast("Đang dùng bản mới nhất");
      setBanMoi(null); return;
    }
    setBanMoi({ phien_ban: r.phien_ban, url_tai: r.url_tai, mo_ta: r.mo_ta });
    if (!imLang) setMoModal(true);
  }, [toast]);

  useEffect(() => { void kiemTra(true); }, [kiemTra]);   // kiểm tra nền 1 lần lúc mở
```

Nút trong banner (đặt cạnh khu chip thống kê; badge "●" khi `banMoi`):

```tsx
  <button type="button" className="..." onClick={() => (banMoi ? setMoModal(true) : kiemTra(false))}>
    Kiểm tra cập nhật{banMoi ? " ●" : ""}
  </button>
```

- [ ] **Step 3: Thêm Modal cập nhật trong `ui/src/App.tsx`**

```tsx
  <Modal mo={moModal} dong={() => setMoModal(false)} tieuDe="Có bản cập nhật">
    {banMoi && <>
      <p className="text-sm">Có bản <b>{banMoi.phien_ban}</b> (đang dùng {__PHIEN_BAN__}).</p>
      {banMoi.mo_ta && <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap text-xs">{banMoi.mo_ta}</pre>}
      <div className="mt-4 flex justify-end gap-2">
        <Nut onClick={() => setMoModal(false)}>Để sau</Nut>
        <Nut bien="chinh" disabled={dangTai} onClick={async () => {
          setDangTai(true);
          const r = await A.goi("tai_va_cai", banMoi.url_tai);
          if (laLoi(r)) { setDangTai(false); toast(r.loi); }
          // thành công: app tự thoát, không cần xử lý thêm
        }}>{dangTai ? "Đang tải…" : "Cài ngay"}</Nut>
      </div>
    </>}
  </Modal>
```

Ghi chú: kiểm tên prop nút chính thật trong `ui.tsx` (`Nut` dùng `bien="phu"|"chinh"|...`); dùng đúng biến thể nhấn mạnh sẵn có. Bổ sung `useCallback`, `useEffect`, `useState` vào import React nếu thiếu.

- [ ] **Step 4: Build lại UI + kiểm tra biên dịch**

Run: `cd ui && npm run build`
Expected: build thành công, ghi ra `app/webapp/` (không lỗi TypeScript).

- [ ] **Step 5: Smoke thủ công (nếu chạy được app)**

Run: `python -m app.main`
Expected: banner có nút "Kiểm tra cập nhật"; bấm khi chưa cấu hình repo thật → toast "Không kết nối được…", app KHÔNG treo.

- [ ] **Step 6: Commit**

```bash
git add ui/src/api.ts ui/src/App.tsx app/webapp
git commit -m "feat(ui): nut kiem tra cap nhat + modal cai dat ban moi"
```

---

### Task 6: Bộ cài sạch dữ liệu (bỏ CĐPS, tên chi nhánh ra file local)

**Files:**
- Modify: `tools/tao_seed.py`
- Create: `chi_nhanh.json` (local, gitignore — dữ liệu tên chi nhánh thật)
- Modify: `.gitignore`
- Modify: `tools/DONG_GOI.md` (quy trình phát hành)
- Test: `tests/test_tao_seed.py`

**Interfaces:**
- `tao_seed.dung(seed: Path)` giữ nguyên chữ ký; đọc `QUY_DOI` từ `chi_nhanh.json`; KHÔNG còn nạp/copy CĐPS.

- [ ] **Step 1: Tạo file tên chi nhánh local + gitignore**

Tạo `chi_nhanh.json` ở gốc repo:

```json
{
  "A01": "Hà Nội", "A02": "Vĩnh Phúc", "A03": "Bắc Giang", "A04": "Hồ Chí Minh",
  "A05": "Long An", "A06": "An Giang", "A07": "Đắc Lắc", "A08": "Nhựa Long An"
}
```

Thêm dòng vào `.gitignore`:

```
chi_nhanh.json
```

- [ ] **Step 2: Viết test thất bại**

```python
# tests/test_tao_seed.py
import json
from pathlib import Path

from tools import tao_seed
from app.kho import KhoChotSo


def test_seed_khong_nhung_cdps(monkeypatch, tmp_path):
    # ép nguồn tên chi nhánh vào tmp, không đọc file thật
    cn = tmp_path / "chi_nhanh.json"
    cn.write_text(json.dumps({"A01": "Hà Nội"}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(tao_seed, "FILE_CHI_NHANH", cn)

    seed = tmp_path / "_seed"
    tao_seed.dung(seed)

    # kho có bảng quy đổi tên nhưng KHÔNG có CĐPS nào
    kho = KhoChotSo(str(seed / "3. Chốt sổ" / "kho_chot_so.sqlite"))
    try:
        assert kho.doc_quy_doi().get("A01") == "Hà Nội"
        assert kho.so_ky_cdps() == 0            # <-- không nhúng CĐPS
    finally:
        kho.dong()
    # không copy file CĐPS gốc vào seed
    assert not list((seed / "1. Source").rglob("*.xlsx"))
```

> Ghi chú người thực thi: mở `app/kho/__init__.py`/`KhoChotSo` để lấy đúng tên hàm đọc quy đổi và đếm CĐPS (ví dụ `doc_quy_doi`, và một cách đếm số CĐPS). Nếu tên khác, sửa test cho khớp API thật rồi mới sang Step 3. Đường dẫn `3. Chốt sổ`/`1. Source` lấy từ `app.cau_hinh.MAC_DINH`.

- [ ] **Step 3: Chạy test cho thất bại**

Run: `python -m pytest tests/test_tao_seed.py -q`
Expected: FAIL (`AttributeError: FILE_CHI_NHANH` hoặc kho vẫn có CĐPS)

- [ ] **Step 4: Sửa `tools/tao_seed.py`**

Thay khối `QUY_DOI = {...}` cứng bằng đọc file local, và **xoá** vòng nạp CĐPS + khối copy CĐPS gốc:

```python
FILE_CHI_NHANH = GOC / "chi_nhanh.json"


def _quy_doi() -> dict:
    """Tên chi nhánh đọc từ file local (gitignore) — không nhúng vào mã public."""
    return json.loads(FILE_CHI_NHANH.read_text(encoding="utf-8"))
```

Trong `dung(...)`: thay `kho.ghi_quy_doi(QUY_DOI)` bằng `kho.ghi_quy_doi(_quy_doi())`; **xoá** đoạn `for p in sorted(THU_MUC_CDPS.glob(...)): ... kho.luu_cdps(...)` và **xoá** đoạn "Kèm CĐPS gốc" (copy `*.xlsx`). Đổi dòng in cuối:

```python
    print(f"Seed xong: {seed}  ({len(_quy_doi())} chi nhánh, không kèm CĐPS)")
```

Cập nhật docstring đầu file: bỏ câu "toàn bộ CĐPS đã nạp"; nêu rõ lần đầu người dùng tự nạp CĐPS.

- [ ] **Step 5: Chạy test cho đạt + toàn bộ suite**

Run: `python -m pytest tests/test_tao_seed.py -q && python -m pytest -q`
Expected: PASS toàn bộ.

- [ ] **Step 6: Ghi quy trình phát hành vào `tools/DONG_GOI.md`**

Thêm mục:

```markdown
## Phát hành bản mới (auto-update)
1. Sửa số trong file `VERSION` (vd 1.2.0).
2. Đảm bảo `chi_nhanh.json` có ở gốc (local, không commit).
3. Build: `python -m tools.tao_seed && pyinstaller tools/app.spec --noconfirm --clean` rồi chạy ISCC (như trên).
4. Phát hành: `gh release create v1.2.0 build/Output/KiemTraKhoaSo-Setup-1.2.0.exe --title 1.2.0 --notes "..."`.
   (Lần đầu: đặt `KHO_PHAT_HANH` trong `app/cap_nhat.py` = slug repo public.)
```

- [ ] **Step 7: Commit**

```bash
git add tools/tao_seed.py tools/DONG_GOI.md .gitignore tests/test_tao_seed.py
git commit -m "build: bo cai thoi nhung CDPS that; ten chi nhanh ra file local"
```

---

## Self-Review

**Spec coverage:**
- §2 bỏ CĐPS + tên chi nhánh ra local → Task 6. ✓
- §3 luồng (startup best-effort, nút, modal Cài/Để sau, tải+thoát) → Task 5 + Task 4. ✓
- §4.1 `cap_nhat.py` → Task 1–3. ✓ · §4.2 JsApi → Task 4. ✓ · §4.3 UI → Task 5. ✓ · §4.4 đóng gói → Task 6. ✓
- §5 bảng lỗi → nuốt lỗi ở Task 2 (mạng/404/thiếu asset), Task 3 (đứt mạng), Task 4 (tải/startfile lỗi không đóng app). ✓
- §6 kiểm thử → test ở Task 1–4, 6; UI không có test-runner nên build+smoke (Task 5). ✓
- §7 ngoài phạm vi → không có task nào làm silent-install/delta. ✓

**Placeholder scan:** `KHO_PHAT_HANH="owner/ten-repo"` là tham số triển khai (điền khi tạo repo), đã nêu rõ ở Global Constraints/§2 — không phải TODO logic. Không còn "TBD/xử lý phù hợp".

**Type consistency:** `lay_ban_moi_nhat`→dict `{phien_ban,url_tai,mo_ta}`/`{khong_co_release}`/`{loi}` khớp giữa Task 2, Task 4, và interface TS Task 5. `moi_hon(latest, hien_tai)` dùng nhất quán. `tai_bo_cai(url, thu_muc)` / `tai_va_cai(url)` khớp Task 3↔4↔5.
