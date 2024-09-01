import geopandas as gpd
import numpy as np

lcsf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/lcsf.shp"
buildings_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/9-Shade/buildings.shp"
BDinlcsf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/9-Shade/BDinlcsf.shp"

buildings = gpd.read_file(buildings_path)
lcsf = gpd.read_file(lcsf_path)


target_crs = "EPSG:2056"
if buildings.crs != target_crs:
    buildings = buildings.to_crs(target_crs)
if lcsf.crs != target_crs:
    lcsf = lcsf.to_crs(target_crs)

lcsf['GWR_EGID'] = lcsf['GWR_EGID'].astype(str)
buildings['egid'] = buildings['egid'].astype(str)


merged_data = lcsf.merge(buildings[['egid', 'GASTW']], left_on='GWR_EGID', right_on='egid', how='left')


merged_data['height'] = np.where(merged_data['GASTW'].notna(), merged_data['GASTW'] * 3.0, 0)


merged_data.to_file(BDinlcsf_path)
