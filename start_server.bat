@echo off
echo ============================================================
echo Starting Flask Server
echo ============================================================
echo.

REM Kill any existing Python processes
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Start the server
python app.py

pause
