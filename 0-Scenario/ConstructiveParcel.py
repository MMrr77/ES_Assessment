### This is the code first select parcels (resf.shp) that can be constructed on based on the allowed land types (grundnutzung.shp) and then filter out parcels that already have GWR (GWR_SZ.shp) and save the remaining parcels to a new shapefile (noBD_conparcel.shp).

import geopandas as gpd
import pandas as pd
import numpy as np

resf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/resf_grundnutzung.shp"
grundnutzung_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/grundnutzung.shp"
lcsf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/lcsf.shp"
construct_parcel_p = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/constructive_parcel_grun.shp"
GWR_p= "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/GWR_SZ.shp"
noBD_conparcels = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/noBD_conparcel_grun.shp"


parcels = gpd.read_file(resf_path)
grundnutzung = gpd.read_file(grundnutzung_path)
GWR = gpd.read_file(GWR_p)
lcsf= gpd.read_file(lcsf_path)

if parcels.crs != grundnutzung.crs:
    grundnutzung = grundnutzung.to_crs(parcels.crs)
if GWR.crs != parcels.crs:
    GWR = GWR.to_crs(parcels.crs)
if lcsf.crs != parcels.crs:
    roads = lcsf.to_crs(parcels.crs)

parcels = parcels.dropna(subset=['EGRIS_EGRI'])

allowed_typ_kommun = [
    '14.1.2', '14.1.3', '11.2.1', '11.2.2', '11.3.1', 
    '11.4.1', '13.1.1', '13.2.1', '13.3.1'
]

# Filter the land types to only include those with allowed typ_kommun values
building_land = grundnutzung[grundnutzung['typ_kommun'].isin(allowed_typ_kommun)]

# spatial intersection between parcels with ID and the filtered building land
intersected = gpd.overlay(parcels, building_land, how='intersection', keep_geom_type=False)

# Dissolve by EGID
intersected_dissolved = intersected.dissolve(by='EGRIS_EGRI', as_index=False, aggfunc='first')
intersected_dissolved['typ_kommun'] = intersected['typ_kommun']

# Compute area ratio - only significant overlaps are considered
intersected_dissolved['intersect_area'] = intersected_dissolved.area
parcels['parcel_area'] = parcels.area

print(parcels.columns)
print(intersected_dissolved.columns)

# Merge the intersected dissolved data back
merged = parcels.merge(intersected_dissolved[['EGRIS_EGRI', 'intersect_area', 'typ_kommun']], how='left', on='EGRIS_EGRI')

# area ratio
merged['area_ratio'] = merged['intersect_area'] / merged['parcel_area']

# Filter out parcels that overlap significantly (area_ratio > 0.5)
selected_parcels = merged[merged['area_ratio'] > 0.5]

# Exclude parcels overlapped with polygons in lcsf.shp where Art=Strasse_Weg
roads = lcsf[lcsf['Art'] == 'Strasse_Weg']
intersection = gpd.overlay(selected_parcels, roads, how='intersection')

intersection['overlap_area'] = intersection.area
selected_parcels['parcel_area'] = selected_parcels.area

selected_parcels = selected_parcels.merge(intersection[['EGRIS_EGRI', 'overlap_area']], on='EGRIS_EGRI', how='left')
selected_parcels['overlap_area'].fillna(0, inplace=True)

selected_parcels['overlap_ratio'] = selected_parcels['overlap_area'] / selected_parcels['parcel_area']

## remove parcels with significant overlap (0.4)
final_selected_parcels = selected_parcels[selected_parcels['overlap_ratio'] <= 0.4]
## save
final_selected_parcels.to_file(construct_parcel_p)
print(f"Selected parcels after road deduction saved to {construct_parcel_p}.")


construct_parcel = gpd.read_file(construct_parcel_p)

# Save the selected parcels to a new shapefile
selected_parcels.to_file(construct_parcel_p)

print(f"Selected parcels with significant overlap with allowed land types saved to {construct_parcel_p}.")

construct_parcel = gpd.read_file(construct_parcel_p)
if construct_parcel.crs != GWR.crs:
    GWR = GWR.to_crs(construct_parcel.crs)

parcels_with_GWR = gpd.sjoin(construct_parcel, GWR, how='inner', predicate='contains')
parcels_with_building_ids = parcels_with_GWR['EGRIS_EGRI'].unique()

parcels_without_GWR = construct_parcel[~construct_parcel['EGRIS_EGRI'].isin(parcels_with_building_ids)]

parcels_without_GWR = construct_parcel[~construct_parcel['EGRIS_EGRI'].isin(parcels_with_building_ids)]

parcels_without_GWR.to_file(noBD_conparcels)
print(f"Parcels without existing GWR saved to {noBD_conparcels}.")