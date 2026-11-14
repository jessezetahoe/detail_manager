@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo Detail Manager Prototype 0.1 - Presentation Computer Setup
echo ============================================================
echo.

where py >nul 2>&1
if errorlevel 1 (
    echo PYTHON NOT FOUND.
    echo.
    echo Install 64-bit Python 3.12 or newer from python.org.
    echo During installation, enable:
    echo   - Add python.exe to PATH
    echo   - pip
    echo   - Tcl/Tk and IDLE
    echo.
    echo Then run this file again.
    pause
    exit /b 1
)

echo Python found:
py -3 --version
echo.

echo Checking pip...
py -3 -m pip --version >nul 2>&1
if errorlevel 1 (
    echo pip is not available in this Python installation.
    echo Repair/reinstall Python with pip enabled, then run setup again.
    pause
    exit /b 1
)

echo Installing/updating required Python package: PyMuPDF
py -3 -m pip install --user -r requirements.txt
if errorlevel 1 (
    echo.
    echo PyMuPDF installation failed.
    echo If this computer has no internet access, connect it temporarily
    echo or install PyMuPDF before continuing.
    pause
    exit /b 1
)

echo.
echo Checking Tkinter...
py -3 -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo Tkinter is missing. Repair/reinstall Python with Tcl/Tk enabled.
    pause
    exit /b 1
)

echo.
echo Checking PyMuPDF...
py -3 -c "import fitz; print('PyMuPDF OK')" 
if errorlevel 1 (
    echo PyMuPDF test failed.
    pause
    exit /b 1
)

echo.
echo Creating Desktop shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$desktop=[Environment]::GetFolderPath('Desktop');" ^
 "$ws=New-Object -ComObject WScript.Shell;" ^
 "$s=$ws.CreateShortcut((Join-Path $desktop 'Detail Manager Prototype 0.1.lnk'));" ^
 "$s.TargetPath=(Join-Path '%~dp0' 'START_DETAIL_MANAGER.vbs');" ^
 "$s.WorkingDirectory='%~dp0';" ^
 "$s.Description='Detail Manager Prototype 0.1';" ^
 "$s.Save()"

echo.
echo ============================================================
echo SETUP COMPLETE
echo ============================================================
echo.
echo Next:
echo   1. Double-click START_DETAIL_MANAGER.vbs
echo   2. Choose the existing Distribution Library on C:
echo   3. Refresh/index the library
echo   4. Follow PRESENTATION_COMPUTER_SETUP.txt for thumbnails
echo.
pause
