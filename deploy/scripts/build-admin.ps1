# Build Frontend static admin locally (Windows) — copy .output/public to server manually
$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$Frontend = Join-Path $Root "Frontend"

Set-Location $Frontend

$env:NUXT_PUBLIC_SITE_URL = "https://admin.anyamusicschool.com"
$env:NUXT_PUBLIC_API_BASE = "/api/v1"
$env:NUXT_PUBLIC_USE_BACKEND_API = "true"

pnpm install --frozen-lockfile
pnpm exec nuxi generate

Write-Host "Built admin at: $Frontend\.output\public"
Write-Host "Upload that folder to the server: /var/www/anyamusicschool-admin"
