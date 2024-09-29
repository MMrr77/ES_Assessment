# import json
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

pd.set_option('display.max_columns', None)
# pd.reset_option('display.max_columns')

########## data import / export

gwr_ds = r"F:\home\michals\shared\ieb_files\gebaeude_batiment_edificio.csv"
av_ds = r"F:\home\michals\shared\ieb_files\av\av_testgemeinden_1.shp"
av_subtract_ds = r"F:\home\michals\shared\ieb_files\av_subtract\sz_strassen_schwyz_ALL.shp"
grundnutz_ds = r"F:\home\michals\shared\ieb_files\nutzungsplanung\grundnutzung_testgemeinden_1_AZ.shp"
bzo_ds = r"F:\home\michals\shared\ieb_files\bzo_masse\ieb_Baumasse_SZ_mss.csv"
snp_ds = r"F:\home\michals\shared\ieb_files\nutzungsplanung\ueberlagernde_nutzungsplaninhalte_flaechen.shp"
statent_ds = r"F:\home\michals\shared\ieb_files\statent\statent_sz_2021.shp"
statpop_ds = r"F:\home\michals\shared\ieb_files\statpop\STATPOP_2022_SZ.shp"

capacity_export = r"F:\home\michals\shared\ieb_files\kapazitat\av_capacity.shp"
gwr_export = r"F:\home\michals\shared\ieb_files\gwr_sz.csv"
av_grundnutz_export = r"F:\home\michals\shared\ieb_files\av_intersection\av_grundnutz.shp"

EXPORT = 1

########## data cleaning

# relevant features:
# av: EGRIS_EGRID, Flaeche + bzo: typ_kanton (11 - Wohnzonen, 13 - Mischzonen, 14 - Zentrumszonen)
# gwr: EGRID, GAREA, GSTAW (Anzahl Geschosse),
# statpop: pseudoFederalBuildingId, geoCoordE, geoCoordN
#   GKAT (1020, 1030, 1040 - Geb. mit Wohnnutzung), GSTAT (1050, 1007, 1008 - not realised/usable -> apply 0m2 Area?)
# GKAT_SELECT = [1020, 1030, 1040] # do not implement
# GSTAT_REJECT = [1005, 1007, 1008]  # to be implemented?


GWR_COLSELECT = ["EGRID", "GAREA", "GASTW", "GKAT", "GSTAT"]
KORREKTUR_KONSTRUKTION = 0.9

AV_COLSELECT = ["BFSNr", "NAME", "EGRIS_EGRI", "Nummer", "geometry"]

GRUNDNUTZ_COLSELECT = ["typ_kommun", "typ_komm_1", "hauptnutzu", "hauptnut_1", "AZ", "geometry"]
ZONES_SELECT = [11, 13, 14]

BZO_SELECT = ["Baumass", "Wert", "typ_kommun", "Zone"]
BAUMASS_SELECT = ["Zone", "typ_kommun", "AZ", "GH", "VG", "GrA", "GeA", "kGA", "gGA"]

SNP_COLSELECT = ["typ_komm_1", "hauptnutzu", "geometry"]
SNP_COLRENAME = {"typ_komm_1":"typ_komm_1_SNP", "hauptnutzu":"hauptnutzu_SNP"}
SNP_ZONES = [61]


KORREKTUR_AG = [0.66, 0.2, 0.1] # korrekturen nicht ueberbaut, unternutzt, bebaute Potenziale
KORREKTUR_WZ = 0.9
KORREKTUR_WMZ_ZZ = 0.5
KORREKTUR_AUSSCHOEPFUNG = 0.8

KORREKTUR_AZ_SNP = 1.1


#%%

########## GWR

# "CH967722407633" unbebaute Parzelle Schwyz ->
# CH207740742262 Kirche Schwyz

gwr = pd.read_csv(gwr_ds, delimiter='\t')

gwr = gwr.filter(GWR_COLSELECT, axis=1)

# gwr = gwr[gwr["GKAT"].isin(GKAT_SELECT)]

print(gwr[gwr["GASTW"].isna()])  # certain building types have GASTW == NaN (usually garages)

gwr["GASTW"] = gwr["GASTW"].fillna(1.0)
gwr["GAREA"] = gwr["GAREA"].fillna(0.01)  # will have to repeated with "RGF" after join with AV (plots without buildings->not in GWR)

gwr["RGF"] = gwr["GAREA"] * gwr["GASTW"] * KORREKTUR_KONSTRUKTION  # NOTE: Not all GAREA seem to be correct

