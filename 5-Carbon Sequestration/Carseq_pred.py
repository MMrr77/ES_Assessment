import geopandas as gpd
import pandas as pd

# File paths (replace these with your actual paths)
lcsf_pred_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/2_join_bds_to_LULC/sjoinedMap.shp"
carbon_sequestration_csv = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/7-CarbonSeq/CarSeq.csv"
pred_output_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/7-CarbonSeq/CarSeq_pred.shp"

lcsf_pred_gdf = gpd.read_file(lcsf_pred_path)
target_crs = "EPSG:2056"
if lcsf_pred_gdf.crs != target_crs:
    lcsf_pred_gdf = lcsf_pred_gdf.to_crs(target_crs)


carbon_sequestration_df = pd.read_csv(carbon_sequestration_csv, delimiter=",")

# Merge
lcsf_pred_gdf = lcsf_pred_gdf.merge(carbon_sequestration_df, on="Art")


lcsf_pred_gdf.to_file(pred_output_path)
print(f"New shapefile with carbon sequestration values saved to: {pred_output_path}")
