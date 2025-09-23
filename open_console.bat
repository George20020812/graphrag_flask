@echo off
TITLE Graphrag API Console

REM Check if the virtual environment directory exists
IF NOT EXIST .\venv\Scripts\activate.bat (
    ECHO Virtual environment not found.
    ECHO Please run the following command first to create it:
    ECHO.
    ECHO   python -m venv venv
    ECHO.
    PAUSE
    EXIT /B
)

REM Check if api_server.py exists in the current directory
IF NOT EXIST api_server.py (
    ECHO Error: api_server.py not found in the current directory.
    ECHO Please ensure you are running this script from the project root directory (E:\graphrag\graphrag_api_project).
    PAUSE
    EXIT /B
)

ECHO Activating Python virtual environment...
CALL .\venv\Scripts\activate.bat

ECHO.
ECHO Environment is ready!
ECHO You can now run 'python api_server.py' to start the server in this window.
ECHO.

REM This keeps the command prompt open with the activated environment
cmd /k
