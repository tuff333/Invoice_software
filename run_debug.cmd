@echo off
REM Debug Mode - Shows all errors in console

setlocal

title Invoice Software (Debug Mode)

set "PROJECT_DIR=%~dp0"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  DEBUG MODE - Invoice Software                           ║
echo ║  All errors will appear below                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

call "%PROJECT_DIR%\venv\Scripts\activate.bat"
set FLASK_APP=server.py
set FLASK_ENV=development

cd "%PROJECT_DIR%"
python server.py