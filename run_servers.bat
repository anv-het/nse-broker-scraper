@echo off
REM NSE Broker Dashboard - Server Startup Script (Batch Version)
REM This script starts both backend (Flask) and frontend (http-server) servers

color 0B
echo ========================================
echo NSE Broker Dashboard - Server Startup
echo ========================================
echo.

REM Define ports
set BACKEND_PORT=8755
set FRONTEND_PORT=1050

REM Check if virtual environment exists
echo Step 1: Checking Python virtual environment...
if exist ".venv\Scripts\activate.bat" (
    echo   Virtual environment found!
) else (
    color 0C
    echo   ERROR: Virtual environment not found at .venv\
    echo   Please create it first: python -m venv .venv
    pause
    exit /b 1
)

REM Clear ports
echo.
echo Step 2: Clearing ports...
echo Checking for processes on port %BACKEND_PORT%...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT% " ^| findstr "LISTENING"') do (
    echo   Found process %%a on port %BACKEND_PORT%. Stopping...
    taskkill /F /PID %%a >nul 2>&1
)
echo   Port %BACKEND_PORT% cleared!

echo Checking for processes on port %FRONTEND_PORT%...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%FRONTEND_PORT% " ^| findstr "LISTENING"') do (
    echo   Found process %%a on port %FRONTEND_PORT%. Stopping...
    taskkill /F /PID %%a >nul 2>&1
)
echo   Port %FRONTEND_PORT% cleared!

REM Start Backend Server
echo.
echo Step 3: Starting Backend Server (Flask on port %BACKEND_PORT%)...
start "Backend Server (Port %BACKEND_PORT%)" cmd /k "echo ======================================== & echo Backend Server - Flask (Port %BACKEND_PORT%) & echo ======================================== & echo. & call .venv\Scripts\activate.bat & cd broker-project\backend & echo Starting Flask server... & python run_server.py"
timeout /t 2 /nobreak >nul
echo   Backend server starting in new window...

REM Start Frontend Server
echo.
echo Step 4: Starting Frontend Server (HTTP on port %FRONTEND_PORT%)...
start "Frontend Server (Port %FRONTEND_PORT%)" cmd /k "echo ======================================== & echo Frontend Server - HTTP (Port %FRONTEND_PORT%) & echo ======================================== & echo. & cd broker-project\frontend & echo Starting HTTP server... & npm run dev"
timeout /t 2 /nobreak >nul
echo   Frontend server starting in new window...

REM Display status
echo.
echo ========================================
color 0A
echo Servers Started Successfully!
color 0B
echo ========================================
echo.
echo Backend (Flask):  http://192.168.119.183:%BACKEND_PORT%
echo Frontend (HTTP):  http://192.168.119.183:%FRONTEND_PORT%
echo.
echo API Base URL:     http://192.168.119.183:%BACKEND_PORT%/api/v1
echo.
echo ========================================
echo.
echo Both servers are running in separate windows.
echo Close those windows to stop the servers.
echo.
echo You can close this window now.
echo.
pause
