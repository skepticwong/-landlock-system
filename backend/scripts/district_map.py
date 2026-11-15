import sqlite3, os
os.chdir(os.path.join(os.path.dirname(__file__), '..'))
c = sqlite3.connect('landlock.db')
rows = c.execute("SELECT district_id, COUNT(*) FROM chief_areas GROUP BY district_id ORDER BY 2 DESC").fetchall()
total = 0
for d, n in rows:
    print(f'{d}: {n}')
    total += n
print('TOTAL:', total)
# sample of Lilongwe breakdown by prefix
print('\nLilongwe sample:')
for name, in c.execute("SELECT area_name FROM chief_areas WHERE district_id='lilongwe' LIMIT 12"):
    print(' ', name)
