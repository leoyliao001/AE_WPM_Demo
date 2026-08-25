@echo off
setlocal
cd /d E:\AE_WPM_Demo\backend
set DJANGO_DB_ENGINE=mssql
set PYTHONUTF8=1
E:\wpm_env\Scripts\python.exe scripts\repair_and_migrate_mssql.py > scripts\mssql_current_migrate_log.txt 2>&1
exit /b %ERRORLEVEL%