print(gwr[gwr["RGF"] == 0])
print(gwr[gwr["RGF"].isna()])

print(gwr.GKAT.value_counts())

gwr_aggregated = gwr.groupby("EGRID").agg(
    GKAT=pd.NamedAgg(column="GKAT", aggfunc='first'),  # should be majority ratio function
    GASTW=pd.NamedAgg(column="GASTW", aggfunc='max'),
    GAREA=pd.NamedAgg(column="GAREA", aggfunc='sum'),
    RGF=pd.NamedAgg(column="RGF", aggfunc="sum")
).reset_index()

print(gwr_aggregated.head())

gwr_aggregated.to_csv(gwr_export, sep=";")

#%%

########## AV

av = gpd.read_file(av_ds) ; print("AV shapefile imported")

av = av.filter(AV_COLSELECT)

av = av.merge(gwr_aggregated, left_on="EGRIS_EGRI", right_on="EGRID", how="left")
av.drop("EGRID", axis=1, inplace=True)

av.fillna(0, inplace=True)


########## SNP

snp = gpd.read_file(snp_ds) ; print("SNP shapefile imported")
snp = snp.filter(SNP_COLSELECT)
snp = snp[snp["hauptnutzu"].isin(SNP_ZONES)]
snp.rename(columns=SNP_COLRENAME, inplace=True)

av_snp = av.sjoin(snp, how="left", predicate="within", rsuffix="SNP") ; print("AV + SNP join executed")
av_snp.fillna("keine SNP:61", inplace=True)

agg_dict = {
    'BFSNr':'first',
    'NAME':'first',
    'GKAT': 'first',
    'GASTW': 'max',
    'GAREA': 'sum',
    'EGRIS_EGRI': 'first',
    'Nummer': 'first',
    'RGF': 'sum',
    'typ_komm_1_SNP': 'first',
    'hauptnutzu_SNP': 'first'
}

av_snp_rest = av_snp[av_snp['index_SNP'] == 'keine SNP:61']
av_snp_dis = av_snp[~(av_snp['index_SNP'] == 'keine SNP:61')]
av_snp_dis = av_snp_dis.dissolve(by='index_SNP', as_index=False, aggfunc=agg_dict)


av_snp = pd.concat([av_snp_dis, av_snp_rest], ignore_index=True)
av_snp['Area'] = av_snp.area


########## Grundnutzung

grundnutz = gpd.read_file(grundnutz_ds) ; print("\nGrundnutzung+AZ shapefile imported\n")

grundnutz = grundnutz.filter(GRUNDNUTZ_COLSELECT)

#%%
# intersection between AV & Grundnutzung
av_grundnutz = av_snp.overlay(grundnutz, how="intersection", keep_geom_type=False)
print("\nintersection AV + Grundnutzung executed\n")
print(len(av_grundnutz))    # 34186 features

av_grundnutz = av_grundnutz.drop_duplicates(subset="geometry")  # 21936 features

av_grundnutz = av_grundnutz[av_grundnutz["hauptnutzu"].isin(ZONES_SELECT)]

print(av_grundnutz.geom_type.value_counts())

# data cleaning: explode multipolygons/geometries, remove point features, join together by temp_ID
av_grundnutz['temp_ID'] = [i for i in range(1, (len(av_grundnutz) + 1) )]

av_grundnutz = av_grundnutz.explode(index_parts=False)

av_grundnutz = av_grundnutz[av_grundnutz['geometry'].geom_type != 'Point']
av_grundnutz = av_grundnutz[av_grundnutz['geometry'].geom_type != 'LineString']

av_grundnutz = av_grundnutz.dissolve('temp_ID')

# av_grundnutz.drop('temp_ID', axis=1, inplace=True) # it seems temp_ID is dropped anyway in the dissolve operation

av_grundnutz["Area_split"] = av_grundnutz.area

av_grundnutz = av_grundnutz[~(av_grundnutz["Area_split"] < 0.01)]

av_grundnutz["Area_ratio"] = av_grundnutz["Area_split"] / av_grundnutz["Area"]

av_grundnutz['AZ'] = pd.to_numeric(av_grundnutz['AZ'])

condition_AZ_bonus = (av_grundnutz['hauptnutzu_SNP']=='keine SNP:61')
av_grundnutz.loc[~condition_AZ_bonus, 'AZ'] = av_grundnutz.loc[~condition_AZ_bonus, 'AZ'].values * KORREKTUR_AZ_SNP

