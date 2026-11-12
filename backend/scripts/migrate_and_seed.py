import sqlite3, os, sys
os.chdir(os.path.join(os.path.dirname(__file__), '..'))
c = sqlite3.connect('landlock.db')
cols = {r[1] for r in c.execute("PRAGMA table_info(chief_areas)")}
for col in ('area_type TEXT', 'area_id TEXT'):
    name = col.split()[0]
    if name not in cols:
        c.execute(f'ALTER TABLE chief_areas ADD COLUMN {col}')
        print('added column', name)
c.commit()
c.close()
import seed_village_areas  # noqa: E402
seed_village_areas.seed(force=False)
