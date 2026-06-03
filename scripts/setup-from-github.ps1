# First-time setup after git clone (another PC). Does not start Docker.
param(
    [switch]$Start
)

Set-Location (Split-Path $PSScriptRoot -Parent)
$ErrorActionPreference = "Stop"

Write-Host "E-Commerce — setup from GitHub" -ForegroundColor Cyan

if (-not (Test-Path "Backend\.env")) {
    Copy-Item "Backend\.env.example" "Backend\.env"
    Write-Host "Created Backend\.env from example — edit TELEGRAM_*, DB password, JWT_SECRET_KEY" -ForegroundColor Yellow
} else {
    Write-Host "Backend\.env already exists — skipped" -ForegroundColor Green
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.deploy.example" ".env"
    Write-Host "Created root .env from .env.deploy.example" -ForegroundColor Yellow
}

$credDir = "Backend\credentials"
if (-not (Test-Path $credDir)) {
    New-Item -ItemType Directory -Path $credDir | Out-Null
}
$placeholder = Join-Path $credDir "google-service-account.json"
if (-not (Test-Path $placeholder)) {
    Write-Host "Optional: add Google JSON to Backend\credentials\google-service-account.json" -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Edit Backend\.env (same TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID as your other PC)"
Write-Host "  2. Install Docker Desktop; allow firewall TCP 80/443 for host nginx"
Write-Host "  3. Run: .\docker-update.ps1"
Write-Host "  4. Build frontend + configure host nginx — see host-nginx-examples\"

if ($Start) {
    & "$PSScriptRoot\..\docker-update.ps1"
}
