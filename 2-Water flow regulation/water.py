"""
Calculate runoff using the Curve Number (CN) method
Rasterize the Land Use Map and calculate.
Vectorize the rasterized map and calculate.
"""

import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.features import rasterize
from shapely.geometry import mapping
import numpy as np
from rasterio.mask import mask

lcsf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/lcsf.shp"
precipitation_raster_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/4-Runoff/Precipitation_SZ.tif"
cn_csv_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/4-Runoff/HSG_B_CN.csv"
runoff_raster_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/4-Runoff/Runoff_SZ.tif"
runoff_vector_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/4-Runoff/Runoff_SZ.shp"



lcsf_gdf = gpd.read_file(lcsf_path)
cn_df = pd.read_csv(cn_csv_path)

# Merge Art and CN values
lcsf_gdf = lcsf_gdf.merge(cn_df, how='left', on='Art')

# Read the precipitation raster
with rasterio.open(precipitation_raster_path) as src:
    precipitation_data = src.read(1)
    precipitation_transform = src.transform
    precipitation_crs = src.crs
    precipitation_nodata = src.nodata
    precipitation_meta = src.meta

# Method 1: Extract Raster Values to Polygons and Calculate Runoff in Vector Format
def calculate_runoff_vector(lcsf_gdf, precipitation_data):
    # Extract precipitation values to each polygon
    lcsf_gdf['precipitation'] = None
    for index, row in lcsf_gdf.iterrows():
        # Mask precipitation raster with the polygon
        out_image, _ = mask(src, [row.geometry], crop=True, nodata=precipitation_nodata)
        mean_precipitation = out_image[out_image != precipitation_nodata].mean()
        lcsf_gdf.at[index, 'precipitation'] = mean_precipitation

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
lcsf_gdf = calculate_runoff_vector(lcsf_gdf, precipitation_data)
lcsf_gdf.to_file(runoff_vector_path)
print(f"Runoff vector map saved to {runoff_vector_path}.")

# Method 2: Convert Polygon Values into Raster and Calculate Runoff in Raster Format
# Rasterize the land use map with CN values
lcsf_raster = rasterize(
    [(mapping(geom), cn) for geom, cn in zip(lcsf_gdf.geometry, lcsf_gdf['CN_HSG_B'])],
    out_shape=precipitation_data.shape,
    transform=precipitation_transform,
    fill=precipitation_nodata,
    dtype='float32'
)

# Calculate S_0.20 and S_0.05 in raster format
S_020_raster = (1000 / lcsf_raster) - 10
S_005_raster = 1.33 * S_020_raster**1.15

# Calculate runoff (Q) in raster format
runoff_raster = np.where(
    precipitation_data > 0.05 * S_005_raster,
    ((precipitation_data - 0.05 * S_005_raster)**2) / (precipitation_data + 0.95 * S_005_raster),
    0
)

# Update metadata for the output runoff raster
runoff_meta = precipitation_meta.copy()
runoff_meta.update({
    'dtype': 'float32',
    'count': 1,
    'nodata': precipitation_nodata
})

# Save the runoff raster
with rasterio.open(runoff_raster_path, 'w', **runoff_meta) as dst:
    dst.write(runoff_raster.astype(np.float32), 1)

print(f"Runoff raster map saved to {runoff_raster_path}.")
