@echo off
title Stats Launcher
cd /d "%~dp0"
echo ============================================
echo  Local App Launcher
echo ============================================
echo.
echo If browser does not open, navigate to:
echo    http://127.0.0.1:8515
echo.
echo Close this window to stop the app.
echo.
streamlit run launcher.py --server.port 8515 --server.address 127.0.0.1
echo.
echo ============================================
echo  App stopped. Press any key to close.
echo ============================================
pause >nul
