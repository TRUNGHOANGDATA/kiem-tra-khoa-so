# Cấu hình thư mục (Cài đặt) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development hoặc executing-plans để thực thi từng task. Bước dùng checkbox `- [ ]`.

**Goal:** Cho người dùng đặt **thư mục Nguồn / Xuất / Kho** qua một màn **Cài đặt** (có nút chọn thư mục) hoặc sửa tay một **file JSON có mẫu template**; app **đọc lại cấu hình mỗi lần dùng** nên sửa file là có hiệu lực ngay ở thao tác kế tiếp.

**Architecture:** Thêm module `app/cau_hinh.py` (đọc/ghi JSON, tự tạo từ mẫu lần đầu, gộp mặc định). `app/api.py` biến 3 thuộc tính thư mục thành **property đọc cấu hình**, kèm **setter lưu override** để không vỡ test cũ (test gán thẳng `api.thu_muc_source = …`). UI thêm nút ⚙ Cài đặt + modal 3 dòng thư mục.

**Tech Stack:** Python `json` (stdlib), pywebview folder dialog; HTML/CSS/JS thuần.

**Spec/Decisions (đã chốt với người dùng):**
- Phạm vi: **Nguồn + Xuất + Kho** (3 thư mục).
- Tự cập nhật: **đọc lại mỗi lần dùng** (mở hộp thoại/quét/xuất/mở kho) — không thêm dependency, không luồng nền.
- Định dạng: **JSON** — `cau-hinh.json` (thực, git-ignored, tự tạo từ mẫu lần đầu) + `cau-hinh.mau.json` (mẫu commit sẵn).
- Giao diện: **màn Cài đặt** (nút ⚙ trên header) với nút "Chọn…" (hộp thoại thư mục) cho từng mục + Lưu; sửa tay file JSON cũng được.

## Global Constraints
- Giữ **toàn bộ test hiện có xanh** dưới `pytest -W error` (số hiện tại tăng dần theo các đợt; chạy `pytest -W error` để biết mốc trước khi bắt đầu).
- **Không thêm thư viện ngoài.**
- **Giữ hành vi cũ cho người dùng hiện tại:** mặc định vẫn là `1. Source` / `2. Report` / `3. Chot so` (đường dẫn tương đối, giải theo gốc repo `GOC`).
- **Không vỡ test:** `api.thu_muc_source`, `api.thu_muc_report`, `api._thu_muc_kho` phải **vẫn gán đè được** (8 chỗ test đang gán/`monkeypatch.setattr`). Đường dẫn tương đối trong cấu hình giải theo `GOC`; đường dẫn tuyệt đối giữ nguyên.
- `cau-hinh.json` **git-ignored** (có thể chứa đường dẫn tuyệt đối theo máy).

---

### Task 1: Module `app/cau_hinh.py` — đọc/ghi/first-run

**Files:**
- Create: `app/cau_hinh.py`
- Test: `tests/test_cau_hinh.py`

**Interfaces — Produces:**
- `KHOA = ("thu_muc_nguon", "thu_muc_xuat", "thu_muc_kho")`
- `MAC_DINH = {"thu_muc_nguon": "1. Source", "thu_muc_xuat": "2. Report", "thu_muc_kho": "3. Chot so"}`
- `duong_dan_cau_hinh(goc) -> Path` → `goc/"cau-hinh.json"`
- `doc_cau_hinh(goc) -> dict` — trả 3 khóa, **đường dẫn đã giải tuyệt đối** theo `goc`. Tự tạo `cau-hinh.json` từ mẫu (hoặc từ `MAC_DINH`) nếu chưa có; JSON hỏng → dùng `MAC_DINH` (không ném).
- `ghi_cau_hinh(goc, cfg: dict) -> None` — ghi JSON (chỉ 3 khóa hợp lệ; giữ nguyên giá trị người dùng nhập, kể cả tương đối).

- [ ] **Step 1: Test**

