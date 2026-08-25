@echo off
setlocal
cd /d E:\AE_WPM_Demo\backend
set DJANGO_DB_ENGINE=mssql
set PYTHONUTF8=1
E:\wpm_env\Scripts\python.exe scripts\inspect_mssql_migration_state.py > scripts\mssql_migration_inspection_log.txt 2>&1
exit /b %ERRORLEVEL%