# One-click LAN Docker start (auto-detects IP). Run from project root.
Set-Location $PSScriptRoot
python scripts/deploy_lan.py @args
exit $LASTEXITCODE
