@echo off
setlocal
title ZE Detail Manager
rem Daily-use copy of Detail Manager. Its own index and thumbnails live in
rem   %LOCALAPPDATA%\ZE Detail Manager
rem The first start copies them once from the development copy (already
rem refreshed with the new titles and clean text). Masters on Z: are only read.
set "FROM=%LOCALAPPDATA%\ZE Detail Manager Dev"
set "ZE_DETAIL_MANAGER_DATA_DIR=%LOCALAPPDATA%\ZE Detail Manager"

if exist "%ZE_DETAIL_MANAGER_DATA_DIR%\copy_complete.txt" goto run

if not exist "%FROM%\detail_library.sqlite" (
  echo The index to copy was not found at:
  echo   %FROM%
  echo Nothing was started. Tell Claude what this message says.
  pause
  exit /b 1
)
echo ONE-TIME STEP: copying the index and thumbnails to
echo   %ZE_DETAIL_MANAGER_DATA_DIR%
echo About 7 GB, usually under a minute. Nothing else is changed.
echo.
robocopy "%FROM%" "%ZE_DETAIL_MANAGER_DATA_DIR%" /E /XD staging logs thumbnail_jobs /XF dev_copy_complete.txt /R:1 /W:1 /NFL /NDL /NP
if errorlevel 8 (
  echo.
  echo The copy did not finish ^(not enough disk space?^). Nothing was started.
  echo Tell Claude what this window says.
  pause
  exit /b 1
)
echo copied from "%FROM%" on %DATE% %TIME% > "%ZE_DETAIL_MANAGER_DATA_DIR%\copy_complete.txt"
echo Copy finished.
echo.

:run
py "%~dp0detail_manager.py"
if errorlevel 1 pause
