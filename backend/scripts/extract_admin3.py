import zipfile, json, os
dst = r'i:\landlock-system\landlock\backend\data\tmp'
z = zipfile.ZipFile(os.path.join(dst, 'mwi_admin_full.zip'))
z.extract('mwi_admin3.geojson', dst)
gj = json.load(open(os.path.join(dst, 'mwi_admin3.geojson'), encoding='utf-8'))
feats = gj['features']
print(len(feats), 'features')
props = feats[0]['properties']
print(list(props.keys()))
for f in feats[:15]:
    p = f['properties']
    print(p)
