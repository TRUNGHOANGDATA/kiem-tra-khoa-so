@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title Kiem tra khoa so cuoi ky

REM ===== 1. Tim Python =====
REM Uu tien py launcher, sau do python trong PATH.
set "PY="
where py >nul 2>&1 && set "PY=py"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY (
  echo.
  echo   [X] May chua cai Python.
  echo   Tai ban 3.11 tro len tai: https://www.python.org/downloads/
  echo   Khi cai nho tich "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)

REM ===== 2. Kiem tra thu vien, chi cai khi thieu =====
%PY% -c "import webview, pandas, python_calamine, xlsxwriter, openpyxl" >nul 2>&1
if errorlevel 1 (
  echo.
  echo   Lan dau chay: dang cai cac thu vien can thiet, vui long doi mot chut...
  echo.
  %PY% -m pip install -r requirements.txt
  if errorlevel 1 (
    echo.
    echo   [X] Cai thu vien that bai. Kiem tra ket noi mang roi chay lai file nay.
    echo.
    pause
    exit /b 1
  )
)

REM ===== 3. Chay ung dung =====
%PY% -m app.main
if errorlevel 1 (
  echo.
  echo   [X] Khong mo duoc ung dung. Xem thong bao loi ben tren.
  echo.
  pause
  exit /b 1
)
endlocal
