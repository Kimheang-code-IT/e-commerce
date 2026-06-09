# Build Frontend static admin (Windows)
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Frontend = Join-Path $Root "Frontend"

Set-Location $Frontend

$env:NUXT_PUBLIC_SITE_URL = "https://admin.anyamusicschool.com"
$env:NUXT_PUBLIC_API_BASE = "/api/v1"
$env:NUXT_PUBLIC_USE_BACKEND_API = "true"

pnpm install --frozen-lockfile
pnpm exec nuxi generate

Write-Host "Built admin at: $Frontend\.output\public"
Write-Host "Upload to server: /var/www/anyamusicschool-admin"
