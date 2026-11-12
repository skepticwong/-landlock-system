import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import app
from utils.security import create_access_token
from db.sqlite_db import db

client = app.test_client()

# who's likely logged in on the frontend: user 17 is superuser
for uid in (17, 8):
    hdr = {"Authorization": "Bearer " + create_access_token({"sub": str(uid)}),
           "Content-Type": "application/json"}
    r = client.post("/api/official/caseload/6/approve", headers=hdr, data=json.dumps({"action": "approve"}))
    print(f"user {uid} approve plot 6:", r.status_code, r.get_json())
