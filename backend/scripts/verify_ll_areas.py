import sqlite3, os, json
os.chdir(os.path.join(os.path.dirname(__file__), '..'))
c = sqlite3.connect('landlock.db')
c.row_factory = sqlite3.Row
rows = c.execute("SELECT area_name, area_id, chief_id, boundary FROM chief_areas ORDER BY area_name").fetchall()
poly, circ = 0, 0
for r in rows:
    b = json.loads(r['boundary'])
    n = len(b)
    kind = 'polygon' if n > 6 else 'circle~'
    if n > 6: poly += 1
    else: circ += 1
    print(f"{r['area_name']:12s} {kind:9s} pts={n:4d} chief={r['chief_id']}")
print(f'\ntotal={len(rows)} real-polygons={poly} approx-circles={circ}')
