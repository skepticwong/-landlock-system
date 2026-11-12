import sqlite3, os
os.chdir(os.path.join(os.path.dirname(__file__), '..'))
c = sqlite3.connect('landlock.db')
for r in c.execute("select id, username, role, is_superuser, is_active from users"):
    print(r)
