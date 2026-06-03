# Verify nginx load balancing and production health (Phase 1).
# Usage: .\scripts\verify_lb.ps1 [-HttpPort 8081]
param(
    [int]$HttpPort = 0
)

Set-Location $PSScriptRoot\..
$ErrorActionPreference = "Continue"
$fail = 0

if ($HttpPort -eq 0 -and (Test-Path ".env")) {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*PUBLIC_HTTP_PORT=(\d+)') { $HttpPort = [int]$Matches[1] }
    }
}
if ($HttpPort -eq 0) { $HttpPort = 8081 }

Write-Host "=== Load balancer verification (port $HttpPort) ===" -ForegroundColor Cyan

Write-Host "`n[1] Backend replicas" -ForegroundColor Yellow
docker compose ps backend
$backendCount = (docker compose ps backend -q 2>$null | Measure-Object).Count
if ($backendCount -lt 2) {
    Write-Host "WARN: Expected 2+ backend containers. Set BACKEND_REPLICAS=2 and redeploy." -ForegroundColor Yellow
} else {
    Write-Host "OK: $backendCount backend container(s)" -ForegroundColor Green
}

Write-Host "`n[2] nginx DNS for backend" -ForegroundColor Yellow
docker compose exec -T nginx getent hosts backend 2>$null
if ($LASTEXITCODE -ne 0) { $fail++ }

Write-Host "`n[3] Health via nginx" -ForegroundColor Yellow
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$HttpPort/health" -UseBasicParsing -TimeoutSec 10
    Write-Host "Status: $($resp.StatusCode) Body: $($resp.Content.Substring(0, [Math]::Min(200, $resp.Content.Length)))"
    if ($resp.StatusCode -ne 200) { $fail++ }
} catch {
    Write-Host "FAIL: $($_.Exception.Message)" -ForegroundColor Red
    $fail++
}

Write-Host "`n[4] Singleton services" -ForegroundColor Yellow
docker compose ps telegram-bot celery-beat
$tg = (docker compose ps telegram-bot -q 2>$null | Measure-Object).Count
$beat = (docker compose ps celery-beat -q 2>$null | Measure-Object).Count
if ($tg -ne 1) {
    Write-Host "FAIL: telegram-bot must be exactly 1 instance" -ForegroundColor Red
    $fail++
}
if ($beat -ne 1) {
    Write-Host "FAIL: celery-beat must be exactly 1 instance" -ForegroundColor Red
    $fail++
}

if ($fail -eq 0) {
    Write-Host "`nAll automated checks passed. Manually test login + checkout in the browser." -ForegroundColor Green
    exit 0
}
Write-Host "`nSome checks failed ($fail). See docs/PRODUCTION.md" -ForegroundColor Red
exit 1
