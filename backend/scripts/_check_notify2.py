import sqlite3

conn = sqlite3.connect("db.sqlite3")
conn.row_factory = sqlite3.Row

row = conn.execute(
    "select migration_request_id, requestor, region, areas "
    "from migration_intake_submission "
    "where migration_request_id = ?",
    ("WPM_PRJ_20260818831525",),
).fetchone()
print("SUBMISSION:", dict(row) if row else "NOT FOUND")

print("PRODUCT_OWNERSHIP ROWS:", conn.execute("select count(*) from product_ownership").fetchone()[0])
for r in conn.execute("select region, area, migration_manager from product_ownership limit 15"):
    print("  ", dict(r))
