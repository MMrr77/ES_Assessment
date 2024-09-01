"""
1. Aggregate predicted building information to the land use map.
2. Mark new buildings with column 'new_construct' = 1. add shade
3. Change land use type of surrounding areas of new buildings to 'Pavement', with the buffer distance of 20 meters.
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

###### lcsf map and buildings footprint shp
BDinlcsf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/9-Shade/BDinlcsf.shp"
predicted_buildings_path = '/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/rectangles_from_centroids.shp' 
sjmap_path = '/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/2_join_bds_to_LULC/sjoinedMap_shade.shp'

land_use_gdf = gpd.read_file(BDinlcsf_path)
predicted_buildings_gdf = gpd.read_file(predicted_buildings_path)

target_crs = "EPSG:2056"

if land_use_gdf.crs is None:
    land_use_gdf.set_crs(target_crs, inplace=True)
elif land_use_gdf.crs != target_crs:
    land_use_gdf = land_use_gdf.to_crs(target_crs)

if predicted_buildings_gdf.crs is None:
    predicted_buildings_gdf.set_crs(target_crs, inplace=True)
elif predicted_buildings_gdf.crs != target_crs:
    predicted_buildings_gdf = predicted_buildings_gdf.to_crs(target_crs)

predicted_buildings_gdf = predicted_buildings_gdf.sjoin(
    land_use_gdf[land_use_gdf['Art'] == 'Gebaeude'], 
    how='left', 
    predicate='intersects'
)

predicted_buildings_gdf['Art'] = 'Gebaeude'
predicted_buildings_gdf['new_construct'] = 1 
predicted_buildings_gdf['height'] = 9.0 

land_use_gdf = gpd.GeoDataFrame(pd.concat([land_use_gdf, predicted_buildings_gdf], ignore_index=True))


buffer_distance = 20
predicted_buildings_buffer = predicted_buildings_gdf.buffer(buffer_distance)

predicted_buildings_buffer = predicted_buildings_buffer.set_crs(target_crs, inplace=False)

#Update surrounding areas' land use type to 'Pavement'
land_use_gdf.loc[
    land_use_gdf.intersects(predicted_buildings_buffer.unary_union) & 
    (land_use_gdf['Art'] == 'Acker_Wiese_Weide'), 'Art'
] = 'uebrige_befestigte'


land_use_gdf.to_file(sjmap_path)
