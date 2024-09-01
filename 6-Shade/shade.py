import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon, LineString
from shapely.affinity import translate
from datetime import datetime

target_crs = "EPSG:2056"

BDinlcsf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/9-Shade/BDinlcsf.shp"
shadow_output_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/9-Shade/shadow.shp"


def calculate_sun_position(latitude, longitude, date_time):
    """
    Simplified calculation of sun position (altitude and azimuth).
    For precise calculations, consider using libraries like `pvlib` or `astropy`.
    """
    
    sun_altitude = 67  
    sun_azimuth = 180  
    return sun_altitude, sun_azimuth

def calculate_shadow(building_footprint, height, sun_altitude, sun_azimuth):
    """
    Calculate shadow polygon for a given building footprint.
    """
    shadow_length = height / np.tan(np.radians(sun_altitude))
    
    # Calculate shadow direction vector based on sun azimuth
    dx = shadow_length * np.sin(np.radians(sun_azimuth))
    dy = shadow_length * np.cos(np.radians(sun_azimuth))
    
    # Create shadow polygon by translating the building footprint
    shadow = translate(building_footprint, xoff=dx, yoff=dy)
    shadow_polygon = Polygon(list(building_footprint.exterior.coords) + list(shadow.exterior.coords))
    
    return shadow_polygon


lcsf = gpd.read_file(BDinlcsf_path)
if lcsf.crs != target_crs:
    lcsf = lcsf.to_crs(target_crs)


latitude = 47.0207
longitude = 8.6528
tz = 'Europe/Zurich'

# Summer time
date_time = datetime(2024, 7, 21, 12, 0, 0)


# Sun position
sun_altitude, sun_azimuth = calculate_sun_position(latitude, longitude, date_time)

# Filter the land use data to include only buildings

buildings = lcsf[lcsf['height'] > 0]

# Initialize a list to store shadow polygons
shadows = []

# Calculate shadow polygons for each building
for idx, building in buildings.iterrows():
    building_footprint = building.geometry
    height = building['height']
    
    # Calculate the shadow for the building
    shadow_polygon = calculate_shadow(building_footprint, height, sun_altitude, sun_azimuth)
    shadows.append(shadow_polygon)

# Create a GeoDataFrame for shadows
shadow_gdf = gpd.GeoDataFrame(geometry=shadows, crs=lcsf.crs)

# Save the shadow polygons to a new shapefile
shadow_gdf.to_file(shadow_output_path)
