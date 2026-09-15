@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m app.main
if errorlevel 1 (
  echo.
  echo Khong chay duoc app. Kiem tra da cai Python va: pip install -r requirements.txt
  pause
)
