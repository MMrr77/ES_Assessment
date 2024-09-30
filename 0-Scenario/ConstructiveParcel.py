import geopandas as gpd
import pandas as pd
import numpy as np

resf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/resf.shp"
grundnutzung_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/grundnutzung.shp"

construct_parcel_p = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/constructive_parcel.shp"
GWR_p= "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/GWR_SZ.shp"
noBD_conparcels = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/noBD_conparcel.shp"



parcels = gpd.read_file(resf_path)
land_types = gpd.read_file(grundnutzung_path)
GWR = gpd.read_file(GWR_p)

if parcels.crs != land_types.crs:
    land_types = land_types.to_crs(parcels.crs)


parcels = parcels.dropna(subset=['EGRIS_EGRI'])

allowed_typ_kommun = [
    '14.1.2', '14.1.3', '11.2.1', '11.2.2', '11.3.1', 
    '11.4.1', '13.1.1', '13.2.1', '13.3.1'
]

# Filter the land types to only include those with allowed typ_kommun values
building_land = land_types[land_types['typ_kommun'].isin(allowed_typ_kommun)]

# spatial intersection between parcels with ID and the filtered building land
intersected = gpd.overlay(parcels, building_land, how='intersection')

# Dissolve by EGID
intersected_dissolved = intersected.dissolve(by='EGRIS_EGRI', as_index=False, aggfunc='first')
intersected_dissolved['land_type_code'] = intersected['typ_kommun']

# Compute area ratio - only significant overlaps are considered
intersected_dissolved['intersect_area'] = intersected_dissolved.area
parcels['parcel_area'] = parcels.area

# Merge the intersected dissolved data back
merged = parcels.merge(intersected_dissolved[['intersect_area']], how='left', on='EGRIS_EGRI')

# area ratio
merged['area_ratio'] = merged['intersect_area'] / merged['parcel_area']

# Filter out parcels that overlap significantly (area_ratio > 0.5)
selected_parcels = merged[merged['area_ratio'] > 0.5]

# Save the selected parcels to a new shapefile
selected_parcels.to_file(construct_parcel_p)

print(f"Selected parcels with significant overlap with allowed land types saved to {construct_parcel_p}.")

construct_parcel = gpd.read_file(construct_parcel_p)

if construct_parcel.crs != GWR.crs:
    GWR = GWR.to_crs(construct_parcel.crs)

parcels_with_GWR = gpd.sjoin(construct_parcel, GWR, how='inner', predicate='contains')

parcels_with_building_ids = parcels_with_GWR['EGRIS_EGRI'].unique()

parcels_without_GWR = construct_parcel[~construct_parcel['EGRIS_EGRI'].isin(parcels_with_building_ids)]

parcels_without_GWR.to_file(noBD_conparcels)
print(f"Parcels without existing GWR saved to {noBD_conparcels}.")

