"""Generate MSSQL INSERT statements from the local SQLite database.

Reads db.sqlite3 directly and emits T-SQL INSERTs for all api tables plus
django_migrations bookkeeping rows, so a DBA can load existing data into the
"WPM Project" database after running create_tables_mssql.sql.

Usage:
    python scripts/gen_mssql_data.py
    (writes scripts/insert_data_mssql.sql as UTF-8 with BOM)
"""

import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ.pop("DJANGO_DB_ENGINE", None)  # force sqlite settings

import django  # noqa: E402

django.setup()

from django.apps import apps  # noqa: E402
from django.db.models import BooleanField, DateTimeField, JSONField  # noqa: E402

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db.sqlite3")
BATCH = 200


def sql_literal(value, is_datetime=False, is_bool=False):
    if value is None:
        return "NULL"
    if is_bool:
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if is_datetime and "+" not in text and text and not text.endswith("Z"):
        text = f"{text} +00:00"  # Django stores UTC naive text in SQLite
    escaped = text.replace("'", "''")
    return f"N'{escaped}'"


def emit_table(cn, model, out):
    table = model._meta.db_table
    fields = [f for f in model._meta.concrete_fields]
    columns = [f.column for f in fields]
    meta = {
        f.column: (
            isinstance(f, DateTimeField),
            isinstance(f, BooleanField),
        )
        for f in fields
    }
    col_list = ", ".join(f"[{c}]" for c in columns)
    rows = cn.execute(
        f'SELECT {", ".join(columns)} FROM "{table}"'
    ).fetchall()
    if not rows:
        out.write(f"-- {table}: no rows\n")
        return
    out.write(f"-- {table}: {len(rows)} rows\n")
    out.write(f"SET IDENTITY_INSERT [{table}] ON;\n")
    for i in range(0, len(rows), BATCH):
        chunk = rows[i : i + BATCH]
        out.write(f"INSERT INTO [{table}] ({col_list}) VALUES\n")
        lines = []
        for row in chunk:
            vals = ", ".join(
                sql_literal(v, *meta[c]) for c, v in zip(columns, row)
            )
            lines.append(f"({vals})")
        out.write(",\n".join(lines))
        out.write(";\n")
    out.write(f"SET IDENTITY_INSERT [{table}] OFF;\nGO\n")


def emit_django_migrations(cn, out):
    rows = cn.execute("SELECT app, name, applied FROM django_migrations").fetchall()
    out.write(f"-- django_migrations: {len(rows)} rows\n")
    for app, name, applied in rows:
        out.write(
            "INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES "
            f"({sql_literal(app)}, {sql_literal(name)}, "
            f"{sql_literal(applied, is_datetime=True)});\n"
        )
    out.write("GO\n")


def main() -> None:
    cn = sqlite3.connect(DB_PATH)
    out_path = os.path.join(BASE_DIR, "scripts", "insert_data_mssql.sql")
    out = open(out_path, "w", encoding="utf-8-sig", newline="\n")
    out.write("-- Generated from db.sqlite3 -- run AFTER create_tables_mssql.sql\n")
    emit_django_migrations(cn, out)
    # FK dependency: project_gantt_plan references migration_intake_submission.
    models = sorted(
        apps.get_app_config("api").get_models(),
        key=lambda m: m._meta.db_table != "migration_intake_submission",
    )
    for model in models:
        emit_table(cn, model, out)
    out.close()
    cn.close()
    print(f"written: {out_path}")


if __name__ == "__main__":
    main()
