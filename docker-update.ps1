# Rebuild and restart the full Docker stack (LAN deploy).
# Usage:
#   .\docker-update.ps1           # rebuild images + restart
#   .\docker-update.ps1 -NoBuild   # restart only
#   .\docker-update.ps1 -Logs      # follow logs after start
#   .\docker-update.ps1 -Beat      # include celery-beat (daily reports)
param(
    [switch]$NoBuild,
    [switch]$Logs,
    [switch]$Beat,
    [int]$BackendReplicas = 0
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
    Write-Host "Keeping existing data volumes: $($env:COMPOSE_PROJECT_NAME)_pg_data" -ForegroundColor Green
}

Write-Host "Checking Backend/.env for Docker..." -ForegroundColor Cyan
python Backend/scripts/check_env_docker.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$services = @("backend", "celery-worker", "celery-beat", "telegram-bot")

if (-not $NoBuild) {
    Write-Host "Building images: $($services -join ', ')..." -ForegroundColor Cyan
    docker compose build @services
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "Starting stack (detect LAN IP)..." -ForegroundColor Cyan
$lanArgs = @()
if ($Beat) {
    $lanArgs += "--beat"
}
if ($BackendReplicas -gt 0) {
    $lanArgs += "--backend-replicas", $BackendReplicas
}
python scripts/deploy_lan.py @lanArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Container status:" -ForegroundColor Cyan
docker compose ps

Write-Host ""
Write-Host "Quick checks:" -ForegroundColor Cyan
Write-Host "  docker compose logs celery-worker --tail 30"
Write-Host "  docker compose exec backend python -c ""import reportlab; print('reportlab OK')"""
Write-Host "  docker compose logs telegram-bot --tail 30"

if ($Logs) {
    docker compose logs -f backend celery-worker
}
