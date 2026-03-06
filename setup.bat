@echo off
echo ===================================================
echo FedCredit Score - Environment Setup
echo ===================================================

echo.
echo [1] Checking for virtual environment...
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Virtual environment not found. Creating a new one in 'venv'...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment. Please ensure Python is installed and added to PATH.
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created.
) else (
    echo [INFO] Virtual environment 'venv' already exists.
)

echo.
echo [2] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [3] Installing/Updating project and dependencies...
echo [INFO] Running 'pip install -e .'
python -m pip install --upgrade pip
pip install -e .

echo.
echo ===================================================
echo Setup Complete!
echo ===================================================
echo To run the application, type:
echo.
echo     venv\Scripts\activate
echo     uvicorn backend.main:app --reload --port 8000
echo.
pause
