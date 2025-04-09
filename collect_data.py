import overpass
import pandas as pd
import numpy as np
import time
import math
import os
from dotenv import load_dotenv
from typing import Dict, List, Tuple
import random

load_dotenv()  # Load environment variables if you have a .env file

# --- Constants ---
HULHUMALE_BOUNDS = {
    "min_lat": 4.2090,  # Southern boundary
    "max_lat": 4.2400,  # Northern boundary
    "min_lon": 73.5350, # Western boundary
    "max_lon": 73.5450  # Eastern boundary
}
GRID_SPACING = 0.0005  # Approximately 50 meters
POI_RADIUS_METERS = 200
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# POI types to query (Map features: https://wiki.openstreetmap.org/wiki/Map_features)
POI_QUERIES = {
    "cafes": '(node["amenity"="cafe"](around:{radius},{lat},{lon});way["amenity"="cafe"](around:{radius},{lat},{lon});relation["amenity"="cafe"](around:{radius},{lat},{lon}));out count;',
    "groceries": '(node["shop"~"convenience|supermarket"](around:{radius},{lat},{lon});way["shop"~"convenience|supermarket"](around:{radius},{lat},{lon});relation["shop"~"convenience|supermarket"](around:{radius},{lat},{lon}));out count;',
    "schools": '(node["amenity"="school"](around:{radius},{lat},{lon});way["amenity"="school"](around:{radius},{lat},{lon});relation["amenity"="school"](around:{radius},{lat},{lon}));out count;',
    "houses": '(node["building"~"house|residential|apartments"](around:{radius},{lat},{lon});way["building"~"house|residential|apartments"](around:{radius},{lat},{lon});relation["building"~"house|residential|apartments"](around:{radius},{lat},{lon}));out count;',
    "parks": '(node["leisure"="park"](around:{radius},{lat},{lon});way["leisure"="park"](around:{radius},{lat},{lon});relation["leisure"="park"](around:{radius},{lat},{lon}));out count;',
    "clinics": '(node["amenity"~"clinic|doctors"](around:{radius},{lat},{lon});way["amenity"~"clinic|doctors"](around:{radius},{lat},{lon});relation["amenity"~"clinic|doctors"](around:{radius},{lat},{lon}));out count;'
}

OUTPUT_CSV = "hulhumale_poi_data.csv"

# --- Helper Functions ---

def meters_to_degrees_lat(meters):
    """Approximate conversion for latitude."""
    return meters / 111111.0

def meters_to_degrees_lon(meters, latitude):
    """Approximate conversion for longitude, depends on latitude."""
    return meters / (111111.0 * math.cos(math.radians(latitude)))

def generate_grid_points() -> List[Tuple[float, float]]:
    """Generate a grid of points within Hulhumalé bounds."""
    points = []
    lat = HULHUMALE_BOUNDS['min_lat']
    while lat <= HULHUMALE_BOUNDS['max_lat']:
        lon = HULHUMALE_BOUNDS['min_lon']
        while lon <= HULHUMALE_BOUNDS['max_lon']:
            points.append((lat, lon))
            lon += GRID_SPACING
        lat += GRID_SPACING
    return points

def query_overpass(lat: float, lon: float, radius: int, poi_queries: Dict[str, str]) -> Dict[str, int]:
    """Query Overpass API for POIs around a point."""
    api = overpass.API(endpoint=OVERPASS_URL, timeout=60)
    poi_counts = {f"nearby_{key}": 0 for key in poi_queries.keys()}
    print(f"Querying Overpass for ({lat:.5f}, {lon:.5f})...")

    for key, query_template in poi_queries.items():
        try:
            query = query_template.format(radius=radius, lat=lat, lon=lon)
            response = api.get(query, responseformat="json")
            
            if response and 'elements' in response:
                for element in response['elements']:
                    if element.get('type') == 'count':
                        poi_counts[f"nearby_{key}"] = int(element.get('tags', {}).get('total', 0))
            
            time.sleep(2)  # Be nice to the API
        except Exception as e:
            print(f"Error querying {key}: {e}")
            time.sleep(5)  # Longer wait on error
            continue

    print(f"  Finished queries for ({lat:.5f}, {lon:.5f}). Counts: {poi_counts}")
    return poi_counts

def simulate_features() -> Dict[str, float]:
    """Simulate additional features that would come from other data sources."""
    return {
        'foot_traffic_score': random.randint(1, 101),  # 1-100 score
        'distance_to_main_road': random.uniform(10, 500)  # 10-500 meters
    }

def label_point(features: Dict[str, float]) -> str:
    """
    Label a point based on its features using simple heuristics.
    This could be replaced with more sophisticated logic or real data.
    """
    # Extract relevant counts
    cafes = features.get('nearby_cafes', 0)
    parks = features.get('nearby_parks', 0)
    clinics = features.get('nearby_clinics', 0)
    houses = features.get('nearby_houses', 0)
    foot_traffic = features.get('foot_traffic_score', 0)
    
    # Simple decision tree for labeling
    if cafes >= 2 and foot_traffic > 70:
        return 'Café'
    elif parks >= 1 and houses <= 5:
        return 'Park'
    elif clinics >= 1 and foot_traffic > 50:
        return 'Clinic'
    else:
        return 'Residential'

# --- Main Execution ---
if __name__ == "__main__":
    # Generate grid points
    points = generate_grid_points()
    print(f"Generated {len(points)} grid points.")
    
    # Collect data for each point
    data = []
    for lat, lon in points:
        # Get POI counts from Overpass
        poi_counts = query_overpass(lat, lon, POI_RADIUS_METERS, POI_QUERIES)
        
        # Add simulated features
        features = {**poi_counts, **simulate_features()}
        
        # Label the point
        label = label_point(features)
        
        # Add to dataset
        data.append({
            'latitude': lat,
            'longitude': lon,
            'label': label,
            **features
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    df.to_csv(OUTPUT_CSV, index=False)
    print("\nData collection complete!")
    print("Sample data:")
    print(df.head())
    label_distribution = df['label'].value_counts()
    print(f"Label distribution: {label_distribution}")
