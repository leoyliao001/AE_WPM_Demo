@echo off
setlocal
cd /d E:\AE_WPM_Demo\backend
set DJANGO_DB_ENGINE=mssql
set DJANGO_DB_DRIVER=ODBC Driver 17 for SQL Server
set DJANGO_DB_EXTRA_PARAMS=Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;
set PYTHONUTF8=1
E:\wpm_env\Scripts\python.exe scripts\sync_stakeholder_registration_to_mssql.py > scripts\mssql_stakeholder_registration_sync_log.txt 2>&1
exit /b %ERRORLEVEL%