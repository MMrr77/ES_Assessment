"""
1. Aggregate predicted building information to the land use map.
2. Mark new buildings with column 'new_construct' = 1.
3. Change land use type of surrounding areas of new buildings to 'Pavement', with the buffer distance of 20 meters.
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

###### lcsf map and buildings footprint shp
land_use_map_path = '/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/lcsf.shp' 
predicted_buildings_path = '/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/bdft_pred.shp' 

land_use_gdf = gpd.read_file(land_use_map_path)
predicted_buildings_gdf = gpd.read_file(predicted_buildings_path)

# Update attributes for predicted buildings
predicted_buildings_gdf['Art'] = 'Gebaeude'
predicted_buildings_gdf['new_construct'] = 1  # Mark new constructions

# Create a 2.5m buffer (offset) around the new buildings
buffer_distance = 2.5
predicted_buildings_buffer = predicted_buildings_gdf.copy()  # Copy the building polygons
predicted_buildings_buffer['geometry'] = predicted_buildings_gdf.buffer(buffer_distance)  # Create buffer around buildings
predicted_buildings_buffer['Art'] = 'uebrige_befestigte'  # Assign 'uebrige_befestigte' to the buffer polygons
predicted_buildings_buffer['new_construct'] = None  # Buffers are not new constructions

# To ensure that buffers do not overlap with the buildings, subtract the building geometries from the buffers
predicted_buildings_buffer['geometry'] = predicted_buildings_buffer['geometry'].difference(predicted_buildings_gdf.unary_union)

# Combine the new buildings and buffer polygons
buildings_and_buffers_union = predicted_buildings_gdf.unary_union.union(predicted_buildings_buffer.unary_union)

# Remove the original areas in the land use map that intersect with the new buildings or their buffers
land_use_gdf = land_use_gdf[~land_use_gdf.intersects(buildings_and_buffers_union)]

# Add the new buildings to the land use map
land_use_gdf = gpd.GeoDataFrame(pd.concat([land_use_gdf, predicted_buildings_gdf], ignore_index=True))

# Add the buffer polygons (with 'uebrige_befestigte' as 'Art') to the land use map
land_use_gdf = gpd.GeoDataFrame(pd.concat([land_use_gdf, predicted_buildings_buffer], ignore_index=True))

# Save the updated land use map to a new shapefile
output_shapefile_path = '/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/2_join_bds_to_LULC/sjMap_1002_2035.shp'
land_use_gdf.to_file(output_shapefile_path)

# Print the first few rows to verify
print(land_use_gdf.head())