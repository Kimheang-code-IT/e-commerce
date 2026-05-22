@echo off
REM Copy Postgres + uploads from e-comerce_* volumes to e-commerce_* (new folder name).
REM Safe: creates backups\ before changing anything. Old volumes are NOT deleted.
setlocal EnableExtensions
cd /d "%~dp0\.."

if not exist backups mkdir backups

echo === Step 1: Backup running database (old volume e-comerce_pg_data) ===
docker exec ecom-postgres pg_dump -U ecom-admin -Fc ecommerce -f /tmp/ecommerce-migrate.dump
if errorlevel 1 (
  echo FAIL: Is the stack running? Start with: docker-update.cmd
  exit /b 1
)
docker cp ecom-postgres:/tmp/ecommerce-migrate.dump backups\ecommerce-migrate.dump
echo Saved: backups\ecommerce-migrate.dump

echo.
echo === Step 2: Stop containers (volumes kept) ===
docker compose -p e-comerce down
docker compose -p e-commerce down 2>nul

echo.
echo === Step 3: Prepare new Postgres volume (e-commerce_pg_data) ===
docker volume rm e-commerce_pg_data 2>nul
docker run -d --name ecom-pg-migrate ^
  -e POSTGRES_USER=ecom-admin ^
  -e POSTGRES_PASSWORD=admin12!@$ ^
  -e POSTGRES_DB=ecommerce ^
  -v e-commerce_pg_data:/var/lib/postgresql/data ^
  postgres:16-alpine
if errorlevel 1 exit /b 1

echo Waiting for new Postgres to initialize...
powershell -NoProfile -Command "$ok=$false; for ($i=0; $i -lt 40; $i++) { Start-Sleep -Seconds 2; docker exec ecom-pg-migrate pg_isready -U ecom-admin -d ecommerce 2>$null; if ($LASTEXITCODE -eq 0) { $ok=$true; break } }; if (-not $ok) { exit 1 }"
if errorlevel 1 (
  echo FAIL: new Postgres did not become ready
  exit /b 1
)

echo.
echo === Step 4: Restore backup into NEW volume ===
docker cp backups\ecommerce-migrate.dump ecom-pg-migrate:/tmp/ecommerce-migrate.dump
docker exec ecom-pg-migrate pg_restore -U ecom-admin -d ecommerce --clean --if-exists /tmp/ecommerce-migrate.dump
if errorlevel 1 (
  echo pg_restore reported warnings/errors; checking row counts...
)

echo.
echo === Step 5: Verify row counts on NEW database ===
docker exec ecom-pg-migrate psql -U ecom-admin -d ecommerce -c "SELECT 'invoices' AS t, COUNT(*) FROM invoices UNION ALL SELECT 'products', COUNT(*) FROM products UNION ALL SELECT 'users', COUNT(*) FROM users;"

docker stop ecom-pg-migrate
docker rm ecom-pg-migrate

echo.
echo === Step 6: Copy uploads volume (product images, PDFs) ===
docker volume create e-commerce_backend_uploads 2>nul
docker run --rm -v e-comerce_backend_uploads:/from -v e-commerce_backend_uploads:/to alpine sh -c "cp -a /from/. /to/ 2>/dev/null || true"

echo.
echo === Step 7: Switch project to NEW volumes in .env ===
powershell -NoProfile -Command ^
  "$p='.env'; $c=Get-Content $p -Raw; $c=$c -replace 'COMPOSE_PROJECT_NAME=e-comerce','COMPOSE_PROJECT_NAME=e-commerce'; if ($c -notmatch 'COMPOSE_PROJECT_NAME=') { $c='COMPOSE_PROJECT_NAME=e-commerce'+[Environment]::NewLine+$c }; Set-Content $p $c.TrimEnd() -Encoding utf8"

echo COMPOSE_PROJECT_NAME=e-commerce
echo.
echo === Done. Run docker-update.cmd to build new code and start. ===
exit /b 0
