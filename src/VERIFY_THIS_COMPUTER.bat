@echo off
setlocal
cd /d "%~dp0"
echo Detail Manager Prototype 0.1 - Verification
echo ===========================================
echo.
where py >nul 2>&1 && (echo [OK] Python launcher found) || (echo [FAIL] Python launcher not found)
py -3 --version 2>nul
py -3 -c "import tkinter; print('[OK] Tkinter available')" 2>nul
py -3 -c "import fitz; print('[OK] PyMuPDF available')" 2>nul
echo.
echo Local Detail Manager data will be stored in:
echo %LOCALAPPDATA%\ZE Detail Manager Prototype 0.1
echo.
echo SketchUp/LayOut are not installed or modified by this package.
echo Confirm SketchUp/LayOut is already available before rendering thumbnails.
echo.
pause
