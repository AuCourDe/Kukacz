@echo off
setlocal enableextensions enabledelayedexpansion
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

if defined VIRTUAL_ENV (
    set PYTHON_BIN=%VIRTUAL_ENV%\Scripts\python.exe
) else (
    set PYTHON_BIN=python
)

"%PYTHON_BIN%" "%PROJECT_ROOT%\tests\run_e2e_test.py"
endlocal
