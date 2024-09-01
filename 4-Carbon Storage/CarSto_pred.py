import geopandas as gpd
import pandas as pd

lcsf_pred_path ="/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/2_join_bds_to_LULC/sjoinedMap.shp"
biophysical_table_csv = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/6-CarbonSto/Car_BP.csv"
carsto_pred_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/6-CarbonSto/CarSto_pred.shp"


lcsf_pred_gdf = gpd.read_file(lcsf_pred_path)
lcsf_pred_gdf = lcsf_pred_gdf.to_crs("EPSG:2056") 

biophysical_df = pd.read_csv(biophysical_table_csv, delimiter=';')

lcsf_pred_gdf = lcsf_pred_gdf.merge(biophysical_df, on="Art")

lcsf_pred_gdf['area_gdf'] = lcsf_pred_gdf.geometry.area / 10000  # Convert to hectares

# Carbon Stock for each pool
for pool in ['above', 'dead', 'below', 'soil']:
    carbon_column = f'C_{pool}'
    lcsf_pred_gdf[f'CarStock_{pool}'] = lcsf_pred_gdf[carbon_column] * lcsf_pred_gdf['area_gdf']

# Sum the Carbon Stock across all pools to get the total Carbon Stock
lcsf_pred_gdf['TotalCarbonStock'] = lcsf_pred_gdf[[f'CarStock_{pool}' for pool in ['above', 'dead', 'below', 'soil']]].sum(axis=1)

# Aggregate total carbon stock
total_carbon_stock_pred = lcsf_pred_gdf['TotalCarbonStock'].sum()
print(f"Total Carbon Stock (Current Scenario): {total_carbon_stock_pred} metric tons")


lcsf_pred_gdf.to_file(carsto_pred_path)

print(f"Updated shapefile saved to: {carsto_pred_path}")