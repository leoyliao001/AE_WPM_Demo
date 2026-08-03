"""Generate MSSQL DDL for all Django tables without a live DB connection.

Usage:
    python scripts/gen_mssql_ddl.py
    (writes scripts/create_tables_mssql.sql as UTF-8 with BOM)

The output can be executed by a DBA on the "WPM Project" database.
"""

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ["DJANGO_DB_ENGINE"] = "mssql"

import django  # noqa: E402

django.setup()

from django.apps import apps  # noqa: E402
from django.db import connection  # noqa: E402
from django.db.migrations.recorder import MigrationRecorder  # noqa: E402

APP_ORDER = ["contenttypes", "auth", "admin", "sessions", "api"]


def main() -> None:
    out = io.StringIO()
    with connection.schema_editor(collect_sql=True, atomic=False) as editor:
        # Django's own migration-tracking table.
        editor.create_model(MigrationRecorder.Migration)
        for app_label in APP_ORDER:
            # M2M through-tables are created automatically by create_model,
            # so exclude auto-created models to avoid duplicates.
            for model in apps.get_app_config(app_label).get_models():
                editor.create_model(model)
    for stmt in editor.collected_sql:
        out.write(stmt.rstrip(";") + ";\nGO\n")
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "create_tables_mssql.sql"
    )
    with open(out_path, "w", encoding="utf-8-sig", newline="\n") as fh:
        fh.write(out.getvalue())
    print(f"written: {out_path}")


if __name__ == "__main__":
    main()