```python
import json
from pathlib import Path
from app import cau_hinh

def test_doc_tao_file_tu_mac_dinh_khi_chua_co(tmp_path):
    cfg = cau_hinh.doc_cau_hinh(str(tmp_path))
    assert (tmp_path / "cau-hinh.json").exists()
    # tương đối -> giải theo gốc
    assert cfg["thu_muc_nguon"] == str(tmp_path / "1. Source")
    assert cfg["thu_muc_xuat"] == str(tmp_path / "2. Report")
    assert cfg["thu_muc_kho"] == str(tmp_path / "3. Chot so")

def test_doc_ton_trong_gia_tri_da_ghi(tmp_path):
    cau_hinh.ghi_cau_hinh(str(tmp_path), {"thu_muc_nguon": "D:/Ke Toan/Nguon",
                                          "thu_muc_xuat": "2. Report", "thu_muc_kho": "3. Chot so"})
    cfg = cau_hinh.doc_cau_hinh(str(tmp_path))
    assert cfg["thu_muc_nguon"] == "D:/Ke Toan/Nguon"           # tuyệt đối -> giữ nguyên
    assert cfg["thu_muc_xuat"] == str(tmp_path / "2. Report")   # tương đối -> giải

def test_json_hong_thi_ve_mac_dinh(tmp_path):
    (tmp_path / "cau-hinh.json").write_text("{ hỏng", encoding="utf-8")
    cfg = cau_hinh.doc_cau_hinh(str(tmp_path))
    assert cfg["thu_muc_kho"] == str(tmp_path / "3. Chot so")

def test_thieu_khoa_thi_bu_mac_dinh(tmp_path):
    (tmp_path / "cau-hinh.json").write_text(json.dumps({"thu_muc_nguon": "X"}), encoding="utf-8")
    cfg = cau_hinh.doc_cau_hinh(str(tmp_path))
    assert cfg["thu_muc_nguon"].endswith("X")
    assert cfg["thu_muc_xuat"] == str(tmp_path / "2. Report")   # khóa thiếu -> mặc định
```

- [ ] **Step 2: Chạy — đỏ.** `pytest tests/test_cau_hinh.py -v` → FAIL (chưa có module).

- [ ] **Step 3: Viết `app/cau_hinh.py`**

```python
"""Cấu hình thư mục (Nguồn/Xuất/Kho) — đọc JSON, tự tạo từ mẫu, đọc lại mỗi lần dùng.

Đường dẫn tương đối giải theo gốc repo; đường dẫn tuyệt đối giữ nguyên. Ghi/đọc
không bao giờ ném ra ngoài: file hỏng/thiếu khóa -> bù mặc định, để một file JSON
gõ nhầm không làm chết app."""
from __future__ import annotations

import json
from pathlib import Path

KHOA = ("thu_muc_nguon", "thu_muc_xuat", "thu_muc_kho")
MAC_DINH = {"thu_muc_nguon": "1. Source", "thu_muc_xuat": "2. Report", "thu_muc_kho": "3. Chot so"}


def duong_dan_cau_hinh(goc: str) -> Path:
    return Path(goc) / "cau-hinh.json"


def _giai(goc: str, gia_tri: str) -> str:
    p = Path(gia_tri)
    return str(p if p.is_absolute() else Path(goc) / gia_tri)


def _doc_tho(goc: str) -> dict:
    f = duong_dan_cau_hinh(goc)
    if not f.exists():
        mau = Path(goc) / "cau-hinh.mau.json"
        nguon = mau if mau.exists() else None
        try:
            data = json.loads(nguon.read_text(encoding="utf-8")) if nguon else dict(MAC_DINH)
        except (OSError, json.JSONDecodeError):
            data = dict(MAC_DINH)
        _ghi_tho(goc, {k: data.get(k, MAC_DINH[k]) for k in KHOA})
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(MAC_DINH)


def _ghi_tho(goc: str, cfg: dict) -> None:
    sach = {k: str(cfg.get(k, MAC_DINH[k])) for k in KHOA}
    duong_dan_cau_hinh(goc).write_text(json.dumps(sach, ensure_ascii=False, indent=2), encoding="utf-8")


def doc_cau_hinh(goc: str) -> dict:
    tho = _doc_tho(goc)
    return {k: _giai(goc, str(tho.get(k, MAC_DINH[k]))) for k in KHOA}


def ghi_cau_hinh(goc: str, cfg: dict) -> None:
    _ghi_tho(goc, cfg)
```

- [ ] **Step 4: Chạy — xanh.** `pytest tests/test_cau_hinh.py -v`.

- [ ] **Step 5: Commit** `feat(cau-hinh): module doc/ghi cau hinh thu muc (JSON, tu tao tu mac dinh)`.

---

