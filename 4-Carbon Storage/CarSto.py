import geopandas as gpd
import pandas as pd

lcsf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/lcsf.shp"
biophysical_table_csv = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/6-CarbonSto/Car_BP.csv"
carsto_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/6-CarbonSto/CarSto.shp"


lcsf_gdf = gpd.read_file(lcsf_path)
lcsf_gdf = lcsf_gdf.to_crs("EPSG:2056") 

biophysical_df = pd.read_csv(biophysical_table_csv, delimiter=';')

lcsf_gdf = lcsf_gdf.merge(biophysical_df, on="Art")

lcsf_gdf['area_gdf'] = lcsf_gdf.geometry.area / 10000  # Convert to hectares

# Calculate Carbon Stock for each pool
for pool in ['above', 'dead', 'below', 'soil']:
    carbon_column = f'C_{pool}'
    lcsf_gdf[f'CarStock_{pool}'] = lcsf_gdf[carbon_column] * lcsf_gdf['area_gdf']

# Sum the Carbon Stock across all pools to get the total Carbon Stock
lcsf_gdf['TotalCarbonStock'] = lcsf_gdf[[f'CarStock_{pool}' for pool in ['above', 'dead', 'below', 'soil']]].sum(axis=1)

# Aggregate total carbon stock
total_carbon_stock_current = lcsf_gdf['TotalCarbonStock'].sum()
print(f"Total Carbon Stock (Current Scenario): {total_carbon_stock_current} metric tons")

# Save the updated GeoDataFrame to a new shapefile
lcsf_gdf.to_file(carsto_path)

print(f"Updated shapefile saved to: {carsto_path}")
