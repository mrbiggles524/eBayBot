# PowerShell script to cleanly restart the Flask server
Write-Host "============================================================"
Write-Host "RESTARTING FLASK SERVER"
Write-Host "============================================================"
Write-Host ""

# Kill all Python processes
Write-Host "Killing all Python processes..."
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

# Check if any are still running
$remaining = Get-Process python -ErrorAction SilentlyContinue
if ($remaining) {
    Write-Host "Warning: Some Python processes may still be running"
    $remaining | Stop-Process -Force
    Start-Sleep -Seconds 2
}

Write-Host "All Python processes killed"
Write-Host ""

# Start the server
Write-Host "Starting Flask server..."
Write-Host "============================================================"
Write-Host ""
python app.py
