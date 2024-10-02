### This is the code first select parcels (resf.shp) that can be constructed on based on the allowed land types (grundnutzung.shp) and then filter out parcels that already have GWR (GWR_SZ.shp) and save the remaining parcels to a new shapefile (noBD_conparcel.shp).
import geopandas as gpd
import pandas as pd
import numpy as np

# File paths
resf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/resf_grundnutzung.shp"
grundnutzung_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/grundnutzung.shp"
lcsf_path = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/lcsf.shp"
construct_parcel_p = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/constructive_parcel_grun.shp"
construct_p_noRD = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/constructive_parcel_noRD.shp"

GWR_p = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/GWR_SZ.shp"
noBD_conparcels = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/noBD_conparcel_grun.shp"

parcels = gpd.read_file(resf_path)
grundnutzung = gpd.read_file(grundnutzung_path)
GWR = gpd.read_file(GWR_p)
lcsf = gpd.read_file(lcsf_path)

# CRS
if parcels.crs != grundnutzung.crs:
    grundnutzung = grundnutzung.to_crs(parcels.crs)
if GWR.crs != parcels.crs:
    GWR = GWR.to_crs(parcels.crs)
if lcsf.crs != parcels.crs:
    lcsf = lcsf.to_crs(parcels.crs)  # This was incorrect in your previous script

# Filter parcels based on allowed typ_kommun
parcels = parcels.dropna(subset=['EGRIS_EGRI'])
allowed_typ_kommun = ['14.1.2', '14.1.3', '11.2.1', '11.2.2', '11.3.1', '11.4.1', '13.1.1', '13.2.1', '13.3.1']
building_land = grundnutzung[grundnutzung['typ_kommun'].isin(allowed_typ_kommun)]


##### 
# Spatial intersection
intersected = gpd.overlay(parcels, building_land, how='intersection', keep_geom_type=False)

# Dissolve by EGRIS_EGRI
intersected_dissolved = intersected.dissolve(by='EGRIS_EGRI', as_index=False, aggfunc='first')
intersected_dissolved['typ_kommun'] = intersected['typ_kommun']

# Compute area ratio - only significant overlaps are considered
intersected_dissolved['intersect_area'] = intersected_dissolved.area
parcels['parcel_area'] = parcels.area

# Merge the intersected dissolved data back
merged = parcels.merge(intersected_dissolved[['EGRIS_EGRI', 'intersect_area', 'typ_kommun']], how='left', on='EGRIS_EGRI')

# Calculate area ratio
merged['area_ratio'] = merged['intersect_area'] / merged['parcel_area']

# Filter out parcels that don't overlap significantly (area_ratio > 0.5)
selected_parcels = merged[merged['area_ratio'] > 0.3]
# selected_parcels.to_file(construct_parcel_p)


# Exclude parcels overlapped with roads in lcsf.shp where Art=Strasse_Weg， Trottoir
roads = lcsf[lcsf['Art'].isin(['Strasse_Weg', 'Trottoir'])]  # Filter road
intersection = gpd.overlay(selected_parcels, roads, how='intersection')

# Calculate overlap area between selected parcels and roads
intersection['overlap_area'] = intersection.area
selected_parcels['parcel_area'] = selected_parcels.area

# Merge overlap areas with  selected parcels
selected_parcels = selected_parcels.merge(intersection[['EGRIS_EGRI', 'overlap_area']], on='EGRIS_EGRI', how='left')
selected_parcels['overlap_area'].fillna(0, inplace=True)  # missing value = 0

# Calculate overlap ratio
selected_parcels['overlap_ratio'] = selected_parcels['overlap_area'] / selected_parcels['parcel_area']

# Remove parcels with significant overlap (overlap_ratio > 0.4)
final_selected_parcels = selected_parcels[selected_parcels['overlap_ratio'] <= 0.5]

# save
final_selected_parcels.to_file(construct_parcel_p)
print(f"Selected parcels after road deduction saved to {construct_parcel_p}.")


#####
# compute area and perimeter of each parcel: to remove the roads parcels again
construct_parcel_p = gpd.read_file(construct_parcel_p)

construct_parcel_p['parcel_area'] = construct_parcel_p.geometry.area
construct_parcel_p['perimeter'] = construct_parcel_p.geometry.length

construct_parcel_p['perimeter_area_ratio'] = construct_parcel_p['perimeter'] / construct_parcel_p['parcel_area']

# Filter out parcels that are outliers based on perimeter-to-area ratio (< 0.25)
filtered_roads = construct_parcel_p[construct_parcel_p['perimeter_area_ratio'] <= 0.25]

filtered_roads.to_file(construct_p_noRD)
print(f"Filtered parcels based on perimeter-to-area ratio saved to {construct_p_noRD}.")


#####z
# Filter out parcels that already have GWR (existing buildings)
construct_p_noRD = gpd.read_file(construct_p_noRD)

# Ensure CRS
if construct_p_noRD.crs != GWR.crs:
    GWR = GWR.to_crs(construct_p_noRD.crs)

# spatial join to find parcels that contain GWR (buildings)
parcels_with_GWR = gpd.sjoin(construct_p_noRD, GWR, how='inner', predicate='contains')
parcels_with_building_ids = parcels_with_GWR['EGRIS_EGRI'].unique()

# Exclude parcels that have existing GWR
parcels_without_GWR = construct_p_noRD[~construct_p_noRD['EGRIS_EGRI'].isin(parcels_with_building_ids)]

parcels_without_GWR.to_file(noBD_conparcels)
print(f"Parcels without existing GWR saved to {noBD_conparcels}.")
