@echo off
REM Rebuild and restart Docker (no PowerShell execution policy required).
cd /d "%~dp0"
setlocal EnableExtensions

if exist .env for /f "usebackq tokens=1,* delims==" %%a in (".env") do if /i "%%a"=="COMPOSE_PROJECT_NAME" set "COMPOSE_PROJECT_NAME=%%b"

echo Checking Backend/.env for Docker...
python Backend\app\scripts\check_env_docker.py
if errorlevel 1 exit /b 1

if /i "%~1"=="--no-build" goto start
if /i "%~1"=="-NoBuild" goto start

echo Building images...
docker compose build backend celery-worker celery-beat telegram-bot
if errorlevel 1 exit /b 1

:start
echo Starting stack...
docker compose up -d %*
if errorlevel 1 exit /b 1

docker compose ps
echo API: http://127.0.0.1:8000/health
exit /b 0
