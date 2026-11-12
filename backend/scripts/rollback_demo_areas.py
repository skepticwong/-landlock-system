import sqlite3, os
os.chdir(os.path.join(os.path.dirname(__file__), '..'))
c = sqlite3.connect('landlock.db')
n = c.execute("DELETE FROM chief_areas WHERE area_name LIKE 'Demo Area %'").rowcount
c.commit()
remaining = c.execute("SELECT COUNT(*) FROM chief_areas").fetchone()[0]
c.close()
print(f'deleted {n} demo rows; {remaining} chief_areas rows remain')