### Task 2: File mẫu template + git-ignore

**Files:**
- Create: `cau-hinh.mau.json`
- Modify: `.gitignore`

- [ ] **Step 1: Tạo `cau-hinh.mau.json`** (commit — mẫu để người dùng chép/tham khảo; dùng đường dẫn tương đối mặc định):

```json
{
  "_huong_dan": "Copy file nay thanh 'cau-hinh.json' (hoac de app tu tao) roi sua 3 duong dan ben duoi. Duong dan tuong doi tinh theo thu muc app; tuyet doi (vd D:/Ke Toan/Nguon) cung duoc. App doc lai moi lan dung nen sua xong khong can khoi dong lai.",
  "thu_muc_nguon": "1. Source",
  "thu_muc_xuat": "2. Report",
  "thu_muc_kho": "3. Chot so"
}
```
(Khóa `_huong_dan` bị `doc_cau_hinh` bỏ qua vì không nằm trong `KHOA` — an toàn.)

- [ ] **Step 2: `.gitignore`** thêm:
```
# Cấu hình theo máy (có thể chứa đường dẫn tuyệt đối) — không commit
cau-hinh.json
```

- [ ] **Step 3: Kiểm** `git status --porcelain cau-hinh.json` rỗng sau khi app/test tạo ra nó.

- [ ] **Step 4: Commit** `chore(cau-hinh): them file mau + git-ignore cau-hinh.json`.

---

### Task 3: `api.py` — thư mục đọc từ cấu hình (giữ gán đè) + API Cài đặt

**Files:**
- Modify: `app/api.py`
- Test: `tests/test_cau_hinh_api.py`

**Interfaces:**
- Consumes: `app.cau_hinh`.
- Produces (JsApi):
  - `thu_muc_source` / `thu_muc_report` / `_thu_muc_kho` là **property**: trả override nếu đã gán, ngược lại đọc `cau_hinh.doc_cau_hinh(GOC)`. Mỗi cái có **setter** lưu override (giữ tương thích test).
  - `lay_cau_hinh() -> dict` — giá trị THÔ hiện tại (chưa giải tuyệt đối, để hiện trong ô nhập) + đường dẫn đã giải để hiển thị.
  - `luu_cau_hinh(cfg) -> {"ok": True}|{"loi":...}`.
  - `chon_thu_muc() -> {"path":...}|{"huy":True}|{"loi":...}` (hộp thoại FOLDER).

- [ ] **Step 1: Test** (`tests/test_cau_hinh_api.py`)

```python
from app.api import JsApi
from app import cau_hinh

def test_thu_muc_doc_tu_cau_hinh(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)   # ep GOC ve tmp
    cau_hinh.ghi_cau_hinh(str(tmp_path), {"thu_muc_nguon": "Nguon", "thu_muc_xuat": "Xuat", "thu_muc_kho": "Kho"})
    api = JsApi()
    assert api.thu_muc_source == str(tmp_path / "Nguon")
    assert api.thu_muc_report == str(tmp_path / "Xuat")
    assert api._thu_muc_kho == str(tmp_path / "Kho")

def test_gan_de_van_thang_cau_hinh(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    api.thu_muc_source = str(tmp_path / "ghi_de")     # gan thang -> override
    assert api.thu_muc_source == str(tmp_path / "ghi_de")
    api._thu_muc_kho = str(tmp_path / "kho_de")
    assert api._thu_muc_kho == str(tmp_path / "kho_de")

def test_luu_roi_doc_lai_phan_anh_ngay(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.GOC", tmp_path)
    api = JsApi()
    assert api.luu_cau_hinh({"thu_muc_nguon": "A", "thu_muc_xuat": "B", "thu_muc_kho": "C"}) == {"ok": True}
    assert api.thu_muc_source == str(tmp_path / "A")   # doc lai moi lan dung -> thay ngay
```

- [ ] **Step 2: Chạy — đỏ.**

- [ ] **Step 3: Sửa `app/api.py`**

Thêm import: `from . import cau_hinh` (cạnh các import `from .` khác).

Trong `JsApi.__init__`, BỎ ba dòng gán cứng `self.thu_muc_source/report/_thu_muc_kho` và thay bằng khởi tạo override rỗng:
```python
        self._ovr_thu_muc: dict[str, str] = {}   # thư mục gán đè (test/phiên tạm) — thắng cấu hình
```

