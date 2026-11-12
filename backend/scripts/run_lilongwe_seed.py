import sqlite3, os, sys, json
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
import seed_lilongwe_areas  # noqa: E402
with open(seed_lilongwe_areas.CACHE, encoding='utf-8') as f:
    results = json.load(f)
seed_lilongwe_areas.seed(results, force='--force' in sys.argv)
