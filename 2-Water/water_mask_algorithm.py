"""
Calculate runoff using the Curve Number (CN) method
Rasterize the Land Use Map and calculate.
Vectorize the rasterized map and calculate.
"""

import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.mask import mask
import numpy as np

lcsf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/lcsf.shp"
precipitation_raster_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/4-Runoff/Precipitation_SZ.tif"
cn_csv_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/4-Runoff/HSG_B_CN.csv"
runoff_raster_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/4-Runoff/Runoff_SZ.tif"
runoff_vector_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/4-Runoff/Runoff_SZ_mask.shp"

target_crs = "EPSG:2056"

lcsf_gdf = gpd.read_file(lcsf_path)
cn_df = pd.read_csv(cn_csv_path, delimiter=';')

print("Columns in lcsf_gdf:", lcsf_gdf.columns)
print("Columns in cn_df:", cn_df.columns)


# Merge Art and CN values
lcsf_gdf = lcsf_gdf.merge(cn_df, how='left', on='Art')

# Extract Raster Values to Polygons and Calculate Runoff in Vector Format
def calculate_runoff_vector(lcsf_gdf, precipitation_raster_path):
    with rasterio.open(precipitation_raster_path) as src:
        precipitation_data = src.read(1)
        precipitation_nodata = src.nodata
        raster_crs = src.crs

        # Debug: Print the raster's unique values and check CRS
        unique_values = np.unique(precipitation_data)
        print(f"Unique values in raster: {unique_values}")
        print(f"Raster CRS: {raster_crs}, Vector CRS: {lcsf_gdf.crs}")
        
        # Check CRS of shapefile and raster
        if lcsf_gdf.crs != target_crs:
            lcsf_gdf = lcsf_gdf.to_crs(target_crs)

        # Initialize the precipitation column
        lcsf_gdf['precipitation'] = None
        
        # Remapping dictionary
        remap_values = {
            6: 125,  # Band 6 -> 100-125 mm, use 125 mm
            7: 150,  # Band 7 -> 125-150 mm, use 150 mm
            8: 200,  # Band 8 -> 150-200 mm, use 200 mm
            9: 250   # Band 9 -> 200-250 mm, use 250 mm
        }

        # Process each polygon and extract remapped precipitation values
        for index, row in lcsf_gdf.iterrows():
            try:
                # Mask the original raster with the polygon geometry
                out_image, out_transform = mask(src, [row.geometry], crop=True, nodata=precipitation_nodata)

                if np.any(out_image != precipitation_nodata):  # Ensure there are valid data points
                    # Remap the masked raster values
                    for original_value, new_value in remap_values.items():
                        out_image[out_image == original_value] = new_value
                    
                    # Normalize by dividing by 31 to get daily precipitation
                    out_image = out_image / 31.0

                    mean_precipitation = out_image[out_image != precipitation_nodata].mean()
                    lcsf_gdf.at[index, 'precipitation'] = mean_precipitation
                else:
                    lcsf_gdf.at[index, 'precipitation'] = 5.0  # nodata

            except ValueError as e:
                if "Input shapes do not overlap raster." in str(e):
                    print(f"Polygon at index {index} does not overlap with the raster. Skipping.")
                    lcsf_gdf.at[index, 'precipitation'] = 5.0  
                else:
                    raise e

    # Calculate S_0.20, S_0.05, and runoff (Q)
    lcsf_gdf['S_020'] = 1000 / lcsf_gdf['CN_HSG_B'] - 10
    lcsf_gdf['S_005'] = 1.33 * lcsf_gdf['S_020'] ** 1.15
    lcsf_gdf['Q'] = np.where(
        lcsf_gdf['precipitation'] > 0.05 * lcsf_gdf['S_005'],
        ((lcsf_gdf['precipitation'] - 0.05 * lcsf_gdf['S_005']) ** 2) / (lcsf_gdf['precipitation'] + 0.95 * lcsf_gdf['S_005']),
        0
    )
    return lcsf_gdf

# Run the vector-based calculation and save the result
lcsf_gdf = calculate_runoff_vector(lcsf_gdf, precipitation_raster_path)
lcsf_gdf.to_file(runoff_vector_path)
print(f"Runoff vector map saved to {runoff_vector_path}.")