av_grundnutz["MGF"] = (av_grundnutz["AZ"]).astype(float) * av_grundnutz["Area_split"]

# calculating theoretical max capacity with AZ=1 without filling in na's in AZ
av_grundnutz.loc[av_grundnutz['AZ'].isna(), "MGF"] = av_grundnutz.loc[av_grundnutz['AZ'].isna(), "Area_split"] * 1.0001
av_grundnutz.loc[av_grundnutz['AZ'].isna() & condition_AZ_bonus, "MGF"] = av_grundnutz.loc[av_grundnutz['AZ'].isna() & condition_AZ_bonus, "Area_split"] * (1.0001 * KORREKTUR_AZ_SNP)

print(av_grundnutz.geom_type.value_counts())

#%%

bzo = pd.read_csv(bzo_ds, delimiter=";")

bzo = bzo.filter(BZO_SELECT, axis=1)

bzo = bzo.pivot_table(index='typ_kommun', columns='Baumass', values='Wert', aggfunc='min')

bzo.reset_index(inplace=True)

bzo = bzo.filter(BAUMASS_SELECT, axis=1)

# dealing with various missing Baumasse: case by case basis

bzo["GrA_mean"] = bzo[['kGA', 'gGA']].mean(axis=1)
bzo.loc[bzo["GrA_mean"].isna(), "GrA_mean"] = bzo["GeA"]
bzo.loc[bzo["typ_kommun"] == "11.2.1", "GrA_mean"] = 3.
bzo["GrA_mean"] = bzo["GrA_mean"].fillna(bzo["GrA_mean"].mean())
bzo.loc[bzo["typ_kommun"] == "11.1.1", "VG"] = 1  # setting number of storeys of W1 to 1

# bzo["AZ"] = bzo["AZ"].fillna(1.0)

bzo.loc[bzo["VG"].isna(), "VG"] = round( (bzo["GH"] / 3) , 0)

bzo.loc[bzo["VG"] == "15.1.1", "VG"] = 1

print(bzo.isna().sum())

bzo = bzo.filter(["typ_kommun", "VG", "GrA_mean"], axis=1)  # currently taking AZ out, since it is already in grundnutz shapefile

av_grundnutz = av_grundnutz.merge(bzo, left_on="typ_kommun", right_on="typ_kommun", how="left")

av_grundnutz['buffer_geometry'] = av_grundnutz.apply(lambda row: row['geometry'].buffer(-row['GrA_mean']), axis=1)


#%%
av_grundnutz["GFA"] = av_grundnutz['buffer_geometry'].area
av_grundnutz.loc[av_grundnutz["GFA"] < 1.0 , "GFA"] = 1.0 #1.0m2

av_grundnutz["MGF_Geo"] = av_grundnutz["GFA"] * av_grundnutz["VG"]

av_grundnutz["Geo_delta"] = av_grundnutz["MGF_Geo"] - av_grundnutz["MGF"]

av_grundnutz["KapKor"] = av_grundnutz["MGF_Geo"] / av_grundnutz["MGF"]

# condition_KapKor = av_grundnutz["Geo_delta"] > 0
condition_KapKor = ~av_grundnutz["AZ"].isna() & av_grundnutz["Geo_delta"] > 0  # only applying correction to zones without AZ
av_grundnutz.loc[condition_KapKor, 'MGF_Geo'] = av_grundnutz.loc[condition_KapKor, 'MGF_Geo'] / av_grundnutz["KapKor"]


# av_grundnutz['MGF_GeoKor'] = av_grundnutz.loc[condition_KapKor, 'MGF_Geo'] / av_grundnutz["KapKor"]

# av_grundnutz["MGF_delta"] = av_grundnutz["MGF"] - av_grundnutz["MGF_Geo"]

# condition_AZ_bonus = (av_grundnutz['hauptnutzu_SNP']=='keine SNP:61')
# av_grundnutz.loc[~condition_AZ_bonus, 'AZ'] = av_grundnutz.loc[~condition_AZ_bonus, 'AZ'].values * KORREKTUR_AZ_SNP

# av_geo = av_grundnutz.merge(bzo, on=["typ_kommun", "Baumass"], how="left")

# av_geo = av_geo.pivot_table(index=av_geo.index, columns='Baumass', values='Wert', aggfunc='first')

# av_geo.reset_index(inplace=True)

#%%

########## AV + GWR --> capacity calculation

print('NAs in RGF', av_grundnutz["RGF"].isna().sum())

