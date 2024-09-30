import geopandas as gpd

construct_parcel_p = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/constructive_parcel.shp"
GWR_p= "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/GWR_SZ.shp"
noBD_conparcels = "/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/1_predict_newbds_parcels/noBD_conparcel.shp"



construct_parcel = gpd.read_file(construct_parcel_p)
GWR = gpd.read_file(GWR_p)

if construct_parcel.crs != GWR.crs:
    GWR = GWR.to_crs(construct_parcel.crs)


parcels_with_GWR = gpd.sjoin(construct_parcel, GWR, how='inner', predicate='contains')

parcels_with_building_ids = parcels_with_GWR['EGRIS_EGRI'].unique()

# Filter the selected parcels to keep only those that do NOT have GWR
parcels_without_GWR = construct_parcel[~construct_parcel['EGRIS_EGRI'].isin(parcels_with_building_ids)]

# Save the parcels without GWR to a new shapefile
parcels_without_GWR.to_file(noBD_conparcels)

print(f"Parcels without existing GWR saved to {noBD_conparcels}.")

