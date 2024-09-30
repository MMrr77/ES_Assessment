### This script calculates the FAR (floor area ratio), as the construction probability for each parcel in the conparcel.shp file

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon
from shapely import affinity
import numpy as np
import math

noBD_conparcels = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/noBD_conparcel_grun.shp"

conparcel_FAR = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/conparcel_FAR.shp"

conparcel_target = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/targetparcel.shp"

bdft_pred = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/bdft_pred.shp"


parcels = gpd.read_file(noBD_conparcels)

building_regulations = {
    '11.2.1': {'zone': 'W2L', 'VG': 2, 'use_rate': 0.35},
    '11.2.2': {'zone': 'W2D', 'VG': 2, 'use_rate': 0.45},
    '11.3.1': {'zone': 'W3', 'VG': 3, 'use_rate': 0.55},
    '11.4.1': {'zone': 'W4', 'VG': 4, 'use_rate': 0.70},
    '13.1.1': {'zone': 'WG2D', 'VG': 2, 'use_rate': 0.45},
    '13.2.1': {'zone': 'WG3', 'VG': 3, 'use_rate': 0.55},
    '13.3.1': {'zone': 'WG4', 'VG': 4, 'use_rate': 0.70},
    '14.1.2': {'zone': 'Z', 'VG': 4, 'use_rate': 0.85},
    '14.1.3': {'zone': 'Z', 'VG': 4, 'use_rate': 0.85},
}

default_VG = 3
default_use_rate = 0.7

#### FAR of unconstructed parcel
def calculate_far(row):
    land_type_code = row['typ_kommun']  

    regulation = building_regulations.get(land_type_code, {'VG': default_VG, 'use_rate': default_use_rate})
    VG = regulation['VG']
    use_rate = regulation['use_rate']
    
    building_footprint = row['BDFT_pred']  # Get building footprint from the row

    # Calculate maximum floor area
    max_floor_area = building_footprint * VG

    parcel_area = row['Flaeche']  # Get parcel area from the row
    # Calculate Floor Area Ratio (FAR)
    floor_area_ratio = max_floor_area / parcel_area
    
    # Store calculated values
    row['zone'] = regulation['zone']
    row['VG'] = VG
    row['use_rate'] = use_rate
    row['BDFT_pred'] = building_footprint
    row['max_floor_area'] = max_floor_area
    row['FAR'] = floor_area_ratio
    
    return row


parcels_with_far = parcels.apply(calculate_far, axis=1)

# Save the result to a new shapefile
parcels_with_far.to_file(conparcel_FAR)

print(f"Parcels with calculated FAR saved to {conparcel_FAR}")

#### sort parcels and select parcels until total area exceeds 842050 sqm
threshold_area = 842050
parcels_sorted = parcels_with_far.sort_values(by='FAR', ascending=False)

selected_parcels_list = []  
total_area = 0

for _, row in parcels_sorted.iterrows():
    selected_parcels_list.append(row) 
    total_area += row['Flaeche']
    if total_area >= threshold_area:
        break

selected_parcels = gpd.GeoDataFrame(selected_parcels_list, columns=parcels_with_far.columns, crs=parcels_with_far.crs)

print(f"Total area selected: {total_area} square meters.")

#### create rectangles from the centroids of selected parcels
def calculate_orientation(polygon):
    """Calculate orientation of the longest side of the minimum rotated rectangle."""
    min_rect = polygon.minimum_rotated_rectangle
    coords = list(min_rect.exterior.coords)
    
    ##### lengths of each side of the rectangle
    edges = [(coords[i], coords[i+1]) for i in range(len(coords) - 1)]
    lengths = [np.linalg.norm(np.array(edge[0]) - np.array(edge[1])) for edge in edges]
    
    ##### The longest side will define the orientation
    longest_edge = edges[np.argmax(lengths)]
    
    ##### Calculate angle of the longest edge
    delta_x = longest_edge[1][0] - longest_edge[0][0]
    delta_y = longest_edge[1][1] - longest_edge[0][1]
    angle = math.degrees(math.atan2(delta_y, delta_x))
    
    return angle

def create_oriented_rectangle(centroid, width, height, orientation_angle):
    rectangle = Polygon([
            (-width / 2, -height / 2),
            (width / 2, -height / 2),
            (width / 2, height / 2),
            (-width / 2, height / 2),
        ])
    
    ##### Orientation
    rotated_rectangle = affinity.rotate(rectangle, orientation_angle, origin=(0, 0), use_radians=False)

    translated_rectangle = affinity.translate(rotated_rectangle, xoff=centroid.x, yoff=centroid.y)
    
    return translated_rectangle

#### add to shapefile
rectangles_list = []

for _, row in selected_parcels.iterrows():
    centroid = row['geometry'].centroid

    ##### get VG and bdft
    building_footprint = row['BDFT_pred']
    VG = row['VG']

    side_length = np.sqrt(building_footprint)
    width = side_length
    height = side_length

    orientation_angle = calculate_orientation(row['geometry'])

    ##### create oriented rectangle
    rectangle = create_oriented_rectangle(centroid, width, height, orientation_angle)

    ##### add to gdf along with VG and bdft
    rectangles_list.append({
        'geometry': rectangle,
        'VG': VG,
        'bdft': building_footprint,
    })

rectangles_gdf = gpd.GeoDataFrame(rectangles_list, columns=['geometry', 'VG', 'building_footprint'], crs=parcels_with_far.crs)

selected_parcels.to_file(conparcel_target)
rectangles_gdf.to_file(bdft_pred)

print(f"Selected parcels saved to: {conparcel_target}")
print(f"Building rectangles saved to: {bdft_pred}")