"""
Calculate runoff using the Curve Number (CN) method
Rasterize the Land Use Map and calculate.
Vectorize the rasterized map and calculate.
"""

import geopandas as gpd
import pandas as pd
from rasterstats import zonal_stats
import numpy as np

lcsf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/lcsf.shp"
precipitation_raster_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/4-Runoff/Precipitation_SZ.tif"
cn_csv_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/4-Runoff/HSG_B_CN.csv"
runoff_raster_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/4-Runoff/Runoff_SZ.tif"
runoff_vector_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/4-Runoff/Runoff_SZ.shp"


lcsf_gdf = gpd.read_file(lcsf_path)
cn_df = pd.read_csv(cn_csv_path, delimiter=';')
print("Columns in lcsf_gdf:", lcsf_gdf.columns)
print("Columns in cn_df:", cn_df.columns)


target_crs = "EPSG:2056"
if lcsf_gdf.crs != target_crs:
    lcsf_gdf = lcsf_gdf.to_crs(target_crs)

# Merge Art and CN values
lcsf_gdf = lcsf_gdf.merge(cn_df, how='left', on='Art')


# Calculate mean precipitation using zonal statistics
def calculate_runoff_vector(lcsf_gdf, precipitation_raster_path):
    # Calculate zonal statistics (mean precipitation value per polygon)
    zonal_mean = zonal_stats(lcsf_gdf, precipitation_raster_path, stats="mean", nodata= 7)
    
    # Add the mean precipitation to the GeoDataFrame
    lcsf_gdf['precipitation'] = [stat['mean'] for stat in zonal_mean]

    # Remap precipitation values based on predefined bands
    remap_values = {
        125: (6, 125),  # 100-125 mm -> 125 mm
        150: (7, 150),  # 125-150 mm -> 150 mm
        200: (8, 200),  # 150-200 mm -> 200 mm
        250: (9, 250)   # 200-250 mm -> 250 mm
    }
    
    # Normalize by dividing by 31 to get daily precipitation
    lcsf_gdf['precipitation'] /= 31.0

    # Calculate S_0.20, S_0.05, and runoff (Q)
    lcsf_gdf['S_020'] = 1000 / lcsf_gdf['CN_HSG_B'] - 10
    lcsf_gdf['S_005'] = 1.33 * lcsf_gdf['S_020'] ** 1.15
    lcsf_gdf['Q'] = np.where(
        lcsf_gdf['precipitation'] > 0.05 * lcsf_gdf['S_005'],
        ((lcsf_gdf['precipitation'] - 0.05 * lcsf_gdf['S_005']) ** 2) / (lcsf_gdf['precipitation'] + 0.95 * lcsf_gdf['S_005']),
        0
    )
    return lcsf_gdf

# Run the zonal statistics-based calculation and save the result
lcsf_gdf = calculate_runoff_vector(lcsf_gdf, precipitation_raster_path)
lcsf_gdf.to_file(runoff_vector_path)
print(f"Runoff vector map saved to {runoff_vector_path}.")