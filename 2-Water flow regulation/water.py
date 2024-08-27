import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt


def calculate_runoff(P, CN):
    """
    Calculate the water flow regulation (runoff) based on precipitation and curve number.

    Parameters:
    P (float): Precipitation in mm (kg/m²).
    CN (float): Curve Number (0-100).

    Returns:
    Q (float): Amount of runoff.
    """
    # Calculate S_0.20
    S_020 = (1000 / CN) - 10

    # Calculate S_0.05
    S_005 = 1.33 * (S_020 ** 1.15)

    # Calculate Q
    Q = ((P - 0.05 * S_005) ** 2) / (P + 0.95 * S_005)

    return Q


# Load shapefile
shapefile_path = 'path_to_your_shapefile.shp'
gdf = gpd.read_file(shapefile_path)

# Load CSV file containing CN values
csv_path = 'path_to_your_csv.csv'
df_cn = pd.read_csv(csv_path)

# Merge shapefile and CSV data
gdf = gdf.merge(df_cn, on='land_use_type')

# Define precipitation value
P = 50  # Example precipitation in mm

# Calculate runoff for each polygon
gdf['runoff'] = gdf['CN'].apply(lambda cn: calculate_runoff(P, cn))

# Plot the map
fig, ax = plt.subplots(1, 1, figsize=(12, 8))
gdf.plot(column='runoff', ax=ax, legend=True, cmap='Blues')
plt.title('Water Flow Regulation (Runoff)')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.show()