Thêm helper + property (đặt gần đầu lớp, sau `__init__`):
```python
    def _tm(self, khoa: str) -> str:
        if khoa in self._ovr_thu_muc:
            return self._ovr_thu_muc[khoa]
        return cau_hinh.doc_cau_hinh(str(GOC))[khoa]

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
```
(`GOC` đã là `Path(__file__).resolve().parents[1]` ở đầu file — dùng `str(GOC)`.)

Thêm phương thức Cài đặt (cuối lớp):
```python
    def lay_cau_hinh(self) -> dict:
        """Giá trị thô (để hiện trong ô nhập) + đường dẫn đã giải (để hiển thị)."""
        tho = cau_hinh._doc_tho(str(GOC))
        giai = cau_hinh.doc_cau_hinh(str(GOC))
        return {"tho": {k: str(tho.get(k, cau_hinh.MAC_DINH[k])) for k in cau_hinh.KHOA}, "giai": giai}

    def luu_cau_hinh(self, cfg: dict):
        try:
            cau_hinh.ghi_cau_hinh(str(GOC), {k: str((cfg or {}).get(k, cau_hinh.MAC_DINH[k])) for k in cau_hinh.KHOA})
            return {"ok": True}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không lưu được cấu hình: {e}"}

    def chon_thu_muc(self):
        if self._window is None:
            return {"loi": "Chưa có cửa sổ"}
        try:
            import webview
            loai = getattr(getattr(webview, "FileDialog", None), "FOLDER", None) or webview.FOLDER_DIALOG
            chon = self._window.create_file_dialog(loai)
            return {"path": chon[0]} if chon else {"huy": True}
        except Exception as e:  # noqa: BLE001
            return {"loi": f"Không mở được hộp thoại thư mục: {e}"}
```

- [ ] **Step 4: Chạy** `pytest tests/test_cau_hinh_api.py -v` rồi **full** `pytest -W error`. Sửa nếu có test cũ vỡ (không nên: property+setter giữ nguyên ngữ nghĩa gán). Lưu ý: các test cũ tạo `JsApi()` rồi dùng thư mục mặc định — giờ `doc_cau_hinh` sẽ **tạo `cau-hinh.json` ở GOC repo thật** khi chạy test không ép GOC. Để tránh rác/ghi vào repo: các test cũ chỉ ĐỌC thư mục khi thao tác file; nếu có test chạm, ép `monkeypatch.setattr("app.api.GOC", tmp_path)` hoặc gán đè thuộc tính (đa số đã gán đè sẵn). Kiểm `git status` sau test: `cau-hinh.json` phải git-ignored (Task 2) nên không hiện.

- [ ] **Step 5: Commit** `feat(api): thu muc doc tu cau hinh (giu gan de) + lay/luu/chon thu muc`.

---

### Task 4: UI — nút ⚙ Cài đặt + modal chọn thư mục

**Files:**
- Modify: `app/web/index.html`, `app/web/app.js`, `app/web/style.css`

**Interfaces:** gọi `api.lay_cau_hinh()`, `api.chon_thu_muc()`, `api.luu_cau_hinh(cfg)`.

- [ ] **Step 1: Xác định điểm chèn** — READ `index.html` header (nút `#btn-lich-su`) và `app.js` (mẫu modal `#modal-chot`, `toast`, `esc`, `$`). Dùng lại khung `.modal`/`.an`.

- [ ] **Step 2: Nút ⚙ trên header** (cạnh "Lịch sử chốt sổ"), id `#btn-cai-dat`, icon bánh răng (SVG cùng họ, stroke currentColor).

- [ ] **Step 3: Modal Cài đặt** trong `index.html` (ẩn `.an`), 3 dòng (Nguồn/Xuất/Kho), mỗi dòng: nhãn + `<input>` (giá trị thô, sửa tay được) + nút "Chọn…". Chân: "Hủy" / "Lưu".

