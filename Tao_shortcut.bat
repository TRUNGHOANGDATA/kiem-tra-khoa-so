@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Tao shortcut co icon
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\tao_shortcut.ps1"
if errorlevel 1 (
  echo.
  echo   [X] Khong tao duoc shortcut. Xem thong bao loi ben tren.
  echo.
)
pause
