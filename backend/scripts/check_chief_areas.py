import sqlite3, os
os.chdir(os.path.join(os.path.dirname(__file__), '..'))
c = sqlite3.connect('landlock.db')
cols = [r[1] for r in c.execute("PRAGMA table_info(chief_areas)")]
print('columns:', cols)
print('rows:', c.execute("SELECT COUNT(*) FROM chief_areas").fetchone()[0])
for r in c.execute("SELECT id, chief_id, area_type, area_id, area_name, district_id FROM chief_areas LIMIT 10"):
    print(r)
