@echo off
rem Applies pending api migrations to MSSQL "WPM Project".
rem Must run as SYSTEM (machine account) because SQL Server uses Trusted Connection.
cd /d E:\AE_WPM_Demo\backend
set DJANGO_DB_ENGINE=mssql
set DJANGO_DB_DRIVER=ODBC Driver 17 for SQL Server
set DJANGO_DB_EXTRA_PARAMS=Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;
set PYTHONUTF8=1
echo === identity === > scripts\mssql_migrate_api_log.txt
whoami >> scripts\mssql_migrate_api_log.txt 2>&1
echo === showmigrations === >> scripts\mssql_migrate_api_log.txt
E:\wpm_env\Scripts\python.exe manage.py showmigrations api >> scripts\mssql_migrate_api_log.txt 2>&1
echo === migrate === >> scripts\mssql_migrate_api_log.txt
E:\wpm_env\Scripts\python.exe manage.py migrate api >> scripts\mssql_migrate_api_log.txt 2>&1
echo === done === >> scripts\mssql_migrate_api_log.txt
