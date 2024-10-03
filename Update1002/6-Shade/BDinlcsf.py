import geopandas as gpd
import numpy as np

lcsf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/2_join_bds_to_LULC/sjMap_1002_2035.shp"
buildings_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/9-Shade/buildings.shp"
BDinlcsf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/Update1002/0-Data/9-Shade/BDinlcsf.shp"

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


merged_data['height'] = np.where(
    merged_data['new_constr'] == 1.0,  # Condition: if new_construct is 1
    merged_data['VG'] * 3.5,            # New building height: VG * 3.5
    np.where(                           # Else
        merged_data['GASTW'].notna(),   # If GASTW is available
        merged_data['GASTW'] * 3.0,     # Old building height: GASTW * 3.0
        0                               # Default height for missing values
    )
)


merged_data.to_file(BDinlcsf_path)
