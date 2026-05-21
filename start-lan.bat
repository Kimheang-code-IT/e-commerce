@echo off
cd /d "%~dp0"
python scripts\deploy_lan.py %*
exit /b %ERRORLEVEL%
