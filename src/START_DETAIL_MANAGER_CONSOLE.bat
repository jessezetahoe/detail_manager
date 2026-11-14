@echo off
setlocal
cd /d "%~dp0"
py -3 detail_manager.py
if errorlevel 1 (
  echo.
  echo Detail Manager stopped with an error.
  pause
)
