import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.mask import mask
import numpy as np
from shapely.geometry import mapping, box

# File paths
lcsf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/lcsf.shp"
temp_bp_csv = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/BPh_0430.csv"
et0_raster_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/ET0_SZ_use.tif"
t_air_ref_raster_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/Temp_072019_SZ.tif"
output_albedo_path = "Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/Albedo.tif"
output_kc_path = "Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/Kc.tif"
output_ETI_path = "Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/ETI.tif"
output_CC_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/CC.shp"
output_Temp_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/Temp.shp"
output_shapefile_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/lcsf_result.shp"

# 1. Load the land cover shapefile
lcsf_gdf = gpd.read_file(lcsf_path)
temp_biophysical_df = pd.read_csv(temp_bp_csv, delimiter=";")

# Set the CRS for all datasets
target_crs = "EPSG:2056"
lcsf_gdf = lcsf_gdf.to_crs(target_crs)

with rasterio.open(et0_raster_path) as et0_src:
    et0_meta = et0_src.meta
    et0_data = et0_src.read(1)
    et0_affine = et0_src.transform
    et0_bounds = et0_src.bounds
    print("ET0 Raster Metadata:")
    print(et0_meta)

with rasterio.open(t_air_ref_raster_path) as t_air_ref_src:
    t_air_ref_meta = t_air_ref_src.meta
    t_air_ref_data = t_air_ref_src.read(1)
    print("Temperature Raster Metadata:")
    print(t_air_ref_meta)

# 3. Merge biophysical data with shapefile according to "Art"
lcsf_gdf = lcsf_gdf.merge(temp_biophysical_df, on="Art")

# 4. Function to check overlap and extract ET0 values with mask from raster
def extract_raster_values(geometry, raster_path, affine, bounds):
    """Extract the mean raster value for the given geometry if it overlaps the raster bounds."""
    geom = [mapping(geometry)]
    if geometry.intersects(box(*bounds)):
        with rasterio.open(raster_path) as src:
            out_image, out_transform = mask(src, geom, crop=True)
            masked_data = np.ma.masked_array(out_image, out_image == src.nodata)
            return masked_data.mean()
    else:
        return np.nan

# Apply the function to extract ET0 values
lcsf_gdf['ET0_mean'] = lcsf_gdf.apply(lambda row: extract_raster_values(row.geometry, et0_raster_path, et0_affine, et0_bounds), axis=1)

# Debugging step: Check for NaN values or missing ET0_mean data
print("ET0_mean values:")
print(lcsf_gdf['ET0_mean'].describe())

# Calculate ETI
lcsf_gdf['ETI'] = (lcsf_gdf['Kc'] * lcsf_gdf['ET0_mean']) / et0_data.max()

# Debugging step: Check for NaN values or missing ETI data
print("ETI values:")
print(lcsf_gdf['ETI'].describe())

# Calculate Cooling Capacity (CC)
lcsf_gdf['CoolingCapacity'] = 0.6 * lcsf_gdf['Shade'] + 0.2 * lcsf_gdf['Albedo'] + 0.2 * lcsf_gdf['ETI']

# Debugging step: Check for NaN values or missing Cooling Capacity data
print("CoolingCapacity values:")
print(lcsf_gdf['CoolingCapacity'].describe())

# Calculate Temperature
UHI_max = 5  # Example maximum UHI magnitude
lcsf_gdf['Temperature'] = np.nanmean(t_air_ref_data) + (1 - lcsf_gdf['CoolingCapacity']) * UHI_max

# Debugging step: Check for NaN values or missing Temperature data
print("Temperature values:")
print(lcsf_gdf['Temperature'].describe())

# 8. Save the shapefile with Cooling Capacity
lcsf_gdf[['geometry', 'CoolingCapacity']].to_file(output_CC_path)
print(f"Cooling Capacity shapefile saved to: {output_CC_path}")

# 9. Save the shapefile with Temperature
lcsf_gdf[['geometry', 'Temperature']].to_file(output_Temp_path)
print(f"Temperature shapefile saved to: {output_Temp_path}")