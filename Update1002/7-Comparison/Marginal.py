

import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt

def load_data(before_path, after_path):
    before_gdf = gpd.read_file(before_path)
    after_gdf = gpd.read_file(after_path)
    
    # Create unique IDs for each dataset
    before_gdf['unique_id'] = range(1, len(before_gdf) + 1)
    after_gdf['unique_id'] = range(1, len(after_gdf) + 1)
    
    return before_gdf, after_gdf

def calculate_statistics(gdf, column):
    return {
        'mean': gdf[column].mean(),
        'median': gdf[column].median(),
        'std': gdf[column].std(),
        'min': gdf[column].min(),
        'max': gdf[column].max(),
        'sum': gdf[column].sum()
    }

def plot_histogram(data, column, title):
    plt.figure(figsize=(10, 6))
    plt.hist(data, bins=30, alpha=0.7)
    plt.title(title)
    plt.xlabel(column)
    plt.ylabel('Frequency')
    plt.show()

# Main analysis
before_path = '/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/5-Airquality/DepositedAmount.shp'
after_path = '/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/Update1002/0-Data/5-Airquality/DeposiAmount_pred.shp'
cc_column = 'DeposiAmou'

# Load data
before_gdf, after_gdf = load_data(before_path, after_path)

# Ensure the geometries are valid
before_gdf['geometry'] = before_gdf.geometry.buffer(0)
after_gdf['geometry'] = after_gdf.geometry.buffer(0)

# Spatial join instead of merge
merged = gpd.sjoin(before_gdf, after_gdf, how="inner", predicate="intersects")

# Calculate area (assuming the CRS is in meters)
merged['area'] = merged.geometry.area / 10000  # Convert to hectares

# Calculate change in cooling capacity
merged['cc_change'] = merged[f'{cc_column}_right'] - merged[f'{cc_column}_left']

# Calculate marginal change (change per hectare)
merged['marginal_cc_change'] = merged['cc_change'] / merged['area']

# Calculate statistics for marginal change
marginal_stats = calculate_statistics(merged, 'marginal_cc_change')

# Print results
print("Marginal Cooling Capacity Change Statistics (per hectare):")
for key, value in marginal_stats.items():
    print(f"{key}: {value:.4f}")

# Calculate and print overall change
total_change = merged['cc_change'].sum()
total_area = merged['area'].sum()
average_marginal_change = total_change / total_area

print(f"\nTotal Cooling Capacity change: {total_change:.2f}")
print(f"Total area: {total_area:.2f} hectares")
print(f"Average marginal change: {average_marginal_change:.4f} per hectare")

# Plot histogram of marginal changes
plot_histogram(merged['marginal_cc_change'], 'Marginal CC Change', 'Distribution of Marginal Cooling Capacity Changes')

# Identify areas with significant marginal change
significant_change = merged[abs(merged['marginal_cc_change']) > abs(merged['marginal_cc_change']).mean() + abs(merged['marginal_cc_change']).std()]

print(f"\nNumber of areas with significant marginal change: {len(significant_change)}")
print("Top 5 areas with highest marginal change:")
print(significant_change.sort_values('marginal_cc_change', key=abs, ascending=False)[['unique_id_left', 'marginal_cc_change']].head())

# Export results
merged.to_file('/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/Update1002/0-Data/8-Temperature/marginal_cc_change.shp')
significant_change.to_file('/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/Update1002/0-Data/8-Temperature/significant_marginal_cc_change.shp')