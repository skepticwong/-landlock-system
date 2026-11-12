import json, urllib.request, urllib.parse, time

# Lilongwe suburbs/neighbourhoods with full geometry
q = '''[out:json][timeout:90];
(
  way["place"~"^(suburb|neighbourhood|quarter)$"](33.55,-14.15,34.10,-13.80);
  relation["place"~"^(suburb|neighbourhood|quarter)$"](33.55,-14.15,34.10,-13.80);
);
out body;>;out skel qt;'''
mirrors = [
    'https://overpass.kumi.systems/api/interpreter',
    'https://overpass-api.de/api/interpreter',
]
qenc = urllib.parse.urlencode({'data': q}).encode()
out = None
for url in mirrors:
    try:
        req = urllib.request.Request(url, data=qenc, headers={'User-Agent': 'LandLock-dev/1.0'})
        with urllib.request.urlopen(req, timeout=120) as r:
            out = json.load(r)
        print(url, 'OK', len(out.get('elements', [])), 'elements')
        break
    except Exception as e:
        print(url, 'FAILED:', e)
        time.sleep(3)
if not out:
    raise SystemExit(1)

with open('lilongwe_osm_raw.json', 'w', encoding='utf-8') as f:
    json.dump(out, f)

# summarize named ways/relations
els = out['elements']
nodes = {e['id']: (e['lat'], e['lon']) for e in els if e['type'] == 'node'}
named = {}
for e in els:
    if e['type'] in ('way', 'relation') and 'place' in e.get('tags', {}):
        name = e['tags'].get('name')
        if name:
            n_members = len(e.get('nodes', [])) or len(e.get('members', []))
            named.setdefault(name, 0)
            named[name] += 1
print('named places:', named)
