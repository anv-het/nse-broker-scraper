# NSE Broker Dashboard - Server Startup Script
# This script starts both backend (Flask) and frontend (http-server) servers

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NSE Broker Dashboard - Server Startup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Set error action preference
$ErrorActionPreference = "Stop"

# Define ports
$BACKEND_PORT = 8755
$FRONTEND_PORT = 1050

# Function to kill process on a specific port
function Stop-ProcessOnPort {
    param([int]$Port)
    
    Write-Host "Checking for processes on port $Port..." -ForegroundColor Yellow
    
    try {
        $connections = netstat -ano | Select-String ":$Port " | Select-String "LISTENING"
        
        if ($connections) {
            foreach ($connection in $connections) {
                $connectionString = $connection.ToString().Trim()
                $processId = ($connectionString -split '\s+')[-1]
                
                if ($processId -and $processId -match '^\d+$') {
                    Write-Host "  Found process $processId on port $Port. Stopping..." -ForegroundColor Red
                    taskkill /F /PID $processId 2>$null
                    Start-Sleep -Milliseconds 500
                }
            }
            Write-Host "  Port $Port cleared successfully!" -ForegroundColor Green
        } else {
            Write-Host "  Port $Port is already free" -ForegroundColor Green
        }
    } catch {
        Write-Host "  Warning: Could not check/clear port $Port" -ForegroundColor Yellow
    }
}

# Check if virtual environment exists
Write-Host "`nStep 1: Checking Python virtual environment..." -ForegroundColor Cyan
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "  Virtual environment found!" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Virtual environment not found at .\.venv\" -ForegroundColor Red
    Write-Host "  Please create it first: python -m venv .venv" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Clear ports
Write-Host "`nStep 2: Clearing ports..." -ForegroundColor Cyan
Stop-ProcessOnPort -Port $BACKEND_PORT
Stop-ProcessOnPort -Port $FRONTEND_PORT

# Start Backend Server
Write-Host "`nStep 3: Starting Backend Server (Flask on port $BACKEND_PORT)..." -ForegroundColor Cyan

$backendScript = @"
Write-Host '========================================' -ForegroundColor Magenta
Write-Host 'Backend Server (Flask - Port $BACKEND_PORT)' -ForegroundColor Magenta
Write-Host '========================================' -ForegroundColor Magenta
Write-Host ''

# Activate virtual environment
. .\.venv\Scripts\Activate.ps1

# Change to backend directory
Set-Location '.\broker-project\backend'

# Run the server
Write-Host 'Starting Flask server...' -ForegroundColor Green
python run_server.py

Write-Host ''
Write-Host 'Backend server stopped.' -ForegroundColor Yellow
Read-Host 'Press Enter to close this window'
"@

$backendScriptPath = ".\start_backend_temp.ps1"
$backendScript | Out-File -FilePath $backendScriptPath -Encoding UTF8

Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", $backendScriptPath
Write-Host "  Backend server starting in new window..." -ForegroundColor Green
Start-Sleep -Seconds 2

# Start Frontend Server
Write-Host "`nStep 4: Starting Frontend Server (http-server on port $FRONTEND_PORT)..." -ForegroundColor Cyan

$frontendScript = @"
Write-Host '========================================' -ForegroundColor Magenta
Write-Host 'Frontend Server (HTTP - Port $FRONTEND_PORT)' -ForegroundColor Magenta
Write-Host '========================================' -ForegroundColor Magenta
Write-Host ''

# Change to frontend directory
Set-Location '.\broker-project\frontend'

# Run the server
Write-Host 'Starting HTTP server...' -ForegroundColor Green
npm run dev

Write-Host ''
Write-Host 'Frontend server stopped.' -ForegroundColor Yellow
Read-Host 'Press Enter to close this window'
"@

$frontendScriptPath = ".\start_frontend_temp.ps1"
$frontendScript | Out-File -FilePath $frontendScriptPath -Encoding UTF8

Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", $frontendScriptPath
Write-Host "  Frontend server starting in new window..." -ForegroundColor Green
Start-Sleep -Seconds 2

# Display status
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Servers Started Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend (Flask):  " -NoNewline -ForegroundColor Yellow
Write-Host "http://192.168.119.183:$BACKEND_PORT" -ForegroundColor White
Write-Host "Frontend (HTTP):  " -NoNewline -ForegroundColor Yellow
Write-Host "http://192.168.119.183:$FRONTEND_PORT" -ForegroundColor White
Write-Host ""
Write-Host "API Base URL:     " -NoNewline -ForegroundColor Yellow
Write-Host "http://192.168.119.183:$BACKEND_PORT/api/v1" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Both servers are running in separate windows." -ForegroundColor Green
Write-Host "Close those windows to stop the servers." -ForegroundColor Yellow
Write-Host ""
Write-Host "You can close this window now." -ForegroundColor Cyan

# Clean up temporary scripts after 5 seconds
Start-Sleep -Seconds 5
Remove-Item $backendScriptPath -ErrorAction SilentlyContinue
Remove-Item $frontendScriptPath -ErrorAction SilentlyContinue

Write-Host ""
Read-Host "Press Enter to exit"
