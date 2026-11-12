"""Seed chief_areas with all 433 official Traditional Authority / ward areas
from the National Statistics Office of Malawi (via HDX cod-ab-mwi, CC BY 3.0 IGO).

Each TA becomes an unassigned chief-area (area_type='ta') with its real
boundary polygon and parent district, ready for chief assignment.

Run:  python scripts/seed_ta_areas.py [--force]
  --force  deletes previously seeded TA rows (area_id like 'ta-%') first
"""
import json
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEO = os.path.join(HERE, '..', 'data', 'tmp', 'mwi_admin3.geojson')
DB = os.path.join(HERE, '..', 'landlock.db')
NOW = '2026-01-01T00:00:00'

# app district ids <-> HDX adm2_name
DISTRICT_MAP = {
    'lilongwe': 'Lilongwe', 'blantyre': 'Blantyre', 'mzuzu': 'Mzimba',
    'zomba': 'Zomba', 'kasungu': 'Kasungu', 'mangochi': 'Mangochi',
    'salima': 'Salima', 'dedza': 'Dedza', 'ntcheu': 'Ntcheu', 'mwanza': 'Mwanza',
    'balaka': 'Balaka', 'chikwawa': 'Chikwawa', 'chiradzulu': 'Chiradzulu',
    'chitipa': 'Chitipa', 'dowa': 'Dowa', 'karonga': 'Karonga', 'likoma': 'Likoma',
    'machinga': 'Machinga', 'mchinji': 'Mchinji', 'mulanje': 'Mulanje',
    'mzimba': 'Mzimba', 'neno': 'Neno', 'nkhata-bay': 'Nkhata Bay',
    'nkhotakota': 'Nkhotakota', 'nsanje': 'Nsanje', 'ntchisi': 'Ntchisi',
    'phalombe': 'Phalombe', 'rumphi': 'Rumphi', 'thyolo': 'Thyolo',
    # city assemblies are adm2 units in the NSO data but belong to their
    # surrounding district's app entry in this app
}
CITY_PARENT = {
    'Lilongwe City': 'lilongwe', 'Zomba City': 'zomba',
    'Blantyre City': 'blantyre', 'Mzuzu City': 'mzimba',
    'Nkhatabay': 'nkhata-bay',
}
NAME_TO_ID = {v.lower(): k for k, v in DISTRICT_MAP.items()}

def simplify_ring(ring, tolerance=0.002):
    """Douglas-Peucker-lite: drop points closer than tolerance degrees to the
    previous kept point. Good enough for district-scale display."""
    out = [ring[0]]
    for p in ring[1:]:
        dx = p[0] - out[-1][0]
        dy = p[1] - out[-1][1]
        if dx*dx + dy*dy > tolerance*tolerance:
            out.append(p)
    if len(out) > 2 and out[0] != out[-1]:
        out.append(out[0])  # re-close the ring
    return out

def largest_ring(geom):
    if geom['type'] == 'Polygon':
        parts = [geom['coordinates']]
    elif geom['type'] == 'MultiPolygon':
        parts = geom['coordinates']
    else:
        return None
    best = max(parts, key=lambda p: len(p[0]))
    return [[round(x, 6), round(y, 6)] for x, y in best[0]]

def main(force=False):
    gj = json.load(open(GEO, encoding='utf-8'))
    feats = gj['features']

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    if force:
        n = cur.execute("DELETE FROM chief_areas WHERE area_id LIKE 'ta-%'").rowcount
        print(f'deleted {n} previously seeded TA rows')

    inserted = skipped = 0
    unknown_districts = set()
    for f in feats:
        p = f['properties']
        name = p['adm3_name']
        dist_name = p['adm2_name'].lower()
        # city assemblies (Lilongwe City etc.) map onto the parent app district
        dist_id = NAME_TO_ID.get(dist_name) or CITY_PARENT.get(p['adm2_name'])
        if dist_id is None:
            unknown_districts.add(p['adm2_name'])
            continue
        # national parks/reserves and lakes are not chief areas
        if re.search(r'park|reserve|water|forest', name, re.I):
            skipped += 1
            continue
        ring = largest_ring(f['geometry'])
        if not ring or len(ring) < 4:
            skipped += 1
            continue
        ring = simplify_ring(ring)
        area_id = 'ta-' + p['adm3_pcode'].lower()
        exists = cur.execute("SELECT 1 FROM chief_areas WHERE area_id=?", (area_id,)).fetchone()
        if exists:
            skipped += 1
            continue
        cur.execute(
            """INSERT INTO chief_areas
               (chief_id, area_type, area_id, area_name, district_id, boundary, villages_json, created_at, updated_at)
               VALUES (NULL, 'ta', ?, ?, ?, ?, ?, ?, ?)""",
            (area_id, name, dist_id, json.dumps(ring), json.dumps([]), NOW, NOW))
        inserted += 1

    conn.commit()
    total = cur.execute("SELECT COUNT(*) FROM chief_areas").fetchone()[0]
    by_dist = cur.execute("SELECT district_id, COUNT(*) FROM chief_areas GROUP BY district_id ORDER BY 2 DESC").fetchall()
    conn.close()
    print(f'inserted {inserted}, skipped {skipped} (parks/unknown/tiny)')
    if unknown_districts:
        print('unknown parent districts:', unknown_districts)
    print('total chief_areas:', total)
    for d, n in by_dist:
        print(f'  {d}: {n}')

if __name__ == '__main__':
    main(force='--force' in sys.argv)
