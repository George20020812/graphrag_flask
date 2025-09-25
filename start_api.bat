@echo off
REM Activate the virtual environment (path is relative from the parent dir)
call .venv\Scripts\activate.bat

REM Start the API server
echo "Starting API server..."
python api_server.py

REM Keep the window open to see the output
pause
