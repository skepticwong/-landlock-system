import urllib.request, os, time
url = 'https://data.humdata.org/dataset/20eb8e5b-134d-41d8-a56f-4f358f7faf16/resource/375ffef0-933e-434e-9ef5-145f6ae2d9df/download/mwi_admin_boundaries.geojson.zip'
dst = r'i:\landlock-system\landlock\backend\data\tmp\mwi_admin_full.zip'
start = time.time()
req = urllib.request.Request(url, headers={'User-Agent': 'LandLock-dev/1.0'})
with urllib.request.urlopen(req, timeout=300) as r, open(dst, 'wb') as f:
    total = 0
    while True:
        chunk = r.read(1 << 20)
        if not chunk:
            break
        f.write(chunk)
        total += len(chunk)
        if total % (20 << 20) < (1 << 20):
            print(f'{total/1e6:.0f} MB...', flush=True)
print('done', total/1e6, 'MB in', round(time.time()-start), 's')
import zipfile
z = zipfile.ZipFile(dst)
print(z.namelist())
