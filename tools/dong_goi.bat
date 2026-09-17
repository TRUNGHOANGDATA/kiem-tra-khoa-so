@echo off
chcp 65001 >nul
cd /d "%~dp0.."
title Dong goi bo cai Kiem tra khoa so

echo [1/4] Build giao dien React...
if exist "ui\package.json" ( pushd ui & call npm run build & popd )

echo [2/4] Dung seed (kho CDPS + ten chi nhanh)...
python -m tools.tao_seed || goto :loi

echo [3/4] Dong goi app (PyInstaller)...
pyinstaller tools\app.spec --noconfirm --clean --distpath build\dist --workpath build\work || goto :loi

echo [4/4] Goi bo cai (Inno Setup)...
set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" ( echo   [X] Chua cai Inno Setup: winget install JRSoftware.InnoSetup & goto :loi )
"%ISCC%" tools\installer.iss || goto :loi

echo.
echo   XONG. Bo cai o: build\Output\
dir /b build\Output\*.exe
pause
exit /b 0

:loi
echo.
echo   [X] Dong goi that bai. Xem thong bao loi ben tren.
pause
exit /b 1
