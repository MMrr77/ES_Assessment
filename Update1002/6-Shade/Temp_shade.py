import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_origin
import numpy as np

# Paths to your shapefiles
temp_shp_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/8-Temperature/Temp.shp"
shadow_shp_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/9-Shade/shadow.shp"
output_raster_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/9-Shade/Temp_shade.tif"

temp_gdf = gpd.read_file(temp_shp_path)
shadow_gdf = gpd.read_file(shadow_shp_path)

target_crs = "EPSG:2056"
if temp_gdf.crs != target_crs:
    temp_gdf = temp_gdf.to_crs(target_crs)
if shadow_gdf.crs != target_crs:
    shadow_gdf = shadow_gdf.to_crs(target_crs)

# Determine the raster extent and resolution
minx, miny, maxx, maxy = temp_gdf.total_bounds
cell_size = 1  # 10m
width = int((maxx - minx) / cell_size)
height = int((maxy - miny) / cell_size)

# Transform
transform = from_origin(minx, maxy, cell_size, cell_size)

# Rasterize temp.shp
temp_raster = rasterize(
    [(geom, value) for geom, value in zip(temp_gdf.geometry, temp_gdf['Temperatur'])],
    out_shape=(height, width),
    transform=transform,
    fill=np.nan,  # Set areas without data to NaN
    dtype='float32'
)

# Rasterize shadow.shp (using binary values: 1 for shadow, 0 for no shadow)
shadow_raster = rasterize(
    [(geom, 1) for geom in shadow_gdf.geometry],
    out_shape=(height, width),
    transform=transform,
    fill=0,  # Areas without shadows are 0
    dtype='int32'
)

# Apply temperature reduction where shadow exists
adjusted_temp_raster = np.where(shadow_raster == 1, temp_raster - 0.6, temp_raster)

# Save the adjusted temperature raster
with rasterio.open(
    output_raster_path,
    'w',
    driver='GTiff',
    height=height,
    width=width,
    count=1,
    dtype='float32',
    crs=target_crs,
    transform=transform,
) as dst:
    dst.write(adjusted_temp_raster, 1)

print(f"Adjusted temperature raster saved to {output_raster_path}")


https://ethz.zoom.us/j/69643332752