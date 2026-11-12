import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import app
from utils.security import create_access_token
from db.sqlite_db import db

client = app.test_client()

# Show the two superusers as the DB sees them
for uid in (8, 17):
    rows = db.select("users", eq={"id": uid})
    print(uid, [(k, rows[0].get(k)) for k in ("username", "role", "is_superuser", "is_active")] if rows else "NOT FOUND")

# Pick a pending plot owned by a citizen
plots = db.select("plots", eq={"status": "pending"})
print("pending plots:", [(p['id'], p.get('plot_type'), p.get('status')) for p in plots][:5])
if plots:
    pid = plots[0]['id']
    all = db.select('plots', order='id')
    print("all plots:", [(p['id'], p.get('plot_type'), p.get('status'), p.get('user_id')) for p in all])
    for uid in (8, 17):
        hdr = {"Authorization": "Bearer " + create_access_token({"sub": str(uid)})}
        r = client.post(f"/api/official/caseload/{pid}/approve", headers=hdr, json={"action": "approve"})
        print(f"user {uid} approve plot {pid}:", r.status_code, r.get_json())
