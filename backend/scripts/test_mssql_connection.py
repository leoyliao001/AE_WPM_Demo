"""Quick connectivity check for SQL Server (Windows auth)."""

import pyodbc

CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=SCRBAEXDEFRM218,1433;"
    "DATABASE=WPM Project;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)


def main() -> None:
    print("Connecting to SCRBAEXDEFRM218 / WPM Project ...")
    try:
        cn = pyodbc.connect(CONN_STR, timeout=8)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL {type(exc).__name__}: {exc}")
        raise SystemExit(1) from exc

    cur = cn.cursor()
    cur.execute(
        "SELECT @@SERVERNAME AS server_name, DB_NAME() AS db_name, SYSTEM_USER AS login_user"
    )
    row = cur.fetchone()
    print(f"OK server={row.server_name} db={row.db_name} user={row.login_user}")

    cur.execute("SELECT name FROM sys.tables ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    print(f"tables_count={len(tables)}")
    print(f"tables_sample={tables[:30]}")
    cn.close()


if __name__ == "__main__":
    main()
