import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'landlock.db')
conn = sqlite3.connect(DB_PATH)
ids = [8, 17]
for uid in ids:
    print(f"before {uid}:", conn.execute("select id, username, is_superuser from users where id=?", (uid,)).fetchall())
conn.executemany("update users set is_superuser=1 where id=?", [(i,) for i in ids])
conn.commit()
for uid in ids:
    print(f"after {uid}:", conn.execute("select id, username, is_superuser from users where id=?", (uid,)).fetchall())
