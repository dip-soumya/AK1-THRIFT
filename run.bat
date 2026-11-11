@echo off
rem AK1-THRIFT launcher - double-click me
cd /d "%~dp0"
set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" main.py
if errorlevel 1 pause
