"""Kiểm tra & tải bản cập nhật từ GitHub Releases công khai. Chỉ stdlib.

Không auth (repo phát hành công khai). Mọi lỗi mạng/HTTP/IO được nuốt thành
{"loi": ...} — cập nhật là tính năng phụ, không bao giờ làm app chết.
"""
from __future__ import annotations

import json
import os
import tempfile
import urllib.error
import urllib.request

# Slug repo GitHub công khai chứa release. ĐIỀN khi tạo repo (tham số triển khai duy nhất).
KHO_PHAT_HANH = "owner/ten-repo"
TEN_ASSET = "KiemTraKhoaSo-Setup"        # tiền tố tên file cài để nhận đúng asset
API_LATEST = f"https://api.github.com/repos/{KHO_PHAT_HANH}/releases/latest"


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
