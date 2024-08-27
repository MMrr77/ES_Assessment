import geopandas as gpd
from shapely.geometry import Polygon

###### lcsf map and buildings footprint shp
land_use_map_path = '/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/lcsf.shp' 
predicted_buildings_path = '/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/rectangles_from_centroids.shp' 

land_use_gdf = gpd.read_file(land_use_map_path)
predicted_buildings_gdf = gpd.read_file(predicted_buildings_path)

###### Identify intersection
predicted_buildings_gdf = predicted_buildings_gdf.sjoin(land_use_gdf[land_use_gdf['Art'] == 'Gebaeude'], how='left', predicate='intersects')

###### Update attributes
predicted_buildings_gdf['Art'] = 'Gebaeude'
predicted_buildings_gdf['new_construct'] = 1 

###### Add to map
land_use_gdf = gpd.GeoDataFrame(pd.concat([land_use_gdf, predicted_buildings_gdf], ignore_index=True))

###### Buffer around the new buildings to identify the surrounding areas
###### Identify surrounding "Acker_Wiese_Weide" areas and update them to "Pavement"
buffer_distance = 20
predicted_buildings_buffer = predicted_buildings_gdf.buffer(buffer_distance)

# Update "Acker_Wiese_Weide" to "Pavement" where they intersect with the buffer
land_use_gdf.loc[land_use_gdf.intersects(predicted_buildings_buffer.unary_union) & 
                 (land_use_gdf['Art'] == 'Acker_Wiese_Weide'), 'Art'] = 'uebrige_befestigte'

# Step 6: Save the updated land use map to a new shapefile
output_shapefile_path = '/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/2_join_bds_to_LULC/sjoinedMap.shp'  # Replace with desired output path
land_use_gdf.to_file(output_shapefile_path)

# Print the first few rows to verify
print(land_use_gdf.head())
