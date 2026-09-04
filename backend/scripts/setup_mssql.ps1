# One-shot: create tables in MSSQL "WPM Project" as the machine account,
# copy data from SQLite, switch the AE_WPM service to MSSQL, restart it.
#
# RUN FROM AN ELEVATED POWERSHELL:
#   powershell -ExecutionPolicy Bypass -File E:\AE_WPM_Demo\backend\scripts\setup_mssql.ps1

$ErrorActionPreference = "Stop"
$backend = "E:\AE_WPM_Demo\backend"
$log = Join-Path $backend "scripts\mssql_migrate_log.txt"

# --- elevation check ---
$elevated = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $elevated) { throw "Please run this script from an ELEVATED PowerShell (Run as administrator)." }

# --- 1. migrate + loaddata as SYSTEM via a temporary scheduled task ---
Write-Host "== 1/3 Running migrate + loaddata as SYSTEM ==" -ForegroundColor Cyan
if (Test-Path $log) { Remove-Item $log }
schtasks /Create /TN "AE_WPM_MssqlMigrate" /TR "$backend\scripts\run_migrate_as_system.cmd" /SC ONCE /ST 23:59 /RU SYSTEM /F | Out-Null
schtasks /Run /TN "AE_WPM_MssqlMigrate" | Out-Null
# wait for the task to finish (locale-independent, 10 min timeout)
$deadline = (Get-Date).AddMinutes(10)
do {
    Start-Sleep -Seconds 3
    $state = (Get-ScheduledTask -TaskName "AE_WPM_MssqlMigrate").State
} while ($state -eq "Running" -and (Get-Date) -lt $deadline)
schtasks /Delete /TN "AE_WPM_MssqlMigrate" /F | Out-Null

Get-Content $log
if (-not (Select-String -Path $log -Pattern "=== done ===" -Quiet)) {
    throw "Migration did not complete - see log above ($log)."
}

# --- 2. point the AE_WPM service at MSSQL ---
Write-Host "== 2/3 Adding DJANGO_DB_ENGINE=mssql to AE_WPM service env ==" -ForegroundColor Cyan
$nssm = "E:\Apps\services\wpm\nssm\nssm.exe"
# NOTE: values set explicitly (nssm's UTF-16 output cannot be read back reliably).
& $nssm set AE_WPM AppEnvironmentExtra `
    "DJANGO_DB_ENGINE=mssql" `
    "DJANGO_DEBUG=True" `
    "DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,SCRBAEXDEFRM217,SCRBAEXDEFRM217.crb.apmoller.net,wpmpulse.crb.apmoller.net,wpmworkflow.crb.apmoller.net,crb.apmoller.net,10.176.115.28,*" `
    "DJANGO_CORS_ORIGINS=http://localhost:3001,http://127.0.0.1:3001,http://localhost,http://127.0.0.1,http://10.176.115.28,http://SCRBAEXDEFRM217,https://localhost,https://127.0.0.1,https://10.176.115.28,https://SCRBAEXDEFRM217,https://SCRBAEXDEFRM217.crb.apmoller.net,https://wpmpulse.crb.apmoller.net,https://wpmworkflow.crb.apmoller.net,https://crb.apmoller.net"
if ($LASTEXITCODE -ne 0) { throw "nssm set AppEnvironmentExtra failed" }

# --- 3. restart service ---
Write-Host "== 3/3 Restarting AE_WPM ==" -ForegroundColor Cyan
Restart-Service AE_WPM -Force
Start-Sleep -Seconds 3
$resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health/" -UseBasicParsing -ErrorAction SilentlyContinue
Write-Host "Service restarted. Backend HTTP status: $($resp.StatusCode)" -ForegroundColor Green
Write-Host "Done - app now reads/writes MSSQL 'WPM Project' via CRB\SCRBAEXDEFRM217$." -ForegroundColor Green