```html
<div id="modal-cai-dat" class="modal an" role="dialog" aria-modal="true" aria-labelledby="modal-cai-dat-tieu-de">
  <div class="modal-hop">
    <h3 id="modal-cai-dat-tieu-de">Cài đặt thư mục</h3>
    <p class="modal-tt">App đọc lại cấu hình mỗi lần dùng — sửa xong bấm Lưu là có hiệu lực ngay.</p>
    <div class="cd-hang"><label>Thư mục Nguồn</label>
      <div class="cd-o"><input id="cd-nguon" type="text"><button class="btn btn-phu" type="button" onclick="chonThuMuc('cd-nguon')">Chọn…</button></div></div>
    <div class="cd-hang"><label>Thư mục Xuất báo cáo</label>
      <div class="cd-o"><input id="cd-xuat" type="text"><button class="btn btn-phu" type="button" onclick="chonThuMuc('cd-xuat')">Chọn…</button></div></div>
    <div class="cd-hang"><label>Thư mục Kho chốt sổ</label>
      <div class="cd-o"><input id="cd-kho" type="text"><button class="btn btn-phu" type="button" onclick="chonThuMuc('cd-kho')">Chọn…</button></div></div>
    <div class="hang-nut">
      <button class="btn btn-phu" type="button" onclick="dongCaiDat()">Hủy</button>
      <button class="btn btn-chinh" type="button" onclick="luuCaiDat()">Lưu</button>
    </div>
  </div>
</div>
```

- [ ] **Step 4: JS** (app.js)

```js
async function moCaiDat() {
  const c = await api.lay_cau_hinh();
  if (c.loi) { toast(c.loi); return; }
  $("cd-nguon").value = c.tho.thu_muc_nguon;
  $("cd-xuat").value = c.tho.thu_muc_xuat;
  $("cd-kho").value = c.tho.thu_muc_kho;
  $("modal-cai-dat").classList.remove("an");
}
function dongCaiDat() { $("modal-cai-dat").classList.add("an"); }
async function chonThuMuc(idO) {
  const f = await api.chon_thu_muc();
  if (!f || f.huy) return;
  if (f.loi) { toast(f.loi); return; }
  $(idO).value = f.path;
}
async function luuCaiDat() {
  const cfg = { thu_muc_nguon: $("cd-nguon").value.trim(),
                thu_muc_xuat: $("cd-xuat").value.trim(),
                thu_muc_kho: $("cd-kho").value.trim() };
  const k = await api.luu_cau_hinh(cfg);
  if (k.loi) { toast(k.loi); return; }
  dongCaiDat();
  toast("Đã lưu cài đặt thư mục");
}
$("btn-cai-dat").onclick = moCaiDat;
```

- [ ] **Step 5: CSS** (`.cd-hang`, `.cd-o`) — dòng nhãn trên, ô input + nút "Chọn…" cùng hàng; theo hệ Premium Light. `node --check app/web/app.js`.

- [ ] **Step 6: Kiểm thủ công** (browser pane với stub `api`): mở modal, đổi giá trị, Lưu → toast; xác nhận `lay_cau_hinh`/`luu_cau_hinh` được gọi đúng.

- [ ] **Step 7: Commit** `feat(ui): man Cai dat thu muc (Nguon/Xuat/Kho) + nut chon thu muc`.

---

## Self-Review
- Phạm vi (Nguồn/Xuất/Kho) → Task 1 `MAC_DINH`/`KHOA`, Task 3 property, Task 4 UI. ✔
- Đọc lại mỗi lần dùng → property gọi `doc_cau_hinh` mỗi lần đọc (Task 3). ✔
- JSON + mẫu + first-run → Task 1 `_doc_tho` tự tạo, Task 2 mẫu. ✔
- Giao diện + folder picker → Task 4 + `chon_thu_muc` (Task 3). ✔
- **Không vỡ test** (8 chỗ gán đè) → property có setter lưu override, giải quyết ở Task 3 Step 3; rủi ro test cũ chạm GOC thật ghi `cau-hinh.json` → git-ignored (Task 2) + kiểm `git status` (Task 3 Step 4). ✔
- Không thêm dependency; đường dẫn tương đối/tuyệt đối phân biệt trong `_giai`. ✔

**Rủi ro cần lưu ý:** `chon_thu_muc` phụ thuộc hằng dialog của pywebview (`FileDialog.FOLDER` / `FOLDER_DIALOG`) — cùng lối `chon_file_sqlite` đã chạy; nếu API webview khác, bắt lỗi trả `{loi}`. Test cũ tạo `JsApi()` không ép GOC sẽ khiến `doc_cau_hinh` tạo `cau-hinh.json` ở repo — phải chắc nó git-ignored trước khi merge.
