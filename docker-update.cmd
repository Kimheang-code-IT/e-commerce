@echo off
REM Same as docker-update.ps1 — works when PowerShell blocks .ps1 scripts.
REM New code is built from this folder; old DB/uploads stay in Docker volumes (see COMPOSE_PROJECT_NAME in .env).
cd /d "%~dp0"
setlocal EnableExtensions

if exist .env for /f "usebackq tokens=1,* delims==" %%a in (".env") do if /i "%%a"=="COMPOSE_PROJECT_NAME" set "COMPOSE_PROJECT_NAME=%%b"
if not defined COMPOSE_PROJECT_NAME set "COMPOSE_PROJECT_NAME=e-commerce"
if defined COMPOSE_PROJECT_NAME (
  echo Keeping existing data volumes: %COMPOSE_PROJECT_NAME%_pg_data
) else (
  echo Tip: set COMPOSE_PROJECT_NAME=e-comerce in .env to reuse an older database volume.
)

echo Checking Backend/.env for Docker...
python Backend\scripts\check_env_docker.py
if errorlevel 1 exit /b 1

if /i "%~1"=="--no-build" goto start
if /i "%~1"=="-NoBuild" goto start

echo Building images: backend, celery-worker, celery-beat, telegram-bot, nginx...
docker compose build backend celery-worker celery-beat telegram-bot nginx
if errorlevel 1 exit /b 1

:start
echo Starting stack (detect LAN IP, port 8081)...
python scripts\deploy_lan.py --port 8081 %*
if errorlevel 1 exit /b 1

echo.
echo Container status:
docker compose ps
exit /b 0
