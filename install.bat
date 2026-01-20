@echo off
REM APIC Installation Script for Windows
REM Handles package installation with retry logic for network issues

setlocal enabledelayedexpansion

REM Configuration
set MAX_RETRIES=3
set RETRY_DELAY=5
set PIP_TIMEOUT=300

echo =====================================
echo APIC Installation Script
echo =====================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python %PYTHON_VERSION% detected
echo.

REM Check if virtual environment is activated
if "%VIRTUAL_ENV%"=="" (
    echo Warning: No virtual environment detected
    echo It's recommended to use a virtual environment
    choice /M "Continue anyway?"
    if errorlevel 2 (
        echo Creating virtual environment...
        python -m venv venv
        echo Virtual environment created
        echo Please activate it with: venv\Scripts\activate
        echo Then run this script again
        exit /b 0
    )
) else (
    echo Virtual environment activated: %VIRTUAL_ENV%
)
echo.

REM Upgrade pip, setuptools, and wheel first
echo Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel --timeout %PIP_TIMEOUT%
if errorlevel 1 (
    echo Failed to upgrade core tools
    exit /b 1
)
echo Core tools upgraded
echo.

REM Install production dependencies
if exist requirements.txt (
    echo Installing packages from requirements.txt...
    set attempt=1
    :retry_production
    echo Attempt !attempt! of %MAX_RETRIES%

    REM Set pip config file if exists
    if exist pip.conf (
        set PIP_CONFIG_FILE=pip.conf
    )

    pip install -r requirements.txt --timeout %PIP_TIMEOUT% --retries 5 --default-timeout %PIP_TIMEOUT%
    if errorlevel 1 (
        if !attempt! LSS %MAX_RETRIES% (
            echo Installation failed on attempt !attempt!
            echo Waiting %RETRY_DELAY% seconds before retry...
            timeout /t %RETRY_DELAY% /nobreak >nul
            set /a attempt+=1
            set /a RETRY_DELAY*=2
            goto retry_production
        ) else (
            echo Failed to install packages after %MAX_RETRIES% attempts
            echo Please check your network connection and try again.
            exit /b 1
        )
    )
    echo Successfully installed packages from requirements.txt
    echo.
) else (
    echo Error: requirements.txt not found
    exit /b 1
)

REM Ask about development dependencies
if exist requirements-dev.txt (
    choice /M "Install development dependencies?"
    if not errorlevel 2 (
        echo Installing packages from requirements-dev.txt...
        set attempt=1
        :retry_dev
        echo Attempt !attempt! of %MAX_RETRIES%

        pip install -r requirements-dev.txt --timeout %PIP_TIMEOUT% --retries 5 --default-timeout %PIP_TIMEOUT%
        if errorlevel 1 (
            if !attempt! LSS %MAX_RETRIES% (
                echo Installation failed on attempt !attempt!
                echo Waiting %RETRY_DELAY% seconds before retry...
                timeout /t %RETRY_DELAY% /nobreak >nul
                set /a attempt+=1
                goto retry_dev
            ) else (
                echo Warning: Development dependencies installation failed
                echo You can try installing them later manually
            )
        ) else (
            echo Successfully installed development dependencies
        )
        echo.
    )
)

REM Verify installation
echo Verifying installation...
if exist src\utils\install_verifier.py (
    python -m src.utils.install_verifier
    if errorlevel 1 (
        echo Warning: Some verification checks failed
        echo The installation may still work, but some features might be unavailable
    ) else (
        echo Installation verification passed
    )
) else (
    echo Verification script not found, skipping...
)

echo.
echo =====================================
echo Installation Complete!
echo =====================================
echo.
echo Next steps:
echo 1. Copy .env.example to .env and configure your API keys
echo 2. Start the application with: python main.py api
echo 3. In another terminal, run: python main.py frontend
echo.

endlocal
