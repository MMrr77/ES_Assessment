import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, box

wozone_path = r"C:\Users\ruisma\Documents\MT\07-Regression\BDfootprint\01-Data\geodata\woZone.shp"
wozone = gpd.read_file(wozone_path)

# numeric
wozone['RGF_pred_f'] = pd.to_numeric(wozone['RGF_pred_f'], errors='coerce')
wozone['RGF_Probab'] = pd.to_numeric(wozone['RGF_Probab'], errors='coerce')

wozone = wozone.dropna(subset=['RGF_pred_f', 'RGF_Probab'])
wozone_sorted = wozone.sort_values(by='RGF_Probab', ascending=False)

sum_RGF = 0
selected_data = []

for index, row in wozone_sorted.iterrows():
    if sum_RGF >= 842050:
        break
    selected_data.append(row)
    sum_RGF += row['RGF_pred_f']

# Create a new GeoDataFrame from the selected data
selected_gdf = gpd.GeoDataFrame(selected_data)
selected_gdf.to_file('selected_areas.shp')

def create_rectangle_from_centroid(polygon, area):
    centroid = polygon.centroid
    # Assuming a square for simplicity, adjust this logic for different aspect ratios
    side_length = (area ** 0.5) / 2
    minx = centroid.x - side_length
    miny = centroid.y - side_length
    maxx = centroid.x + side_length
    maxy = centroid.y + side_length
    return box(minx, miny, maxx, maxy)

# Create a new GeoDataFrame to store the rectangles
rectangles = []

for idx, row in selected_gdf.iterrows():
    polygon = row['geometry']
    area = row['BDFT_pred']
    if polygon.is_valid and area > 0:
        rectangle = create_rectangle_from_centroid(polygon, area)
        rectangles.append({
            'geometry': rectangle,
            'BDFT_pred': area
        })

rectangles_gdf = gpd.GeoDataFrame(rectangles, crs=selected_gdf.crs)
rectangles_gdf.to_file('rectangles_from_centroids.shp')