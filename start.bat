@echo off
rem ───────────────────────────────────────────────
rem  Launch the Streamlit app
rem ───────────────────────────────────────────────

if not exist ".venv" (
    echo [ERROR] venv not found.  Run install.bat first!
    pause
    exit /B 1
)

call ".venv\Scripts\activate.bat"

echo Starting Streamlit …
streamlit run main.py

rem keep the window open after Streamlit exits
pause
