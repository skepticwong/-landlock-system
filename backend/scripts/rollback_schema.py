import sqlite3, os
os.chdir(os.path.join(os.path.dirname(__file__), '..'))
c = sqlite3.connect('landlock.db')
version = c.execute("SELECT sqlite_version()").fetchone()[0]
print('sqlite', version)
for col in ('area_type', 'area_id'):
    try:
        c.execute(f'ALTER TABLE chief_areas DROP COLUMN {col}')
        print('dropped', col)
    except Exception as e:
        print('could not drop', col, '-', e)
c.commit()
cols = [r[1] for r in c.execute("PRAGMA table_info(chief_areas)")]
print('final columns:', cols)
c.close()
