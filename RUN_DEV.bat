@echo off
rem Development copy of Detail Manager. Runs beside the daily one (own port 8769).
rem It reads the SAME library index and thumbnails as the daily program on this computer.
set "ZE_DETAIL_MANAGER_DATA_DIR=%LOCALAPPDATA%\ZE Detail Manager POC 07A"
if not exist "%ZE_DETAIL_MANAGER_DATA_DIR%\detail_library.sqlite" (
  echo The daily index was not found at:
  echo   %ZE_DETAIL_MANAGER_DATA_DIR%
  echo Nothing was started. Tell Claude what this message says.
  pause
  exit /b 1
)
py "%~dp0src\detail_manager.py" --port 8769
pause
