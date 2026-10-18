@echo off
title JARVIS Assistant
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: Search for Python interpreter in order of preference
set "PYTHON_EXE="
if exist "%~dp0.venv\Scripts\python.exe" set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist "%~dp0venv\Scripts\python.exe" set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist "C:\Python313\python.exe" set "PYTHON_EXE=C:\Python313\python.exe"
if not defined PYTHON_EXE if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not defined PYTHON_EXE set "PYTHON_EXE=python.exe"

echo ============================================================
echo JARVIS Terminal Launcher
echo Python : %PYTHON_EXE%
echo WorkDir: %~dp0
echo ============================================================

"%PYTHON_EXE%" run_jarvis.py %*
if %ERRORLEVEL% neq 0 (
    echo.
    echo [JARVIS ERROR] Application exited with error code %ERRORLEVEL%.
    echo Check log file at: %~dp0data\startup_launcher.log
    pause
)
