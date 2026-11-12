"""Seed chief_areas with real Lilongwe city areas (Area 1-49 + named areas).

Boundaries come from Nominatim (OpenStreetMap) where a polygon exists;
for point-only hits a ~1 km circle is generated around the real location.
Results are cached to lilongwe_areas_cache.json so re-runs don't re-query.

Run:  python scripts/seed_lilongwe_areas.py [--force]
"""
import json
import math
import os
import sqlite3
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'lilongwe_areas_cache.json')
DB_PATH = os.path.join(HERE, '..', 'landlock.db')
HEADERS = {'User-Agent': 'LandLock-dev/1.0 (local testing)'}

AREA_NAMES = [f'Area {n}' for n in range(1, 50)] + [
    'Kawale', 'Biwi', 'Mtandire', 'Chilinde', 'Njewa', 'Kauma',
    'Chinsapo', 'Mchesi', 'Chilomoni', 'Ntandire', 'Area 25 Sector 2',
]

def nominatim(name, retries=3):
    q = urllib.parse.urlencode({
        'q': f'{name}, Lilongwe, Malawi',
        'polygon_geojson': '1',
        'format': 'jsonv2',
        'limit': 3,
    })
    url = f'https://nominatim.openstreetmap.org/search?{q}'
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:
            print(f'  retry {attempt+1} for {name}: {e}')
            time.sleep(3)
    return []

def largest_ring(geojson):
    """Return [[lng,lat],...] of the largest ring, closed ring removed."""
    if not geojson:
        return None
    if geojson['type'] == 'Polygon':
        rings = [geojson['coordinates'][0]]
    elif geojson['type'] == 'MultiPolygon':
        rings = [p[0] for p in geojson['coordinates']]
    else:
        return None
    best = max(rings, key=len)
    ring = [[round(x, 6), round(y, 6)] for x, y in best]
    if len(ring) > 3 and ring[0] == ring[-1]:
        ring = ring[:-1]
    return ring

def circle_around(lat, lon, radius_deg=0.009, n=24):
    ring = []
    for i in range(n):
        a = 2 * math.pi * i / n
        ring.append([round(lon + radius_deg * math.sin(a), 6),
                     round(lat + radius_deg * math.cos(a), 6)])
    return ring

def collect():
    """Query Nominatim for every area; cache results."""
    results = {}
    if os.path.exists(CACHE):
        with open(CACHE, encoding='utf-8') as f:
            results = json.load(f)
        print('resuming from cache:', len(results))
    for name in AREA_NAMES:
        if name in results:
            continue
        hits = nominatim(name)
        picked = None
        for hit in hits:
            dn = hit.get('display_name', '')
            if 'Lilongwe' not in dn:
                continue
            low = dn.lower()
            # skip roads, schools etc.: require the area name at the start
            if not low.startswith(name.lower()):
                continue
            picked = hit
            break
        if picked:
            ring = largest_ring(picked.get('geojson'))
            if ring:
                results[name] = {'ring': ring, 'source': 'osm-polygon',
                                 'display': picked['display_name']}
                print(f'{name}: polygon ({len(ring)} pts)')
            else:
                lat, lon = picked['lat'], picked['lon']
                results[name] = {'ring': circle_around(float(lat), float(lon)),
                                 'source': 'point-circle',
                                 'display': picked['display_name']}
                print(f'{name}: point -> circle at {lat},{lon}')
        else:
            print(f'{name}: NO MATCH')
        time.sleep(0.8)
        with open(CACHE, 'w', encoding='utf-8') as f:
            json.dump(results, f)
    return results

def seed(results, force=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if force:
        n = cur.execute("DELETE FROM chief_areas WHERE district_id='lilongwe' "
                        "AND area_name LIKE 'Area %' OR district_id='lilongwe' "
                        "AND area_name NOT LIKE 'Demo%' AND chief_id IS NULL").rowcount
        # safer: delete only rows we inserted (marked via area_id pattern)
        conn.rollback()
        n = cur.execute("DELETE FROM chief_areas WHERE area_id LIKE 'll-%'").rowcount
        print(f'deleted {n} previously seeded lilongwe rows')
    inserted = 0
    now = '2026-01-01T00:00:00'
    for name, info in results.items():
        area_id = 'll-' + name.lower().replace(' ', '-')
        exists = cur.execute("SELECT 1 FROM chief_areas WHERE area_id=?", (area_id,)).fetchone()
        if exists:
            print(f'- {name}: already seeded')
            continue
        cur.execute(
            """INSERT INTO chief_areas
               (chief_id, area_name, area_id, district_id, boundary, villages_json, created_at, updated_at)
               VALUES (NULL, ?, ?, 'lilongwe', ?, ?, ?, ?)""",
            (name, area_id, json.dumps(info['ring']), json.dumps([name]), now, now))
        inserted += 1
    conn.commit()
    total = cur.execute("SELECT COUNT(*) FROM chief_areas").fetchone()[0]
    conn.close()
    print(f'inserted {inserted}; chief_areas now has {total} rows')

if __name__ == '__main__':
    if os.path.exists(CACHE) and '--refresh' not in sys.argv:
        with open(CACHE, encoding='utf-8') as f:
            results = json.load(f)
        print('using cache:', len(results), 'areas')
    else:
        results = collect()
        print('collected:', sum(1 for v in results.values()), 'areas')
    seed(results, force='--force' in sys.argv)
