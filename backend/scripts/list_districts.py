import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from data.geographic_areas import MALAWI_DISTRICT_BOUNDARIES, get_all_districts
print('boundaries:', len(MALAWI_DISTRICT_BOUNDARIES))
print(sorted(MALAWI_DISTRICT_BOUNDARIES.keys()))
print('app districts:', [d['id'] for d in get_all_districts()])
missing = [d['id'] for d in get_all_districts() if d['id'] not in MALAWI_DISTRICT_BOUNDARIES]
print('app districts missing a boundary:', missing)

import data.geographic_areas as g
ds = g.get_all_districts()
print(len(ds), 'districts total')
print('nkhata-bay first 2 coords:', g.get_district_boundaries()['nkhata-bay'][:2])
print('ntchisi TAs:', g.get_traditional_authorities('ntchisi'))
print('neno area lookup:', g.get_area_name('district', 'neno'))
