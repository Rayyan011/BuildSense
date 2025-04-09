import pandas as pd
import numpy as np
import random
from typing import Dict, List, Tuple

# Constants
HULHUMALE_BOUNDS = {
    'min_lat': 4.2090,  # Southern boundary
    'max_lat': 4.2400,  # Northern boundary
    'min_lon': 73.5350, # Western boundary
    'max_lon': 73.5450  # Eastern boundary
}

GRID_SPACING = 0.0005  # Approximately 50 meters
OUTPUT_CSV = "hulhumale_poi_data.csv"

# Feature categories
POI_FEATURES = ["nearby_cafes", "nearby_groceries", "nearby_schools", 
                "nearby_houses", "nearby_parks", "nearby_clinics"]

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

def generate_feature_values(lat: float, lon: float) -> Dict[str, int]:
    """
    Generate synthetic feature values based on position.
    We'll use the coordinates to determine feature density, creating
    patterns in different areas of the map.
    """
    # Normalize coordinates to 0-1 range for the bounded area
    norm_lat = (lat - HULHUMALE_BOUNDS['min_lat']) / (HULHUMALE_BOUNDS['max_lat'] - HULHUMALE_BOUNDS['min_lat'])
    norm_lon = (lon - HULHUMALE_BOUNDS['min_lon']) / (HULHUMALE_BOUNDS['max_lon'] - HULHUMALE_BOUNDS['min_lon'])
    
    # Create spatial patterns
    # North area (high lat): more cafes
    # East area (high lon): more houses
    # Central area: more parks
    # South area: more clinics
    # West area: more schools
    
    center_lat = (HULHUMALE_BOUNDS['min_lat'] + HULHUMALE_BOUNDS['max_lat']) / 2
    center_lon = (HULHUMALE_BOUNDS['min_lon'] + HULHUMALE_BOUNDS['max_lon']) / 2
    dist_from_center = np.sqrt((lat - center_lat)**2 + (lon - center_lon)**2)
    
    # Base values with some randomness
    cafes = int(3 * norm_lat + random.randint(0, 2))
    groceries = int(2 * (1 - norm_lon) + random.randint(0, 2))
    schools = int(3 * (1 - norm_lat) * (1 - norm_lon) + random.randint(0, 1))
    houses = int(15 * norm_lon + random.randint(5, 15))
    parks = int(3 * (1 - dist_from_center * 10) + random.randint(0, 1))
    clinics = int(2 * (1 - norm_lat) + random.randint(0, 1))
    
    # Ensure non-negative values
    return {
        "nearby_cafes": max(0, cafes),
        "nearby_groceries": max(0, groceries),
        "nearby_schools": max(0, schools),
        "nearby_houses": max(0, houses),
        "nearby_parks": max(0, parks),
        "nearby_clinics": max(0, clinics)
    }

def generate_additional_features() -> Dict[str, float]:
    """Generate additional features with random values."""
    return {
        'foot_traffic_score': random.randint(1, 101),  # 1-100 score
        'distance_to_main_road': random.uniform(10, 500)  # 10-500 meters
    }

def label_point(features: Dict[str, float]) -> str:
    """
    Label a point based on its features using simple heuristics.
    This matches the logic in collect_data.py.
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

if __name__ == "__main__":
    # Generate grid points
    points = generate_grid_points()
    print(f"Generated {len(points)} grid points.")
    
    # Generate synthetic data
    data = []
    for i, (lat, lon) in enumerate(points):
        # Generate feature values
        poi_counts = generate_feature_values(lat, lon)
        additional_features = generate_additional_features()
        
        # Combine features
        features = {**poi_counts, **additional_features}
        
        # Label the point
        label = label_point(features)
        
        # Add to dataset
        data.append({
            'latitude': lat,
            'longitude': lon,
            'label': label,
            **features
        })
        
        # Print progress
        if (i + 1) % 100 == 0:
            print(f"Generated data for {i + 1}/{len(points)} points...")
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    df.to_csv(OUTPUT_CSV, index=False)
    print("\nData generation complete!")
    print("Sample data:")
    print(df.head())
    label_distribution = df['label'].value_counts()
    print(f"Label distribution: {label_distribution}") 