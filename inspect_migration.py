import pandas as pd
from pathlib import Path
root = Path(r'E:\AE_WPM_Demo')
path = next(root.rglob('Migration Tracking (1).xlsx'))
print(f'FILE: {path}')
for sheet in ['BPM ROFO', 'BPM Actual']:
    print('\n' + '=' * 100)
    print(f'SHEET: {sheet}')
    df = pd.read_excel(path, sheet_name=sheet, header=0)
    print(f'SHAPE: {df.shape}')
    print('\nFULL COLUMN LIST WITH DTYPES (df.dtypes):')
    print(df.dtypes.to_string())
    print('\nUP TO 5 NON-NULL DISTINCT SAMPLE VALUES PER COLUMN:')
    for col in df.columns:
        print(f'\n[{col!r}]')
        vals = df[col].dropna().drop_duplicates().head(5).tolist()
        for i, value in enumerate(vals, 1): print(f'  {i}: {value!r}')
        if not vals: print('  <no non-null values>')
