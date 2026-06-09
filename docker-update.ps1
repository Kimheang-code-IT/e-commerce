# Rebuild and restart the Docker stack.
# Usage:
#   .\docker-update.ps1
#   .\docker-update.ps1 -NoBuild
#   .\docker-update.ps1 -Logs
#   .\docker-update.ps1 -Prod
#   .\docker-update.ps1 -BackendReplicas 2
param(
    [switch]$NoBuild,
    [switch]$Logs,
    [switch]$Prod,
    [int]$BackendReplicas = 1
)

Set-Location $PSScriptRoot
$ErrorActionPreference = "Stop"

if (Test-Path ".env") {
    $projectFromFile = $null
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*COMPOSE_PROJECT_NAME=(.+)$') { $projectFromFile = $Matches[1].Trim() }
    }
    if ($projectFromFile) {
        if ($env:COMPOSE_PROJECT_NAME -and $env:COMPOSE_PROJECT_NAME -ne $projectFromFile) {
            Write-Host "Overriding stale COMPOSE_PROJECT_NAME=$($env:COMPOSE_PROJECT_NAME) -> $projectFromFile" -ForegroundColor Yellow
        }
        $env:COMPOSE_PROJECT_NAME = $projectFromFile
    }
}
if ($env:COMPOSE_PROJECT_NAME) {
    Write-Host "Docker volumes: $($env:COMPOSE_PROJECT_NAME)_pg_data" -ForegroundColor Green
}

Write-Host "Checking Backend/.env for Docker..." -ForegroundColor Cyan
python Backend/app/scripts/check_env_docker.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$services = @("backend", "celery-worker", "celery-beat", "telegram-bot")
$composeArgs = @("compose")
if ($Prod) {
    $composeArgs += @("-f", "docker-compose.yml", "-f", "docker-compose.prod.yml")
}

if (-not $NoBuild) {
    Write-Host "Building: $($services -join ', ')..." -ForegroundColor Cyan
    docker @composeArgs build @services
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "Starting stack..." -ForegroundColor Cyan
docker @composeArgs up -d --scale "backend=$BackendReplicas"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Container status:" -ForegroundColor Cyan
docker compose ps

Write-Host ""
Write-Host "API health: curl http://127.0.0.1:8000/health" -ForegroundColor Cyan
Write-Host "Server deploy: ./build-admin.sh  (git pull + website + admin)" -ForegroundColor Cyan
Write-Host "Local admin build: .\build-admin.ps1" -ForegroundColor Cyan

if ($Logs) {
    docker compose logs -f backend celery-worker
}
