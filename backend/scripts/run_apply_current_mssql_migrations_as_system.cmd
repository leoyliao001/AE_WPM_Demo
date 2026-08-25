@echo off
setlocal
cd /d E:\AE_WPM_Demo\backend
set DJANGO_DB_ENGINE=mssql
set PYTHONUTF8=1
E:\wpm_env\Scripts\python.exe scripts\apply_current_mssql_migrations.py > scripts\mssql_apply_current_migrations_log.txt 2>&1
exit /b %ERRORLEVEL%