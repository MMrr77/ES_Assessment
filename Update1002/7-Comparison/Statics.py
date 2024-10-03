import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def load_data(before_path, after_path):
    before_gdf = gpd.read_file(before_path)
    after_gdf = gpd.read_file(after_path)
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

def plot_histogram(before_data, after_data, column, title):
    plt.figure(figsize=(10, 6))
    plt.hist(before_data[column], bins=30, alpha=0.5, label='Before')
    plt.hist(after_data[column], bins=30, alpha=0.5, label='After')
    plt.title(title)
    plt.xlabel(column)
    plt.ylabel('Frequency')
    plt.legend()
    plt.show()

def calculate_sensitivity(merged_gdf, runoff_column, land_use_column):
    merged_gdf['runoff_change'] = merged_gdf[f'{runoff_column}_after'] - merged_gdf[f'{runoff_column}_before']
    merged_gdf['land_use_change'] = merged_gdf[f'{land_use_column}_after'] - merged_gdf[f'{land_use_column}_before']
    
    # Calculate sensitivity (change in runoff per unit change in land use)
    merged_gdf['sensitivity'] = merged_gdf['runoff_change'] / merged_gdf['land_use_change']
    
    # Handle division by zero
    merged_gdf['sensitivity'] = merged_gdf['sensitivity'].replace([np.inf, -np.inf], np.nan)
    
    return merged_gdf

# Main analysis
before_path = '/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/0-Data/7-CarbonSeq/CarSeq.shp'
after_path = '/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/Update1002/0-Data/7-CarbonSeq/CarSeq_pred.shp'
cc_column = 'Sequestrat'
land_use_column = 'Art'  # Assuming there's a column indicating land use type or intensity

# Load data
before_gdf, after_gdf = load_data(before_path, after_path)

# Calculate statistics
before_stats = calculate_statistics(before_gdf, runoff_column)
after_stats = calculate_statistics(after_gdf, runoff_column)

# Print results
print("Before scenario statistics:")
for key, value in before_stats.items():
    print(f"{key}: {value:.2f}")

print("\nAfter scenario statistics:")
for key, value in after_stats.items():
    print(f"{key}: {value:.2f}")

# Calculate and print overall change
total_change = after_stats['sum'] - before_stats['sum']
percent_change = (total_change / before_stats['sum']) * 100

print(f"\nTotal runoff change: {total_change:.2f}")
print(f"Percent change: {percent_change:.2f}%")

# Plot histogram
plot_histogram(before_gdf, after_gdf, runoff_column, 'Distribution of Runoff Values')

# Merge datasets and calculate sensitivity
merged = before_gdf.merge(after_gdf, on='fid_1', suffixes=('_before', '_after'))
merged = calculate_sensitivity(merged, runoff_column, land_use_column)

# Analyze sensitivity
print("\nSensitivity Analysis:")
print(f"Mean sensitivity: {merged['sensitivity'].mean():.4f}")
print(f"Median sensitivity: {merged['sensitivity'].median():.4f}")
print(f"Std deviation of sensitivity: {merged['sensitivity'].std():.4f}")

# Identify areas with high sensitivity
high_sensitivity = merged[abs(merged['sensitivity']) > merged['sensitivity'].abs().mean() + merged['sensitivity'].abs().std()]
print(f"\nNumber of areas with high sensitivity: {len(high_sensitivity)}")
print("Top 5 areas with highest sensitivity:")
print(high_sensitivity.sort_values('sensitivity', key=abs, ascending=False)[['fid_1', 'sensitivity', 'land_use_change', 'runoff_change']].head())

# Calculate average change in runoff per unit change in land use
avg_change_per_unit = merged['runoff_change'].sum() / merged['land_use_change'].sum()
print(f"\nAverage change in runoff per unit change in land use: {avg_change_per_unit:.4f}")

# Plot sensitivity vs land use change
plt.figure(figsize=(10, 6))
plt.scatter(merged['land_use_change'], merged['sensitivity'], alpha=0.5)
plt.title('Sensitivity vs Land Use Change')
plt.xlabel('Change in Land Use')
plt.ylabel('Sensitivity (Change in Runoff / Change in Land Use)')
plt.show()

# Export results
high_sensitivity.to_file('/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/Update1002/0-Data/4-Runoff/high_sensitivity_areas.shp')
merged.to_file('/Users/rrs/Library/CloudStorage/OneDrive-KTH/KTH/SUPD/0-Degree Project/02-All Codes/ES_Assessment/Update1002/0-Data/4-Runoff/runoff_sensitivity_analysis.shp')
