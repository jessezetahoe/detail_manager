@echo off
setlocal
rem Development copy of Detail Manager. Runs beside the daily program:
rem own port (8769) and its OWN copy of the index and thumbnails, so nothing
rem tried here can change what the daily program shows.
set "DAILY=%LOCALAPPDATA%\ZE Detail Manager POC 07A"
set "DEV=%LOCALAPPDATA%\ZE Detail Manager Dev"
set "ZE_DETAIL_MANAGER_DATA_DIR=%DEV%"

if exist "%DEV%\dev_copy_complete.txt" goto run

if not exist "%DAILY%\detail_library.sqlite" (
  echo The daily index was not found at:
  echo   %DAILY%
  echo Nothing was started. Tell Claude what this message says.
  pause
  exit /b 1
)
echo ONE-TIME STEP: copying the daily index and thumbnails to
echo   %DEV%
echo About 7 GB. This can take 5 to 15 minutes. The daily program is not changed.
echo.
robocopy "%DAILY%" "%DEV%" /E /XD staging logs thumbnail_jobs /R:1 /W:1 /NFL /NDL /NP
if errorlevel 8 (
  echo.
  echo The copy did not finish ^(not enough disk space?^). Nothing was started.
  echo Tell Claude what this window says.
  pause
  exit /b 1
)
echo copied from "%DAILY%" on %DATE% %TIME% > "%DEV%\dev_copy_complete.txt"
echo Copy finished.
echo.

:run
py "%~dp0src\detail_manager.py" --port 8769
pause
