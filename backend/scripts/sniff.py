b = open(r'i:\landlock-system\landlock\backend\data\tmp\mwi_admin.geojson.zip','rb').read(64)
print(b[:16])
print('hex:', b[:16].hex())
