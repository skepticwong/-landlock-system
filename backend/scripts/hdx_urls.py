import json, urllib.request
req = urllib.request.Request('https://data.humdata.org/api/action/package_show?id=cod-ab-mwi',
                             headers={'User-Agent': 'LandLock-dev/1.0'})
with urllib.request.urlopen(req, timeout=30) as r:
    pkg = json.load(r)['result']
for res in pkg['resources']:
    print(res.get('name'), '::', res.get('download_url'))
