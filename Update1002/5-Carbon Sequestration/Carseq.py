import geopandas as gpd
import pandas as pd

# File paths (replace these with your actual paths)
lcsf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/lcsf.shp"
carbon_sequestration_csv = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/7-CarbonSeq/CarSeq.csv"
output_shapefile_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/7-CarbonSeq/CarSeq.shp"

lcsf_gdf = gpd.read_file(lcsf_path)
target_crs = "EPSG:2056"
if lcsf_gdf.crs != target_crs:
    lcsf_gdf = lcsf_gdf.to_crs(target_crs)


carbon_sequestration_df = pd.read_csv(carbon_sequestration_csv, delimiter=",")

# Merge
lcsf_gdf = lcsf_gdf.merge(carbon_sequestration_df, on="Art")


lcsf_gdf.to_file(output_shapefile_path)
print(f"New shapefile with carbon sequestration values saved to: {output_shapefile_path}")
