@echo off
REM ─────────────────────────────────────────────────────────────────────────
REM  Dogesh Assistant – Windows Setup
REM  Double-click or run from Command Prompt
REM ─────────────────────────────────────────────────────────────────────────
echo.
echo  ============================================================
echo    Dogesh Assistant  -  Windows Setup
echo  ============================================================
echo.

echo [1/3] Creating virtual environment...
python -m venv .venv
call .venv\Scripts\activate.bat

echo [2/3] Installing packages...
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo [3/3] Setting up .env...
if not exist .env (
    copy .env.example .env
    echo   .env created
) else (
    echo   .env already exists
)

echo.
echo  ============================================================
echo   Setup complete!  Run:  flet run main.py
echo  ============================================================
echo.
pause
