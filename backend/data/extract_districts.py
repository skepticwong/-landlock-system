import json

# Load the GeoJSON
with open('e:/landlock-system/landlock/backend/data/malawi_districts.geojson', 'r') as f:
    geojson = json.load(f)

# Districts we need (from geographic_areas.py)
needed_districts = {
    "lilongwe": "Lilongwe",
    "blantyre": "Blantyre",
    "mzuzu": "Mzimba",  # Mzuzu district might be called Mzimba
    "zomba": "Zomba",
    "kasungu": "Kasungu",
    "mangochi": "Mangochi",
    "salima": "Salima",
    "dedza": "Dedza",
    "ntcheu": "Ntcheu",
    "mwanza": "Mwanza"
}

# Extract polygon coordinates for each district
district_boundaries = {}

for feature in geojson['features']:
    shape_name = feature['properties']['shapeName']
    
    # Check if this is a district we need
    for district_id, district_name in needed_districts.items():
        if shape_name.lower() == district_name.lower():
            # Get the geometry coordinates
            geometry = feature['geometry']
            if geometry['type'] == 'Polygon':
                # GeoJSON coordinates are [longitude, latitude]
                # We need to keep them in this format for the frontend
                coordinates = geometry['coordinates'][0]
                district_boundaries[district_id] = coordinates
                print(f"Extracted {district_name}: {len(coordinates)} coordinates")
            elif geometry['type'] == 'MultiPolygon':
                # For multipolygons, select the largest polygon by area
                largest_polygon = None
                largest_size = 0
                for polygon in geometry['coordinates']:
                    coords = polygon[0]
                    if len(coords) > largest_size:
                        largest_size = len(coords)
                        largest_polygon = coords
                district_boundaries[district_id] = largest_polygon
                print(f"Extracted {district_name} (MultiPolygon, largest): {len(largest_polygon)} coordinates")
            break

# Write the Python code to a file
with open('e:/landlock-system/landlock/backend/data/district_boundaries.py', 'w') as f:
    f.write("# District boundary coordinates (actual polygons from GeoJSON)\n")
    f.write("MALAWI_DISTRICT_BOUNDARIES = {\n")
    for district_id, coords in district_boundaries.items():
        f.write(f'    "{district_id}": {coords},\n')
    f.write("}\n")

print("\nDistrict boundaries written to district_boundaries.py")
