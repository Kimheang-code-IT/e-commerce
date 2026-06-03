# Quick checks after clone + docker compose up (no nginx install).
Set-Location $PSScriptRoot\..
$ErrorActionPreference = "Continue"
$fail = 0

Write-Host "=== E-Commerce deploy verification ===" -ForegroundColor Cyan

if (-not (Test-Path "Backend\.env")) {
    Write-Host "FAIL: Backend\.env missing — run .\scripts\setup-from-github.ps1" -ForegroundColor Red
    exit 1
}

Write-Host "`n[1] Backend .env (Docker)" -ForegroundColor Yellow
python Backend/scripts/check_env_docker.py
if ($LASTEXITCODE -ne 0) { $fail++ }

Write-Host "`n[2] Docker containers" -ForegroundColor Yellow
docker compose ps
$backend = docker compose ps backend -q 2>$null
if (-not $backend) {
    Write-Host "FAIL: backend not running — run .\docker-update.ps1" -ForegroundColor Red
    $fail++
}

Write-Host "`n[3] API health (127.0.0.1:8000)" -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 10
    Write-Host "OK: $($r.StatusCode) $($r.Content.Substring(0, [Math]::Min(120, $r.Content.Length)))"
} catch {
    Write-Host "FAIL: $($_.Exception.Message)" -ForegroundColor Red
    $fail++
}

Write-Host "`n[4] Frontend build" -ForegroundColor Yellow
if (Test-Path "Frontend\.output\public\index.html") {
    Write-Host "OK: Frontend/.output/public exists (host nginx can serve it)" -ForegroundColor Green
} else {
    Write-Host "WARN: Run: cd Frontend; pnpm install; pnpm exec nuxi generate" -ForegroundColor Yellow
}

Write-Host "`n[5] Singleton services" -ForegroundColor Yellow
$tg = (docker compose ps telegram-bot -q 2>$null | Measure-Object).Count
if ($tg -gt 1) {
    Write-Host "FAIL: Only one telegram-bot allowed" -ForegroundColor Red
    $fail++
} elseif ($tg -eq 0) {
    Write-Host "WARN: telegram-bot not running" -ForegroundColor Yellow
} else {
    Write-Host "OK: one telegram-bot" -ForegroundColor Green
}

if ($fail -eq 0) {
    Write-Host "`nCore checks passed. Configure host nginx — see docs\DEPLOY-NEW-PC.md" -ForegroundColor Green
    exit 0
}
Write-Host "`n$fail check(s) failed. See docs\DEPLOY-NEW-PC.md" -ForegroundColor Red
exit 1
