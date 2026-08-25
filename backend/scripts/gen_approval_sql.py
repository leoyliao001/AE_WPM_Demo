import openpyxl

wb = openpyxl.load_workbook('E:/AE_WPM_Demo/InputforApproval.xlsx', read_only=True, data_only=True)
ws = wb['Sheet1']
rows = list(ws.iter_rows(values_only=True))

def q(v):
    return str(v or '').replace("'", "''")

lines = []
lines.append('-- ===== Run in SSMS on SCRBAEXDEFRM218 / [WPM Project] =====')
lines.append('')
lines.append('-- 1. Create approval_input table')
lines.append('CREATE TABLE [approval_input] (')
lines.append("  [id]                BIGINT IDENTITY(1,1) PRIMARY KEY,")
lines.append("  [activity_function] NVARCHAR(128) NOT NULL DEFAULT '',")
lines.append("  [product]           NVARCHAR(128) NOT NULL DEFAULT '',")
lines.append("  [area_head]         NVARCHAR(255) NOT NULL DEFAULT '',")
lines.append("  [pmo]               NVARCHAR(255) NOT NULL DEFAULT '',")
lines.append("  [bpm]               NVARCHAR(255) NOT NULL DEFAULT '',")
lines.append("  [fbp]               NVARCHAR(255) NOT NULL DEFAULT '',")
lines.append("  [wpm]               NVARCHAR(255) NOT NULL DEFAULT '',")
lines.append("  [elt]               NVARCHAR(255) NOT NULL DEFAULT '',")
lines.append("  [gsc_head]          NVARCHAR(255) NOT NULL DEFAULT '',")
lines.append("  [created_at]        DATETIME2 NOT NULL,")
lines.append("  [updated_at]        DATETIME2 NOT NULL")
lines.append(');')
lines.append('GO')
lines.append('CREATE INDEX [approval_in_act_fun_idx] ON [approval_input] ([activity_function],[product]);')
lines.append('GO')
lines.append('')
lines.append('-- 2. Seed data')

val_rows = []
for row in rows[1:]:
    if not row[0]:
        continue
    val_rows.append(
        "  ('" + q(row[0]) + "','" + q(row[1]) + "','" + q(row[2]) + "','" +
        q(row[3]) + "','" + q(row[4]) + "','" + q(row[5]) + "','" +
        q(row[6]) + "','" + q(row[7]) + "','" + q(row[8]) + "',GETUTCDATE(),GETUTCDATE())"
    )

lines.append('INSERT INTO [approval_input]')
lines.append('  ([activity_function],[product],[area_head],[pmo],[bpm],[fbp],[wpm],[elt],[gsc_head],[created_at],[updated_at])')
lines.append('VALUES')
lines.append(',\n'.join(val_rows) + ';')
lines.append('GO')
lines.append('')
lines.append('-- 3. Add input_for_approval column to access control table')
lines.append('ALTER TABLE [project_attributes_access] ADD [input_for_approval] BIT NOT NULL DEFAULT 0;')
lines.append('GO')
lines.append('')
lines.append('-- 4. Widen migration_manager (if not already done from migration 0026)')
lines.append('-- ALTER TABLE [product_ownership] ALTER COLUMN [migration_manager] NVARCHAR(255) NOT NULL;')
lines.append('-- GO')
lines.append('')
lines.append('-- 5. Mark all pending migrations as applied')
lines.append("INSERT INTO [django_migrations] ([app],[name],[applied]) VALUES")
lines.append("  ('api','0026_product_ownership_email',GETUTCDATE()),")
lines.append("  ('api','0027_approval_input',GETUTCDATE()),")
lines.append("  ('api','0028_project_attributes_access_input_for_approval',GETUTCDATE());")
lines.append('GO')

out = 'E:/AE_WPM_Demo/backend/scripts/apply_approval_input.sql'
with open(out, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('Written', len(val_rows), 'rows to', out)
