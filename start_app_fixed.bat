@echo off
echo Starting eBay Bot Flask App on port 5001...
echo.
cd /d %~dp0
set LOCAL_DEV=1
set IMAGE_FETCH_DEBUG=1
echo Auto-restart on code change: ON
echo Image fetch debug: ON
echo.
echo Checking Python...
python --version
echo.
echo Starting Flask app...
python app.py
if errorlevel 1 (
    echo.
    echo ERROR: Flask app failed to start!
    echo Check the error messages above.
    pause
)
