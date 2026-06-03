# First-time setup after git clone on a new PC.
# Usage:
#   .\scripts\setup-from-github.ps1
#   .\scripts\setup-from-github.ps1 -Start    # also run docker-update.ps1
param(
    [switch]$Start
)

Set-Location (Split-Path $PSScriptRoot -Parent)
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  E-Commerce — new PC setup (from Git)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Repo: https://github.com/Kimheang-code-IT/e-commerce (branch: main)" -ForegroundColor DarkGray
Write-Host ""

# --- Env files ---
if (-not (Test-Path "Backend\.env")) {
    Copy-Item "Backend\.env.example" "Backend\.env"
    Write-Host "[+] Created Backend\.env from example" -ForegroundColor Yellow
    Write-Host "    REQUIRED: edit password, JWT_SECRET_KEY, TELEGRAM_* before Docker starts" -ForegroundColor Yellow
} else {
    Write-Host "[=] Backend\.env already exists" -ForegroundColor Green
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.deploy.example" ".env"
    Write-Host "[+] Created root .env from .env.deploy.example" -ForegroundColor Yellow
} else {
    Write-Host "[=] root .env already exists" -ForegroundColor Green
}

$credDir = "Backend\credentials"
if (-not (Test-Path $credDir)) {
    New-Item -ItemType Directory -Path $credDir | Out-Null
    Write-Host "[+] Created Backend\credentials\" -ForegroundColor Green
}
if (-not (Get-ChildItem "$credDir\*.json" -ErrorAction SilentlyContinue)) {
    Write-Host "[!] Optional: copy Google service account JSON to Backend\credentials\" -ForegroundColor DarkYellow
}

# --- Docker ---
$dockerOk = $false
try {
    $null = docker version 2>&1
    if ($LASTEXITCODE -eq 0) { $dockerOk = $true }
} catch { }

if ($dockerOk) {
    Write-Host "[+] Docker is available" -ForegroundColor Green
} else {
    Write-Host "[!] Docker not found — install Docker Desktop and restart this script" -ForegroundColor Red
}

# --- Env validate (only if user already filled secrets) ---
if (Test-Path "Backend\.env") {
    Write-Host ""
    Write-Host "Checking Backend\.env for Docker..." -ForegroundColor Cyan
    python Backend/scripts/check_env_docker.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Fix Backend\.env, or copy Backend\.env from your old PC, then run:" -ForegroundColor Yellow
        Write-Host "  python Backend/scripts/check_env_docker.py" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor Cyan
Write-Host "Next steps (see docs\DEPLOY-NEW-PC.md):" -ForegroundColor Cyan
Write-Host "  1. Edit Backend\.env (or copy from old computer)" -ForegroundColor White
Write-Host "  2. python Backend/scripts/check_env_docker.py" -ForegroundColor White
Write-Host "  3. .\docker-update.ps1" -ForegroundColor White
Write-Host "  4. cd Frontend; pnpm install; pnpm exec nuxi generate" -ForegroundColor White
Write-Host "  5. Configure host nginx — host-nginx-examples\" -ForegroundColor White
Write-Host "  6. .\scripts\verify-deploy.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Copy from old PC (if migrating):" -ForegroundColor DarkCyan
Write-Host "  - Backend\.env" -ForegroundColor White
Write-Host "  - Backend\credentials\*.json" -ForegroundColor White
Write-Host "  - Only ONE machine may run telegram-bot with the same bot token" -ForegroundColor DarkYellow
Write-Host ""

if ($Start) {
    if (-not $dockerOk) {
        Write-Host "Cannot -Start without Docker." -ForegroundColor Red
        exit 1
    }
    & "$PSScriptRoot\..\docker-update.ps1"
}
