import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.features import geometry_mask, geometry_window
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
import numpy as np
from rasterio.features import rasterize
from rasterstats import zonal_stats

# File paths
lcsf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/lcsf.shp"
temp_bp_csv = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/BPh_0430.csv"
et0_raster_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/ET0_SZ.tif"
t_air_ref_raster_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/TempMon_July2019_SZ.tif"
output_albedo_path = "Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/Albedo.tif"
output_kc_path = "Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/Kc.tif"
output_ETI_path = "Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/ETI.tif"
output_CC_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/CC.tif"
output_Temp_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/Temp.tif"
output_shapefile_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/lcsf_result.shp"

# 1. Load the land cover shapefile
lcsf_gdf = gpd.read_file(lcsf_path)
temp_biophysical_df = pd.read_csv(temp_bp_csv, delimiter=";")

# Set the CRS for all datasets
target_crs = "EPSG:2056"
lcsf_gdf = lcsf_gdf.to_crs(target_crs)

# 2. Load the ET0 raster and temperature raster
with rasterio.open(et0_raster_path) as et0_src:
    et0_meta = et0_src.meta
    et0_affine = et0_src.transform
    et0_data = et0_src.read(1)
    et0_bounds = et0_src.bounds
    et0_res = et0_src.res

with rasterio.open(t_air_ref_raster_path) as t_air_ref_src:
    t_air_ref_data = t_air_ref_src.read(1)

# 3. Merge biophysical data with shapefile according to "Art"
lcsf_gdf = lcsf_gdf.merge(temp_biophysical_df, on="Art")

# 4. Rasterize Albedo and Kc
def rasterize_feature(feature, transform, out_shape, all_touched=False):
    return rasterize(
        [(geom, value) for geom, value in zip(feature.geometry, feature)],
        out_shape=out_shape,
        transform=transform,
        fill=0,
        all_touched=all_touched,
        dtype=rasterio.float32
    )

albedo_raster = rasterize_feature(lcsf_gdf['Albedo'], et0_affine, et0_data.shape)
kc_raster = rasterize_feature(lcsf_gdf['Kc'], et0_affine, et0_data.shape)

# Save the Albedo and Kc rasters
with rasterio.open(output_albedo_path, 'w', **et0_meta) as dst:
    dst.write(albedo_raster, 1)

with rasterio.open(output_kc_path, 'w', **et0_meta) as dst:
    dst.write(kc_raster, 1)

# 5. Calculate ETI
eti_raster = (kc_raster * et0_data) / np.max(et0_data)

# Save the ETI raster
eti_meta = et0_meta.copy()
eti_meta.update(dtype=rasterio.float32)
with rasterio.open(output_ETI_path, 'w', **eti_meta) as dst:
    dst.write(eti_raster, 1)

# 6. Calculate Cooling Capacity (CC)
# Assume Shade is also rasterized or directly from the shapefile
shade_raster = rasterize_feature(lcsf_gdf['Shade'], et0_affine, et0_data.shape)
cc_raster = 0.6 * shade_raster + 0.2 * albedo_raster + 0.2 * eti_raster

# Save the Cooling Capacity raster
with rasterio.open(output_CC_path, 'w', **eti_meta) as dst:
    dst.write(cc_raster, 1)

# 7. Calculate Temperature
UHI_max = 5  # Example maximum UHI magnitude
temp_raster = t_air_ref_data + (1 - cc_raster) * UHI_max

# Save the Temperature raster
with rasterio.open(output_temp_path, 'w', **eti_meta) as dst:
    dst.write(temp_raster, 1)

# 8. Aggregate raster values to polygons
# Add "CC" attribute to shapefile
lcsf_gdf['CC'] = [x['mean'] for x in zonal_stats(lcsf_gdf, cc_raster, affine=et0_affine, stats=['mean'])]

# Add "temperature" attribute to shapefile
lcsf_gdf['temperature'] = [x['mean'] for x in zonal_stats(lcsf_gdf, temp_raster, affine=et0_affine, stats=['mean'])]

# 9. Save the updated shapefile
lcsf_gdf.to_file(output_shapefile_path)
print(f"Updated shapefile saved to: {output_shapefile_path}")
