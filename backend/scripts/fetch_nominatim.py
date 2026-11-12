import json, urllib.request, urllib.parse, time

areas = [
    "Area 25", "Area 49", "Area 43", "Area 47", "Area 10", "Area 18",
    "Kawale", "Biwi", "Chilomoni", "Njewa", "Kanengo", "Tsabango",
    "Mtandire", "Chilinde", "Kachere", "Mgona", "Lumbadzi", "Kasinje",
]
headers = {'User-Agent': 'LandLock-dev/1.0 (local testing)'}
results = {}
for name in areas:
    q = urllib.parse.urlencode({
        'q': f'{name}, Lilongwe, Malawi',
        'polygon_geojson': '1',
        'format': 'jsonv2',
        'limit': 1,
    })
    url = f'https://nominatim.openstreetmap.org/search?{q}'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        if data:
            hit = data[0]
            gj = hit.get('geojson')
            print(name, '->', hit.get('display_name', '')[:60], '| geom:', (gj or {}).get('type'), '| bounded:', hit.get('boundingbox'))
            results[name] = hit
        else:
            print(name, '-> NO RESULT')
    except Exception as e:
        print(name, 'ERROR', e)
    time.sleep(1.2)

with open('lilongwe_nominatim.json', 'w', encoding='utf-8') as f:
    json.dump(results, f)
print('saved', len(results), 'hits')
