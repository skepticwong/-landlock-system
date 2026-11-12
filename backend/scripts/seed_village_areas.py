"""Auto-generate demo village chief-areas for every district.

Divides each district polygon into grid cells; keeps cells whose centroid
falls inside the district polygon. Each cell becomes a chief_areas row of
type 'village' with an unassigned chief, ready to be assigned from the
official dashboard.

Run:  python scripts/seed_village_areas.py [--force]
--force deletes previously auto-generated demo areas (names starting with
the DEMO_PREFIX) before re-seeding.
"""
import json
import math
import os
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from data.geographic_areas import MALAWI_DISTRICT_BOUNDARIES, get_all_districts

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'landlock.db')
DEMO_PREFIX = 'Demo Area '
CELLS_PER_SIDE = 3  # 3x3 grid => up to ~9 areas per district

def point_in_ring(lng, lat, ring):
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

def seed(force=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if force:
        n = cur.execute("DELETE FROM chief_areas WHERE area_name LIKE ?", (DEMO_PREFIX + '%',)).rowcount
        print(f'deleted {n} previous demo areas')

    inserted = 0
    now = '2026-01-01T00:00:00'
    for district in get_all_districts():
        did = district['id']
        ring = MALAWI_DISTRICT_BOUNDARIES.get(did)
        if not ring:
            print(f'! no boundary for {did}, skipping')
            continue
        # skip if this district already has demo areas
        existing = cur.execute(
            "SELECT COUNT(*) FROM chief_areas WHERE district_id=? AND area_name LIKE ?",
            (did, DEMO_PREFIX + '%')).fetchone()[0]
        if existing:
            print(f'- {did}: {existing} demo areas already present, skipping')
            continue

        lons = [p[0] for p in ring]
        lats = [p[1] for p in ring]
        lon_min, lon_max = min(lons), max(lons)
        lat_min, lat_max = min(lats), max(lats)

        cell_w = (lon_max - lon_min) / CELLS_PER_SIDE
        cell_h = (lat_max - lat_min) / CELLS_PER_SIDE

        idx = 0
        for gy in range(CELLS_PER_SIDE):
            for gx in range(CELLS_PER_SIDE):
                x0, x1 = lon_min + gx * cell_w, lon_min + (gx + 1) * cell_w
                y0, y1 = lat_min + gy * cell_h, lat_min + (gy + 1) * cell_h
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                if not point_in_ring(cx, cy, ring):
                    continue
                idx += 1
                name = f'{DEMO_PREFIX}{idx} ({district["name"]})'
                cell = [[round(x0, 6), round(y0, 6)], [round(x1, 6), round(y0, 6)],
                        [round(x1, 6), round(y1, 6)], [round(x0, 6), round(y1, 6)]]
                cur.execute(
                    """INSERT INTO chief_areas
                       (chief_id, area_type, area_id, area_name, district_id, boundary, villages_json, created_at, updated_at)
                       VALUES (NULL, 'village', ?, ?, ?, ?, ?, ?, ?)""",
                    (f'{did}-demo-{idx}', name, did, json.dumps(cell), json.dumps([name]), now, now))
                inserted += 1
        print(f'+ {did}: {idx} demo areas')

    conn.commit()
    conn.close()
    print(f'done: {inserted} demo village areas inserted')

if __name__ == '__main__':
    seed(force='--force' in sys.argv)
