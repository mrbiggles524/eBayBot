@echo off
echo Starting eBay Bot Flask App on port 5001...
echo.
cd /d %~dp0
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
