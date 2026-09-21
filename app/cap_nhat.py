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
