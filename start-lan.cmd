@echo off
REM Same as start-lan.ps1 — no PowerShell execution policy required.
cd /d "%~dp0"
python scripts\deploy_lan.py --port 8081 %*
exit /b %ERRORLEVEL%