av_grundnutz["RGF"] = av_grundnutz["RGF"].fillna(0.01)  # check if necessary at this stage

av_grundnutz["RGF_split"] = av_grundnutz["RGF"] * av_grundnutz["Area_ratio"]

# av_grundnutz['AZ'] = av_grundnutz['AZ'].fillna(1.0001)  # can delete, see line 184


#####

av_grundnutz["max_kap"] = av_grundnutz["MGF"] - av_grundnutz["RGF_split"]
av_grundnutz["AG"] = av_grundnutz["RGF_split"] / av_grundnutz["MGF"] * 100

av_grundnutz["max_kap_geo"] = av_grundnutz["MGF_Geo"] - av_grundnutz["RGF_split"]
av_grundnutz["AG_geo"] = av_grundnutz["RGF_split"] / av_grundnutz["MGF_Geo"] * 100

# theo_kap:
condition_Z1 = av_grundnutz['hauptnutzu'] == 11
condition_Z2 = (av_grundnutz['hauptnutzu'] == 13) | (av_grundnutz['hauptnutzu'] == 14)
av_grundnutz.loc[condition_Z1, 'theo_kap'] = av_grundnutz.loc[condition_Z1, 'max_kap'] * KORREKTUR_WZ
av_grundnutz.loc[condition_Z2, 'theo_kap'] = av_grundnutz.loc[condition_Z2, 'max_kap'] * KORREKTUR_WMZ_ZZ

av_grundnutz["theo_kap"] = av_grundnutz["theo_kap"] * KORREKTUR_AUSSCHOEPFUNG

# Define AG conditions
condition_AG1 = av_grundnutz['AG'] <= 5
condition_AG2 = (av_grundnutz['AG'] > 5) & (av_grundnutz['AG'] <= 50)
condition_AG3 = av_grundnutz['AG'] > 50

# Update 'mob_kap' based on AG conditions
av_grundnutz.loc[condition_AG1, 'mob_kap'] = av_grundnutz.loc[condition_AG1, 'theo_kap'] * KORREKTUR_AG[0]
av_grundnutz.loc[condition_AG2, 'mob_kap'] = av_grundnutz.loc[condition_AG2, 'theo_kap'] * KORREKTUR_AG[1]
av_grundnutz.loc[condition_AG3, 'mob_kap'] = av_grundnutz.loc[condition_AG3, 'theo_kap'] * KORREKTUR_AG[2]

# some properties with different AG / zone to check calculations
# print(av_grundnutz.iloc[8,:])
# print(av_grundnutz.iloc[10])
# print(av_grundnutz.iloc[51])

#%%

def weighted_avg(group_df, whole_df, values, weights):
    v = whole_df.loc[group_df.index, values]
    w = whole_df.loc[group_df.index, weights]
    return (v.astype(float) * w).sum() / w.sum()

def majority_ratio(group_df, whole_df, values, field):
    v = whole_df.loc[group_df.index, values]
    s = whole_df.loc[group_df.index, field]
    return v[s.idxmax()]

capacity = av_grundnutz.dissolve(
    by="EGRIS_EGRI",
        aggfunc={
        'BFSNr':'first',
        'NAME': 'first',
        'typ_komm_1': lambda x: majority_ratio(x, av_grundnutz, "typ_komm_1", "Area_ratio"),
        'hauptnutzu': lambda x: majority_ratio(x, av_grundnutz, "hauptnutzu", "Area_ratio"),
        'hauptnut_1': lambda x: majority_ratio(x, av_grundnutz, 'hauptnut_1', "Area_ratio"),
        'Area':'first',
        'Area_split':'sum', # Area_split sum should be identical to Area
        'GASTW':'first',
        'GAREA':'first',
        'RGF':'first',
        'RGF_split':'sum',
        'AZ': lambda group: weighted_avg(group, av_grundnutz, "AZ", "Area_ratio"),
        'MGF':'sum',
        'MGF_Geo':'sum',
        'max_kap':'sum',
        'max_kap_geo':'sum',
        'AG': lambda group: weighted_avg(group, av_grundnutz, "AG", "Area_ratio"),
        'AG_geo': lambda group: weighted_avg(group, av_grundnutz, "AG_geo", "Area_ratio"),
        'theo_kap':'sum',
        'mob_kap':'sum',
        'typ_komm_1_SNP': 'first',
        'hauptnutzu_SNP': 'first'}
).reset_index()

capacity["AG_delta"] = capacity["AG"] - capacity["AG_geo"]

capacity["MGF_delta"] = capacity["MGF"] - capacity["MGF_Geo"]


