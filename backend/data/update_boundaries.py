import re

# Read the district boundaries file
with open('e:/landlock-system/landlock/backend/data/district_boundaries.py', 'r') as f:
    boundaries_content = f.read()

# Extract the MALAWI_DISTRICT_BOUNDARIES dictionary
match = re.search(r'MALAWI_DISTRICT_BOUNDARIES = \{.*?\}', boundaries_content, re.DOTALL)
if match:
    boundaries_dict = match.group(0)
    
    # Read the geographic_areas.py file
    with open('e:/landlock-system/landlock/backend/data/geographic_areas.py', 'r') as f:
        geo_content = f.read()
    
    # Replace the old MALAWI_DISTRICT_BOUNDARIES with the new one
    updated_content = re.sub(
        r'# District boundary coordinates.*?MALAWI_DISTRICT_BOUNDARIES = \{.*?\}',
        f'# District boundary coordinates (actual polygons from GeoJSON)\n{boundaries_dict}',
        geo_content,
        flags=re.DOTALL
    )
    
    # Write the updated content back
    with open('e:/landlock-system/landlock/backend/data/geographic_areas.py', 'w') as f:
        f.write(updated_content)
    
    print("Successfully updated geographic_areas.py with real polygon coordinates")
else:
    print("Could not extract MALAWI_DISTRICT_BOUNDARIES from district_boundaries.py")
