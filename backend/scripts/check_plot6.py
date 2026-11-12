import sqlite3, os, json
os.chdir(os.path.join(os.path.dirname(__file__), '..'))
c = sqlite3.connect('landlock.db')
c.row_factory = sqlite3.Row
r = c.execute("select id, plot_name, plot_type, is_protected, status, user_id, approved_by from plots where id=6").fetchone()
print("before:", dict(r) if r else "plot 6 not found")
# State plots are pre-approved; reset the stale 'pending' status
n = c.execute("update plots set status='verified', approved_by=17, approved_at=datetime('now') where id=6 and status='pending'").rowcount
c.commit()
print("updated rows:", n)
