import zipfile, os
os.chdir(r'i:\landlock-system\landlock\backend\data\tmp')
z = zipfile.ZipFile('mwi_admin.geojson.zip')
print(z.namelist())
z.extractall('admin')
print('extracted to', os.path.abspath('admin'))
