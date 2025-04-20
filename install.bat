@echo off
rem ───────────────────────────────────────────────
rem  One‑time setup script
rem ───────────────────────────────────────────────

rem — check for Python —
python --version >NUL 2>&1 || (
    echo [ERROR] Python 3.10+ not found.  Install Python from https://python.org and rerun.
    pause
    exit /B 1
)

rem — create venv if it does not exist —
if not exist ".venv" (
    echo Creating virtual‑environment …
    python -m venv .venv
)

rem — activate venv —
call ".venv\Scripts\activate.bat"

rem — upgrade pip (optional but helpful) —
python -m pip install --upgrade pip

rem — install dependencies —
if exist requirements.txt (
    echo Installing packages from requirements.txt …
    pip install -r requirements.txt
) else (
    echo requirements.txt not found!  Aborting.
    pause
    exit /B 1
)

echo.
echo ✅  Installation finished.
echo    Run start.bat from now on.
pause
