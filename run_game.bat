@echo off
REM Run script: Starts server and 2 clients for local testing (Windows native)
REM Usage: run_game.bat

setlocal

echo Starting game server and clients...
echo.

REM Check for and kill any existing game processes
echo Cleaning up existing processes...
taskkill /F /FI "WINDOWTITLE eq TD Server*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq TD Client*" >nul 2>&1
timeout /t 1 /nobreak >nul

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found in PATH
    pause
    exit /b 1
)

echo Starting server...
start "TD Server" cmd /k "python -m server.src.td_server.main"

echo Waiting for server to initialize...
timeout /t 3 /nobreak >nul

echo Starting client 1...
start "TD Client 1" cmd /k "set TD_SERVER_ADDR=localhost:42069 && python -m client.src.td_client.main"

echo Waiting before starting client 2...
timeout /t 1 /nobreak >nul

echo Starting client 2...
start "TD Client 2" cmd /k "set TD_SERVER_ADDR=localhost:42069 && python -m client.src.td_client.main"

echo.
echo ======================================
echo All processes started successfully!
echo ======================================
echo.
echo Server PID: Check "TD Server" window
echo Client 1 PID: Check "TD Client 1" window
echo Client 2 PID: Check "TD Client 2" window
echo.
echo To stop: Close the individual windows or press Ctrl+C in each window
echo.
pause