capacity.loc[capacity["max_kap"] < 0, 'max_kap'] = 0
capacity.loc[capacity["max_kap_geo"] < 0, 'max_kap'] = 0
capacity.loc[capacity["mob_kap"] < 0, 'mob_kap'] = 0

print("size joined", len(capacity))
print("size split by zone", len(av_grundnutz))

# for col in av.columns:
#     print(col)

print(capacity.head())

capacity["Area_recalc"] = capacity.area

# remove patches smaller than 50m2
capacity = capacity[capacity["Area_recalc"] > 50]
print("size without small patches", len(capacity))

# remove streets and other non-functional areas
av_subtract = gpd.read_file(av_subtract_ds); print("AV subtract shapefile imported")
capacity = capacity[~capacity["EGRIS_EGRI"].isin(av_subtract["EGRIS_EGRI"])]
print("size without road/non-functional patches", len(capacity))

# print(capacity.geom_type.value_counts())

#%%

########## Capacity + STATENT + STATPOP

# capacity = gpd.read_file(capacity_export)
statent = gpd.read_file(statent_ds); print('STATENT shapefile imported')
# statent.plot(); plt.show()

# aggregating the number of employed on per plot basis
capacity_empfte = capacity.sjoin(statent, how="left", predicate="contains")
capacity['EMPFTE'] = capacity_empfte.groupby(capacity_empfte.index)['EMPFTE'].sum()

print(capacity['EMPFTE'].describe())

#%%
# from shapely.geometry import Point
# statpop['geometry'] = statpop.apply(lambda row: Point(row['longitude'], row['latitude']), axis=1)
# statpop_gdf = gpd.GeoDataFrame(statpop, geometry='geometry')

print("STATPOP import takes a LOOOONG TIME")
statpop = gpd.read_file(statpop_ds); print('STATPOP shapefile imported')


capacity_pop = capacity.sjoin(statpop, how="left", predicate="contains")
capacity_pop['pop_count'] = 1.0
capacity_pop.loc[capacity_pop["AGE"].isna(), "pop_count"] = 0
capacity_pop['AGE'] = capacity_pop['AGE'].astype(float)

capacity['pop_count'] = capacity_pop.groupby(capacity_pop.index)['pop_count'].sum()
capacity['popmeanAGE'] = capacity_pop.groupby(capacity_pop.index)['AGE'].mean()

capacity['person_tot'] = capacity['EMPFTE'] + capacity['pop_count']

capacity['person_ha'] = capacity['person_tot'] / (capacity['Area_recalc'] / 10000)  # personen/ha

dens_mean = capacity.groupby(capacity['typ_komm_1'])['person_ha'].mean().reset_index()
dens_mean = dens_mean.rename(columns={'person_ha': 'dens_mean'})

capacity = capacity.merge(dens_mean, on='typ_komm_1', how='left')

# capacity["NG_RGF"] = capacity["person_tot"] / (capacity["RGF"] / 60) * 100 # also include RGF=0 -> inf
capacity["NG"] = capacity["person_tot"] / ((capacity["MGF"] / 60) * 100 * 0.8)

condition_NG1 = capacity['hauptnutzu'] == 11
condition_NG2 = (capacity['hauptnutzu'] == 13) | (capacity['hauptnutzu'] == 14)
capacity.loc[condition_NG1, 'NG'] = capacity["person_tot"] / ( (capacity.loc[condition_NG1, 'MGF'] * KORREKTUR_WZ * KORREKTUR_AUSSCHOEPFUNG) / 60) * 100
capacity.loc[condition_NG2, 'NG'] = capacity["person_tot"] / ( (capacity.loc[condition_NG2, 'MGF'] * KORREKTUR_WZ * KORREKTUR_AUSSCHOEPFUNG) / 60) * 100

# person/plot area

cond1 = capacity['person_ha'] < capacity['dens_mean']
cond2 = capacity['AG'] < 50

# Create a new column with categories based on conditions
capacity['dens_cat'] = np.select([(cond1) & (cond2), (cond1) & (~cond2), (~cond1) & (cond2), (~cond1) & (~cond2)],
                           ['Low Person Density, Low AG', 'Low Person Density, High AG',
                            'High Person Density, Low AG', 'High Person Density, High AG'],
                           default='Undefined')

#%%

if EXPORT == 1:
    capacity.to_file(capacity_export, driver='ESRI Shapefile')
    print("\nCapacity calculation (shapefile) exported \n")
else:
    pass



