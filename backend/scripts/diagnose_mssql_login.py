"""Diagnose SQL Server access using the legacy 'SQL Server' ODBC driver."""

import pyodbc

BASE = (
    "DRIVER={SQL Server};"
    "SERVER=SCRBAEXDEFRM218,1433;"
    "DATABASE=WPM Project;"
    "Trusted_Connection=yes;"
)

try:
    cn = pyodbc.connect(BASE, timeout=8)
except Exception as exc:  # noqa: BLE001
    print(f"LOGIN FAIL {type(exc).__name__}: {exc}")
    raise SystemExit(1) from exc

cur = cn.cursor()
cur.execute("SELECT @@SERVERNAME, DB_NAME(), SYSTEM_USER")
print("connected:", tuple(cur.fetchone()))

cur.execute(
    "SELECT dp.name FROM sys.database_role_members drm "
    "JOIN sys.database_principals dp ON dp.principal_id = drm.role_principal_id "
    "JOIN sys.database_principals mp ON mp.principal_id = drm.member_principal_id "
    "WHERE mp.name = SYSTEM_USER OR mp.sid = SUSER_SID()"
)
print("db_roles:", [r[0] for r in cur.fetchall()])

cur.execute("SELECT HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'CREATE TABLE')")
print("can_create_table:", cur.fetchone()[0])
cn.close()
