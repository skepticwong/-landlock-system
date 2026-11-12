"""Regenerate MALAWI_DISTRICT_BOUNDARIES from official geoBoundaries ADM2 GeoJSON.

Replaces the incomplete/stale hand-extracted polygons in
data/geographic_areas.py (and data/district_boundaries.py) with all 28
districts of Malawi, keyed by the district ids used by the app.

Source: geoBoundaries gbOpen MWI ADM2 (simplified), CC BY 3.0 IGO,
National Statistics Office of Malawi / OCHA ROSEA.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
GEOJSON = os.path.join(BACKEND, 'data', 'tmp', 'mwi_adm2.geojson')

with open(GEOJSON, encoding='utf-8') as f:
    gj = json.load(f)

shapes = {}
for feat in gj['features']:
    name = feat['properties']['shapeName'].strip().lower()
    shapes[name] = feat['geometry']

def ring_coords(geometry):
    """Return [lng, lat] ring of the largest polygon part."""
    if geometry['type'] == 'Polygon':
        polys = [geometry['coordinates']]
    elif geometry['type'] == 'MultiPolygon':
        polys = geometry['coordinates']
    else:
        raise ValueError(geometry['type'])
    # largest exterior ring by vertex count (approx. biggest area part)
    best = max(polys, key=lambda p: len(p[0]))
    ring = best[0]
    # drop the duplicated closing point
    if len(ring) > 1 and ring[0] == ring[-1]:
        ring = ring[:-1]
    return [[round(x, 6), round(y, 6)] for x, y in ring]

# map app district ids -> geoBoundaries shapeName
ALIAS = {
    'likoma': 'likoma',
    'nkhata bay': 'nkhata bay',
    'nkhatabay': 'nkhata bay',
    'nkhotakota': 'nkhotakota',
    'nkhata-bay': 'nkhata bay',
    'machinga': 'machinga',
    'neno': 'neno',
    'ntscheu': 'ntcheu',
    'ntchisi': 'ntchisi',
    'phalombe': 'phalombe',
    'chikwawa': 'chikwawa',
    'nsanje': 'nsanje',
    'balaka': 'balaka',
    'thyolo': 'thyolo',
    'mwanza': 'mwanza',
    'mwansa': 'mwanza',
    'rumphi': 'rumphi',
    'karonga': 'karonga',
    'chitipa': 'chitipa',
    'mulanje': 'mulanje',
    'chiradzulu': 'chiradzulu',
    'mchinji': 'mchinji',
    'dowa': 'dowa',
    'salima': 'salima',
    'dedza': 'dedza',
    'blantyre': 'blantyre',
    'zomba': 'zomba',
    'mangochi': 'mangochi',
    'lilongwe': 'lilongwe',
    'kasungu': 'kasungu',
    'mzimba': 'mzimba',
    'nkhatabay ': 'nkhata bay',
    'ntcheu': 'ntcheu',
    'mzuzu': 'mzimba city',  # handled specially below
}

def normalize(name: str) -> str:
    return re.sub(r'\s+', ' ', name.strip().lower())

lookup = {normalize(k): v for k, v in shapes.items()}
special = {'mzuzu'}

def resolve(app_id: str):
    key = normalize(app_id)
    if key in special:
        return None  # mzuzu is a city inside mzimba; skip
    for candidate in (key, key.replace('-', ' '), ALIAS.get(key, key)):
        if candidate in lookup:
            return lookup[candidate]
    if 'nkhata' in key:
        return lookup['nkhata bay']
    return None

# Read the app's canonical district id list from geographic_areas.py
geo_path = os.path.join(BACKEND, 'data', 'geographic_areas.py')
with open(geo_path, encoding='utf-8') as f:
    src = f.read()

ids = re.findall(r'\{"id"\s*:\s*"([^"]+)"\s*,\s*"name"', src)
known = ['lilongwe', 'blantyre', 'mzuzu', 'zomba', 'kasungu', 'mangochi',
         'salima', 'dedza', 'ntcheu', 'mwanza']

missing_resolved = []
boundaries = {}
for app_id in known:
    geom = resolve(app_id)
    if geom is None:
        # mzuzu city lies inside mzimba district - reuse mzimba's polygon
        if app_id == 'mzuzu':
            boundaries[app_id] = ring_coords(lookup['mzimba'])
            continue
        missing_resolved.append(app_id)
        continue
    boundaries[app_id] = ring_coords(geom)

# Also add every geojson district not yet covered, slugified as id
used_ids = set(boundaries)
new_district_entries = []
for name, geom in shapes.items():
    slug = normalize(name).replace(' ', '-')
    if slug in used_ids:
        continue
    boundaries[slug] = ring_coords(geom)
    used_ids.add(slug)
    display_name = name.title().replace("Of", "of")
    new_district_entries.append(
        {'id': slug, 'name': display_name}
    )

# Extend MALAWI_DISTRICTS with the newly added districts (no TA/village data
# yet - officials can add chiefs directly; TA lists can be filled in later).
new_districts_block = """
# Districts auto-added from geoBoundaries ADM2 (no TA/village data yet)
EXTRA_MALAWI_DISTRICTS = [
""" + "\n".join(
    '    {"id": "%s", "name": "%s", "traditional_authorities": []},' % (d['id'], d['name'])
    for d in new_district_entries
) + "\n]\n"

districts_list_re = re.compile(r'(MALAWI_DISTRICTS = \[.*?\n\]\n)', re.DOTALL)
m2 = districts_list_re.search(updated_src_placeholder if False else src)
if not m2:
    raise SystemExit('could not locate MALAWI_DISTRICTS list')
extra_src = src[:m2.end(1)] + new_districts_block + src[m2.end(1):]
# make get_all_districts etc. see both lists
extra_src = extra_src.replace(
    'def get_all_districts():\n    """Get all districts"""\n    return [{"id": d["id"], "name": d["name"]} for d in MALAWI_DISTRICTS]',
    'def _all_district_entries():\n    return MALAWI_DISTRICTS + EXTRA_MALAWI_DISTRICTS\n\n\ndef get_all_districts():\n    """Get all districts"""\n    return [{"id": d["id"], "name": d["name"]} for d in _all_district_entries()]'
)
for fn_name in ('get_traditional_authorities', 'get_villages', 'get_area_name'):
    pass
extra_src = extra_src.replace(
    'district = next((d for d in MALAWI_DISTRICTS if d["id"] == district_id), None)',
    'district = next((d for d in _all_district_entries() if d["id"] == district_id), None)'
)
extra_src = extra_src.replace(
    'for district in MALAWI_DISTRICTS:',
    'for district in _all_district_entries():'
)
src = extra_src

out_lines = ['# District boundary coordinates (actual polygons from GeoJSON)',
             '# Source: geoBoundaries gbOpen MWI ADM2 (simplified) - CC BY 3.0 IGO,',
             '# National Statistics Office of Malawi / OCHA ROSEA.',
             'MALAWI_DISTRICT_BOUNDARIES = {']
for key in sorted(boundaries):
    coords = json.dumps(boundaries[key], separators=(',', ':'))
    out_lines.append(f'    "{key}": {coords},')
out_lines.append('}')
body = '\n'.join(out_lines) + '\n'

new_block = '# District boundary coordinates (actual polygons from GeoJSON)\n' \
            + '# Source: geoBoundaries gbOpen MWI ADM2 (simplified) - CC BY 3.0 IGO\n' \
            + body.split('MALAWI_DISTRICT_BOUNDARIES = {', 1)[1].join(['MALAWI_DISTRICT_BOUNDARIES = {', ''])

pattern = re.compile(
    r'# District boundary coordinates.*?MALAWI_DISTRICT_BOUNDARIES = \{.*?\n\}',
    re.DOTALL)
m = pattern.search(src)
assert m, 'boundary block not found'
if not m:
    raise SystemExit('could not locate MALAWI_DISTRICT_BOUNDARIES block')
updated = src[:m.start()] + body + src[m.end():]
with open(geo_path, 'w', encoding='utf-8') as f:
    f.write(updated)
print('wrote', len(boundaries), 'districts to', geo_path)
print('unresolved:', missing_resolved)
