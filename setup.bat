@echo off
echo ============================================
echo   Solar AI Advisor — Windows Setup Script
echo ============================================
echo.

:: Step 1 - Create virtual environment
if not exist "venv" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
) else (
    echo [1/4] Virtual environment already exists, skipping.
)

:: Step 2 - Activate and install dependencies
echo [2/4] Installing Python dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip --quiet
pip install -r requirements.txt

:: Step 3 - Create .env from template
if not exist ".env" (
    echo [3/4] Copying .env.example to .env...
    copy .env.example .env
    echo       ^^^ Edit .env and add your GEMINI_API_KEY before running.
) else (
    echo [3/4] .env already exists, skipping.
)

:: Step 4 - Done
echo.
echo [4/4] Setup complete!
echo.
echo  Next steps:
echo   1. Edit .env and set GEMINI_API_KEY
echo   2. Run:  python build_rag.py     (builds the knowledge base)
echo   3. Run:  streamlit run app.py    (starts the app)
echo.
pause
