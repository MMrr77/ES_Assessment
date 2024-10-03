import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon, LineString
from shapely.affinity import translate
from datetime import datetime

target_crs = "EPSG:2056"

BDlcsf_pred_path = '/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/2_join_bds_to_LULC/sjMap_1002_2035.shp'
shadow_pred_output_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/Update1002/0-Data/9-Shade/shadow_pred.shp"


def calculate_sun_position(latitude, longitude, date_time):
    """
    Simplified calculation of sun position (altitude and azimuth).
    For precise calculations, consider using libraries like `pvlib` or `astropy`.
    """
    
    sun_altitude = 67  
    sun_azimuth = 180  
    return sun_altitude, sun_azimuth

def calculate_shadow_pred(building_footprint, height, sun_altitude, sun_azimuth):
    """
    Calculate shadow_pred polygon for a given building footprint.
    """
    shadow_pred_length = height / np.tan(np.radians(sun_altitude))
    
    # Calculate shadow_pred direction vector based on sun azimuth
    dx = shadow_pred_length * np.sin(np.radians(sun_azimuth))
    dy = shadow_pred_length * np.cos(np.radians(sun_azimuth))
    
    # Create shadow_pred polygon by translating the building footprint
    shadow_pred = translate(building_footprint, xoff=dx, yoff=dy)
    shadow_pred_polygon = Polygon(list(building_footprint.exterior.coords) + list(shadow_pred.exterior.coords))
    
    return shadow_pred_polygon


lcsf_pred = gpd.read_file(BDlcsf_pred_path)
if lcsf_pred.crs != target_crs:
    lcsf_pred = lcsf_pred.to_crs(target_crs)


latitude = 47.0207
longitude = 8.6528
tz = 'Europe/Zurich'

# Summer time
date_time = datetime(2024, 7, 21, 12, 0, 0)


# Sun position
sun_altitude, sun_azimuth = calculate_sun_position(latitude, longitude, date_time)

# Filter the land use data to include only buildings

buildings = lcsf_pred[lcsf_pred['height'] > 0]

# Initialize a list to store shadow_pred polygons
shadow_preds = []

# Calculate shadow_pred polygons for each building
for idx, building in buildings.iterrows():
    building_footprint = building.geometry
    height = building['height']
    
    # Calculate the shadow_pred for the building
    shadow_pred_polygon = calculate_shadow_pred(building_footprint, height, sun_altitude, sun_azimuth)
    shadow_preds.append(shadow_pred_polygon)

# Create a GeoDataFrame for shadow_preds
shadow_pred_gdf = gpd.GeoDataFrame(geometry=shadow_preds, crs=lcsf_pred.crs)

# Save the shadow_pred polygons to a new shapefile
shadow_pred_gdf.to_file(shadow_pred_output_path)
