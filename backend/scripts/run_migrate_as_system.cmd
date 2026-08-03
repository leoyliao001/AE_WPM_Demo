@echo off
rem Runs Django migrate + data load against MSSQL "WPM Project".
rem Executed as SYSTEM (machine account CRB\SCRBAEXDEFRM217$) via scheduled task.
cd /d E:\AE_WPM_Demo\backend
set DJANGO_DB_ENGINE=mssql
set PYTHONUTF8=1
echo === identity === > scripts\mssql_migrate_log.txt
whoami >> scripts\mssql_migrate_log.txt 2>&1
echo === migrate === >> scripts\mssql_migrate_log.txt
E:\wpm_env\Scripts\python.exe manage.py migrate >> scripts\mssql_migrate_log.txt 2>&1
if errorlevel 1 goto :eof
echo === loaddata === >> scripts\mssql_migrate_log.txt
E:\wpm_env\Scripts\python.exe manage.py loaddata scripts\api_data_dump.json >> scripts\mssql_migrate_log.txt 2>&1
echo === done === >> scripts\mssql_migrate_log.txt
