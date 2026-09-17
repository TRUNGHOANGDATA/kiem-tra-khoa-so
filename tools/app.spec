# PyInstaller spec — bản đóng gói một-thư-mục (one-folder) cho tool kiểm tra khóa sổ.
#   Chạy:  python -m tools.tao_seed  &&  pyinstaller tools/app.spec --noconfirm --clean
# One-folder (không one-file) để mở nhanh, không phải giải nén ra %TEMP% mỗi lần.
from pathlib import Path

GOC = Path(SPECPATH).resolve().parent   # SPECPATH = .../tools -> parent = gốc repo

datas = [
    (str(GOC / "app" / "webapp"), "webapp"),   # bản React build -> <bundle>/webapp
    (str(GOC / "app" / "app.ico"), "."),       # icon cửa sổ/taskbar
    (str(GOC / "build" / "_seed"), "_seed"),   # kho + cấu hình bày sẵn lần đầu chạy
]

# calamine/pandas/webview có phần nạp động — gom đủ để bản đóng gói không thiếu module.
hiddenimports = [
    "python_calamine", "webview.platforms.edgechromium", "clr_loader",
    "pandas._libs.tslibs.base",
]

a = Analysis(
    [str(GOC / "tools" / "launch.py")],   # launcher import GÓI app (không chạy main.py truc tiep)
    pathex=[str(GOC)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    excludes=["pytest", "tkinter", "matplotlib", "PyQt5", "PySide2", "PySide6", "notebook"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="KiemTraKhoaSo",
    console=False,                 # ứng dụng cửa sổ, không hiện console đen
    icon=str(GOC / "app" / "app.ico"),
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=False,
    name="KiemTraKhoaSo",          # -> dist/KiemTraKhoaSo/KiemTraKhoaSo.exe
)
