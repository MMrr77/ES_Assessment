import geopandas as gpd
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape
import numpy as np
import pandas as pd


lcsf_gdf = gpd.read_file("lcsf.shp")
lulc_raster_path = "lulc.tif"

with rasterio.open(lulc_raster_path) as src:
    raster_data = src.read(1)  # Read the first band
    raster_transform = src.transform
    raster_nodata = src.nodata


# Aggregation values into 17 combination categories(CC)
# CC12-Productive forest; CC13-Unproductive forest; CC21-Cropland; CC31-Permanent Grassland; CC32-Shrub Vegetation; CC33-Vineyard, low-stem orchard, tree nursery; CC34-Copse; CC35-Orchard; CC36-Stony grassland; CC37-Unproductive grassland; CC39-Vineyard, low-stem orchard, tree nursery; CC41-Surface water; CC42-Unproductive wetland; CC51-Buildings and constructions; CC52-Transport surfaces; CC53-Special Urban Areas; CC54-Recreational areas and cemeteries; CC61-Other land

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


# Reclassify raster based on combination categories
reclassified_raster = np.copy(raster_data)
for original_value, cc_value in cc_mapping.items():
    reclassified_raster[raster_data == original_value] = cc_value



# Convert the reclassified raster to vector polygons
cc_polygons = []
for value in np.unique(reclassified_raster):
    if value != raster_nodata:  # Ignore nodata values
        shapes_generator = shapes(reclassified_raster == value, transform=raster_transform)
        for geom, val in shapes_generator:
            cc_polygons.append({"geometry": shape(geom), "CC": value})

cc_gdf = gpd.GeoDataFrame(cc_polygons)

# Exclude polygons with specific "Art" values from the intersection
excluded_art_values = ["Gebaeude", "uebrige_befestigte", "Fels", "Gartenanlage", "Bahn", "Trottoir", "Reben", "Strasse_Weg", "Verkehrsinsel", "Gewaesser_stehendes", "Wasserbecken" ]
excluded_gdf = lcsf_gdf[lcsf_gdf["Art"].isin(excluded_art_values)]
included_gdf = lcsf_gdf[~lcsf_gdf["Art"].isin(excluded_art_values)]


# Perform intersection between the included polygons and the CC polygons
intersection_gdf = gpd.overlay(included_gdf, cc_gdf, how="intersection")

# Combine the excluded polygons back with the intersected result
final_gdf = pd.concat([excluded_gdf, intersection_gdf], ignore_index=True)


final_gdf.to_file("lcsf_with_cc_final.shp")
print("Final shapefile saved as 'lcsf_with_cc_final.shp'.")
