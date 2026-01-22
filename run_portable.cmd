@echo off
REM Portable Invoice Software Launcher
REM Works from any drive (USB, network, etc.)

setlocal

title Invoice Software (Portable)

REM Get current directory (works even from PowerShell)
set "PROJECT_DIR=%~dp0"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

REM Remove any quotes
set "PROJECT_DIR=%PROJECT_DIR:"=%"

cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  Medicine Wheel Ranch - PORTABLE Invoice Software        ║
echo ║  Running from: %PROJECT_DIR%                               ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.10+
    echo    from https://python.org and add to PATH
    pause
    exit /b 1
)

REM Check/create virtual environment
if not exist "%PROJECT_DIR%\venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv "%PROJECT_DIR%\venv"
    timeout /t 2 >nul
)

REM Activate venv
echo Activating environment...
call "%PROJECT_DIR%\venv\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install dependencies if needed
if not exist "%PROJECT_DIR%\venv\.installed" (
    echo Installing packages...
    pip install -r "%PROJECT_DIR%\requirements.txt"
    if !errorlevel! neq 0 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
    echo. > "%PROJECT_DIR%\venv\.installed"
    echo ✅ Installation complete!
)

REM Ensure directories exist (with full paths)
echo Creating directories...
if not exist "%PROJECT_DIR%\data" mkdir "%PROJECT_DIR%\data"
if not exist "%PROJECT_DIR%\pdfs" mkdir "%PROJECT_DIR%\pdfs"
if not exist "%PROJECT_DIR%\signatures" mkdir "%PROJECT_DIR%\signatures"

REM Start server
echo.
echo 🚀 Starting server...
echo 🌐 Open browser to: http://localhost:3000
echo 📁 PDFs saved to: %PROJECT_DIR%\pdfs
echo 💾 Database: %PROJECT_DIR%\data
echo ✍️  Signatures: %PROJECT_DIR%\signatures
echo.
echo Press CTRL+C to stop
echo.

python "%PROJECT_DIR%\server.py"