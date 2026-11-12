# Smoke test: state-held plots protection
import json
import sys
sys.path.insert(0, '.')
sys.path.insert(0, '..')

from app import app

client = app.test_client()

# Fake JWT helper: sign tokens directly
from utils.security import create_access_token
from db.sqlite_db import db
from datetime import datetime

# Create test users: official + citizen
now = datetime.now().isoformat()
official = db.insert("users", {
    "username": "smoke_official", "email": "smoke_off@test.mw", "phone": "0999000001",
    "password_hash": "x", "full_name": "Test Official", "role": "official",
    "is_superuser": False, "is_active": True, "created_at": now, "updated_at": now
})
citizen = db.insert("users", {
    "username": "smoke_citizen", "email": "smoke_cit@test.mw", "phone": "0999000002",
    "password_hash": "x", "full_name": "Test Citizen", "role": "citizen",
    "is_superuser": False, "is_active": True, "created_at": now, "updated_at": now
})

official_tok = {"Authorization": "Bearer " + create_access_token({"sub": str(official["id"])})}
citizen_tok = {"Authorization": "Bearer " + create_access_token({"sub": str(citizen["id"])})}

pts = [{"lat": -13.9, "lng": 33.7}, {"lat": -13.91, "lng": 33.7}, {"lat": -13.91, "lng": 33.71}]

# 1) Official creates a government plot via /api/plots
r = client.post("/api/plots", headers=official_tok, json={
    "plot_name": "Gov Reserve", "points": pts, "plot_type": "government"})
plot = r.get_json()
print("1 official creates govt plot:", r.status_code, plot.get("plot_type"), "protected:", plot.get("is_protected"))
pid = plot["id"]

# 2) Citizen cannot create a state plot
r = client.post("/api/plots", headers=citizen_tok, json={
    "plot_name": "Hack", "points": pts, "plot_type": "military"})
print("2 citizen tries state plot:", r.status_code, r.get_json().get("error", "")[:60])

# 3) Citizen cannot edit the protected plot even if owner were them
r = client.put(f"/api/plots/{pid}", headers=citizen_tok, json={"plot_name": "Stolen"})
print("3 citizen edits protected plot:", r.status_code, r.get_json().get("error", "")[:60])

# 4) Even the official-owner cannot edit it via the normal endpoint
r = client.put(f"/api/plots/{pid}", headers=official_tok, json={"plot_name": "Renamed"})
print("4 official edits via normal route:", r.status_code, r.get_json().get("error", "")[:60])

# 5) Officials CAN edit via the state-plot endpoint
r = client.put(f"/api/official/state-plots/{pid}", headers=official_tok, json={"description": "Reserve A"})
print("5 official edits via state route:", r.status_code)

# 6) Cannot sell it (even by the owner)
r = client.post("/api/transactions/sale", headers=official_tok, json={
    "plot_id": pid, "buyer_phone": "0999000002", "witness_phone": "0999000001"})
print("6 sell protected plot:", r.status_code, r.get_json().get("error", "")[:60])

# 7) Cannot list it
r = client.post("/api/listings", headers=official_tok, json={"title": "T", "listing_type": "sale", "plot_id": pid})
print("7 list protected plot:", r.status_code, r.get_json().get("error", "")[:60])

# 8) Chief caseload approve is blocked for protected plots
r = client.post(f"/api/official/caseload/{pid}/approve", headers=official_tok, json={"action": "approve"})
print("8 caseload approve protected:", r.status_code, r.get_json().get("error", "")[:60])

# 9) Citizen private plot still works normally
r = client.post("/api/plots", headers=citizen_tok, json={"plot_name": "My Farm", "points": pts})
print("9 citizen private plot:", r.status_code, "type:", r.get_json().get("plot_type"), "protected:", r.get_json().get("is_protected"))
r = client.put(f"/api/plots/{r.get_json()['id']}", headers=citizen_tok, json={"plot_name": "My Farm 2"})
print("10 citizen edits own private plot:", r.status_code)

# 11) list state plots
r = client.get("/api/official/state-plots", headers=official_tok)
print("11 list state plots:", r.status_code, len(r.get_json()))

# Cleanup
for u in ("smoke_official", "smoke_citizen"):
    db.delete("users", eq={"username": u})
db.delete("plots", eq={"id": pid})
