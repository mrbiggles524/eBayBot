@echo off
title eBay Bot Setup
echo ========================================
echo   eBay Card Listing Bot - Setup UI
echo ========================================
echo.
echo Starting setup wizard...
echo This will open in your web browser.
echo.
python -m streamlit run start.py
if errorlevel 1 (
    echo.
    echo ERROR: Could not start the setup UI.
    echo Make sure Python and Streamlit are installed.
    echo.
    pause
)
