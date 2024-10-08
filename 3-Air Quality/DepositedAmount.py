import geopandas as gpd
import rasterio
from rasterio.mask import mask
import pandas as pd
import numpy as np
from shapely.geometry import mapping


target_crs = "EPSG:2056"


lcsf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/lcsf.shp"
deposition_rate_csv = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/5-Airquality/DepositionRate.csv"
lai_raster = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/5-Airquality/LAI_SZ.tif"
depositedAmount_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/5-Airquality/DepositedAmount.shp"

lcsf_gdf = gpd.read_file(lcsf_path)
lcsf_gdf = lcsf_gdf.to_crs(target_crs)
deposition_df = pd.read_csv(deposition_rate_csv, delimiter=';')

lcsf_gdf = lcsf_gdf.merge(deposition_df, on="Art")


# Process the LAI raster
with rasterio.open(lai_raster) as src:
    lai_data = src.read(1) / 1000.0  # Calculate actual LAI = cell value/1000

    # Clean the LAI data
    lai_data[lai_data < 0] = 0  # Set values less than 0 to 0
    lai_data[lai_data > 10] = 10  # Set values greater than 10 to 10

    # Extract cleaned actual LAI value to each polygon
    deposited_amounts = []

    for idx, row in lcsf_gdf.iterrows():
        # Mask
        geom = [mapping(row.geometry)]
        out_image, out_transform = mask(src, geom, crop=True)
        out_image = out_image[0]  # band 1
        

        lai_mean = np.mean(out_image[out_image > 0])  # filter positive
        
        # Velocity t = 1s
        deposited_amount = lai_mean * row["Vd"] * 1.0
        deposited_amounts.append(deposited_amount)
        
    lcsf_gdf["DeposiAmount"] = deposited_amounts


# Remove outliers using IQR method
Q1 = lcsf_gdf["DeposiAmount"].quantile(0.25)
Q3 = lcsf_gdf["DeposiAmount"].quantile(0.75)
IQR = Q3 - Q1

# Define the acceptable range based on IQR
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

# Filter out the outliers
filtered_gdf = lcsf_gdf[(lcsf_gdf["DeposiAmount"] >= lower_bound) & (lcsf_gdf["DeposiAmount"] <= upper_bound)]


filtered_gdf.to_file(depositedAmount_path)
print(f"Deposited amount calculation completed, outliers removed, and results saved to {depositedAmount_path}.")