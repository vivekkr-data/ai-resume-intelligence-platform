@echo off
setlocal
cd /d %~dp0
where python >nul 2>nul || (
  echo Python not found. Install Python 3.11 and select Add Python to PATH.
  pause
  exit /b 1
)
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
  echo Installation failed. Confirm that you are using 64-bit Python 3.11.
  pause
  exit /b 1
)
if not exist .env copy .env.example .env >nul
python -m compileall backend streamlit_app.py
pytest -q
if errorlevel 1 (
  echo Tests failed. Review the output above.
  pause
  exit /b 1
)
echo.
echo Setup and tests completed successfully.
echo Run run_streamlit.bat for the UI or run_api.bat for Swagger API.
pause
