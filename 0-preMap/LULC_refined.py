"""
Reclassify the LULC raster to 17 combination categories (CC) 
Intersect it with the Land Cover Statistics of Switzerland (LCSF) shapefile
"""
import geopandas as gpd
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape
import numpy as np
import pandas as pd
from shapely.geometry import Polygon
from shapely.ops import unary_union



lcsf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/lcsf.shp"
lulc_raster_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/3_reclassify_LULC_for_cal/LULC_raster/LULC_SZ.tif"

lcsf_gdf = gpd.read_file(lcsf_path)
with rasterio.open(lulc_raster_path) as src:
    raster_data = src.read(1)  # Read the first band
    raster_transform = src.transform
    raster_nodata = src.nodata
    raster_crs = src.crs 

print(f"LCSF CRS: {lcsf_gdf.crs}")
print(f"Raster CRS: {raster_crs}")

##### Aggregation values into 17 combination categories(CC)
###### CC12-Productive forest; CC13-Unproductive forest; CC21-Cropland; CC31-Permanent Grassland; CC32-Shrub Vegetation; CC33-Vineyard, low-stem orchard, tree nursery; CC34-Copse; CC35-Orchard; CC36-Stony grassland; CC37-Unproductive grassland; CC39-Vineyard, low-stem orchard, tree nursery; CC41-Surface water; CC42-Unproductive wetland; CC51-Buildings and constructions; CC52-Transport surfaces; CC53-Special Urban Areas; CC54-Recreational areas and cemeteries; CC61-Other land

cc_mapping = {
    1: 51, 2: 51, 3: 51, 4: 51, 5: 51, 6: 51, 7: 51, 8: 51, 9: 51, 10: 51,
    11: 51, 12: 51, 13: 51, 14: 51, 15: 52, 16: 52, 17: 52, 18: 52, 19: 52,
    20: 52, 21: 52, 22: 53, 23: 53, 24: 53, 25: 53, 26: 53, 27: 53, 28: 53,
    29: 53, 30: 53, 31: 54, 32: 54, 33: 54, 34: 54, 35: 54, 36: 54, 37: 35,
    38: 35, 39: 39, 40: 35, 41: 21, 42: 31, 43: 31, 44: 31, 45: 31, 46: 31,
    47: 31, 48: 31, 49: 31, 50: 12, 51: 12, 52: 12, 53: 13, 54: 13, 55: 13,
    56: 13, 57: 13, 58: 13, 59: 13, 60: 13, 61: 41, 62: 41, 63: 61, 64: 34,
    65: 61, 66: 61, 67: 42, 68: 61, 69: 61, 70: 61, 71: 61, 72: 61
}


##### Reclassify raster based on combination categories
reclassified_raster = np.copy(raster_data)
for original_value, cc_value in cc_mapping.items():
    reclassified_raster[raster_data == original_value] = cc_value



##### Convert the reclassified raster to vector polygons
cc_polygons = []
for value in np.unique(reclassified_raster):
    if value != raster_nodata:  # Ignore nodata values
        shapes_generator = shapes(reclassified_raster, mask=(reclassified_raster == value), transform=raster_transform)
        for geom, val in shapes_generator:
            if val:  # valid geometry
                cc_polygons.append({"geometry": shape(geom), "CC": value})

cc_gdf = gpd.GeoDataFrame(cc_polygons)

##### Smooth vector borders, reduce aliasing
cc_gdf['geometry'] = cc_gdf['geometry'].buffer(0.5).simplify(0.01)
cc_gdf['geometry'] = unary_union(cc_gdf['geometry'])

##### Exclude polygons with specific "Art" values from the intersection
excluded_art_values = ["Gebaeude", "uebrige_befestigte", "Fels", "Gartenanlage", "Bahn", "Trottoir", "Reben", "Strasse_Weg", "Verkehrsinsel", "Gewaesser_stehendes", "Wasserbecken"]
excluded_gdf = lcsf_gdf[lcsf_gdf["Art"].isin(excluded_art_values)]
included_gdf = lcsf_gdf[~lcsf_gdf["Art"].isin(excluded_art_values)]



##### Perform intersection between the included polygons and the CC polygons
intersection_gdf = included_gdf.intersection(cc_gdf.unary_union)
###### Convert the result into a GeoDataFrame with the original attributes
intersection_gdf = gpd.GeoDataFrame(included_gdf, geometry=intersection_gdf, crs=included_gdf.crs)


##### Combine the excluded polygons back with the intersected result
final_gdf = pd.concat([excluded_gdf, intersection_gdf], ignore_index=True)


final_gdf.to_file("/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/3_reclassify_LULC_for_cal/lcsf_sj_cc.shp")
print("Final shapefile saved as 'lcsf_sj_cc.shp'.")
