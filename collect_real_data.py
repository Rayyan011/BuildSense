import pandas as pd
import numpy as np
import requests
import time
import json
import random
from typing import Dict, List, Tuple
import os
from datetime import datetime

# Constants
HULHUMALE_BOUNDS = {
    'min_lat': 4.2090,  # Southern boundary
    'max_lat': 4.2400,  # Northern boundary 
    'min_lon': 73.5350, # Western boundary
    'max_lon': 73.5450  # Eastern boundary
}

GRID_SPACING = 0.001   # Approximately 100 meters - fewer points for API kindness
POI_RADIUS_METERS = 200
OUTPUT_CSV = "hulhumale_real_data.csv"
CACHE_DIR = "overpass_cache"
OVERPASS_ENDPOINT = "https://overpass-api.de/api/interpreter"
MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

# Fixed POI queries with correct syntax
POI_CATEGORIES = {
    "cafes": '[out:json];(node["amenity"="cafe"](around:{radius},{lat},{lon});way["amenity"="cafe"](around:{radius},{lat},{lon});relation["amenity"="cafe"](around:{radius},{lat},{lon});node["amenity"="restaurant"](around:{radius},{lat},{lon});way["amenity"="restaurant"](around:{radius},{lat},{lon});relation["amenity"="restaurant"](around:{radius},{lat},{lon}));out count;',
    
    "groceries": '[out:json];(node["shop"~"convenience|supermarket|grocery"](around:{radius},{lat},{lon});way["shop"~"convenience|supermarket|grocery"](around:{radius},{lat},{lon});relation["shop"~"convenience|supermarket|grocery"](around:{radius},{lat},{lon}));out count;',
    
    "schools": '[out:json];(node["amenity"~"school|kindergarten|college|university"](around:{radius},{lat},{lon});way["amenity"~"school|kindergarten|college|university"](around:{radius},{lat},{lon});relation["amenity"~"school|kindergarten|college|university"](around:{radius},{lat},{lon}));out count;',
    
    "houses": '[out:json];(node["building"~"house|residential|apartments"](around:{radius},{lat},{lon});way["building"~"house|residential|apartments"](around:{radius},{lat},{lon});relation["building"~"house|residential|apartments"](around:{radius},{lat},{lon}));out count;',
    
    "parks": '[out:json];(node["leisure"~"park|garden"](around:{radius},{lat},{lon});way["leisure"~"park|garden"](around:{radius},{lat},{lon});relation["leisure"~"park|garden"](around:{radius},{lat},{lon}));out count;',
    
    "clinics": '[out:json];(node["amenity"~"clinic|doctors|hospital|pharmacy"](around:{radius},{lat},{lon});way["amenity"~"clinic|doctors|hospital|pharmacy"](around:{radius},{lat},{lon});relation["amenity"~"clinic|doctors|hospital|pharmacy"](around:{radius},{lat},{lon}));out count;'
}

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

def get_cache_filename(lat: float, lon: float, category: str) -> str:
    """Generate a cache filename for a specific location and category."""
    return os.path.join(CACHE_DIR, f"{lat:.5f}_{lon:.5f}_{category}.json")

def is_cached(lat: float, lon: float, category: str) -> bool:
    """Check if a query result is already cached."""
    cache_file = get_cache_filename(lat, lon, category)
    return os.path.exists(cache_file)

def get_from_cache(lat: float, lon: float, category: str) -> Dict:
    """Get query result from cache."""
    cache_file = get_cache_filename(lat, lon, category)
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading cache: {e}")
        return None

def save_to_cache(lat: float, lon: float, category: str, data: Dict):
    """Save query result to cache."""
    cache_file = get_cache_filename(lat, lon, category)
    try:
        with open(cache_file, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving to cache: {e}")

def query_overpass(lat: float, lon: float, category: str, query_template: str) -> int:
    """Query Overpass API with retry logic and caching."""
    # Check cache first
    if is_cached(lat, lon, category):
        print(f"Using cached data for {category} at ({lat:.5f}, {lon:.5f})")
        result = get_from_cache(lat, lon, category)
        return result['count'] if result else 0
    
    query = query_template.format(radius=POI_RADIUS_METERS, lat=lat, lon=lon)
    
    for attempt in range(MAX_RETRIES):
        try:
            print(f"Querying Overpass for {category} at ({lat:.5f}, {lon:.5f}) - attempt {attempt+1}")
            response = requests.post(OVERPASS_ENDPOINT, data=query, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                count = 0
                if data and 'elements' in data:
                    for element in data['elements']:
                        if element.get('type') == 'count':
                            count += int(element.get('tags', {}).get('total', 0))
                
                result = {'count': count, 'timestamp': datetime.now().isoformat()}
                save_to_cache(lat, lon, category, result)
                
                print(f"  Found {count} {category} at ({lat:.5f}, {lon:.5f})")
                return count
            elif response.status_code == 429 or response.status_code >= 500:
                # Rate limited or server error - retry after delay
                wait_time = RETRY_DELAY * (attempt + 1)
                print(f"  Rate limited or server error (status {response.status_code}). Waiting {wait_time}s before retry.")
                time.sleep(wait_time)
            else:
                # Other error
                print(f"  Error: {response.status_code} - {response.text}")
                break
                
        except Exception as e:
            print(f"  Exception during query: {e}")
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_DELAY * (attempt + 1)
                print(f"  Waiting {wait_time}s before retry.")
                time.sleep(wait_time)
            else:
                print(f"  Max retries reached for {category} at ({lat:.5f}, {lon:.5f})")
                break
    
    # If we get here, all retries failed
    result = {'count': 0, 'timestamp': datetime.now().isoformat()}
    save_to_cache(lat, lon, category, result)
    return 0

def query_all_categories(lat: float, lon: float) -> Dict[str, int]:
    """Query all POI categories for a point."""
    results = {}
    
    for category, query_template in POI_CATEGORIES.items():
        count = query_overpass(lat, lon, category, query_template)
        results[f"nearby_{category}"] = count
        # Be nice to the API - delay between categories
        time.sleep(2)  
        
    return results

def estimate_foot_traffic(features: Dict[str, int]) -> int:
    """
    Estimate foot traffic based on POI density.
    This is a simplified model - in reality, this would come from actual 
    pedestrian count data, mobile phone movement data, etc.
    """
    base_score = 30  # Base foot traffic score
    
    # More POIs generally means more foot traffic
    poi_factor = (
        features.get("nearby_cafes", 0) * 15 +
        features.get("nearby_groceries", 0) * 12 +
        features.get("nearby_schools", 0) * 20 +
        features.get("nearby_houses", 0) * 0.5 +  # Houses add less foot traffic per unit
        features.get("nearby_parks", 0) * 10 +
        features.get("nearby_clinics", 0) * 15
    )
    
    # Add some randomness
    random_factor = random.uniform(0.8, 1.2)
    
    score = int(min(100, max(1, base_score + poi_factor * random_factor)))
    return score

def estimate_distance_to_main_road(lat: float, lon: float) -> float:
    """
    Estimate distance to nearest main road in meters.
    In a real application, this would use actual road network data.
    For this example, we'll simulate based on location.
    """
    # Define some approximate "main roads" in Hulhumalé
    # These are just for simulation - not actual precise locations
    
    # Nirolhu Magu runs north-south in the west side
    west_road_lon = 73.5365
    
    # Ranauraa Magu runs north-south in the east side
    east_road_lon = 73.5435
    
    # Central east-west roads at different latitudes
    central_roads_lat = [4.215, 4.225, 4.235]
    
    # Calculate distances to each road
    dist_to_west = abs(lon - west_road_lon) * 111320  # Convert degrees to meters
    dist_to_east = abs(lon - east_road_lon) * 111320
    
    dist_to_central = min([abs(lat - central_lat) * 111320 for central_lat in central_roads_lat])
    
    # Return the minimum distance
    min_dist = min(dist_to_west, dist_to_east, dist_to_central)
    
    # Add some noise
    noise = random.uniform(0.8, 1.2)
    
    return max(10, min(500, min_dist * noise))  # Constrain between 10-500m

def label_point(features: Dict) -> str:
    """
    Apply realistic labeling logic based on features.
    """
    cafes = features.get("nearby_cafes", 0)
    groceries = features.get("nearby_groceries", 0)
    schools = features.get("nearby_schools", 0)
    houses = features.get("nearby_houses", 0)
    parks = features.get("nearby_parks", 0)
    clinics = features.get("nearby_clinics", 0)
    foot_traffic = features.get("foot_traffic_score", 0)
    road_distance = features.get("distance_to_main_road", 500)
    
    # More sophisticated decision logic based on multiple factors
    
    # Café areas - high foot traffic, close to roads, some houses around
    if (cafes >= 1 or groceries >= 1) and foot_traffic > 60 and road_distance < 100:
        return "Café"
    
    # Park areas - existing parks or low housing density and not too close to main roads
    elif parks >= 1 or (houses <= 5 and road_distance > 150):
        return "Park"
    
    # Clinic areas - existing clinics, medium foot traffic, accessible from roads
    elif clinics >= 1 or (foot_traffic > 40 and road_distance < 120 and houses > 8):
        return "Clinic"
    
    # Residential - default, especially where there are already houses
    else:
        return "Residential"

if __name__ == "__main__":
    # Generate grid points
    points = generate_grid_points()
    print(f"Generated {len(points)} grid points.")
    
    # Collect data for each point
    data = []
    for i, (lat, lon) in enumerate(points):
        print(f"\nProcessing point {i+1}/{len(points)}: ({lat:.5f}, {lon:.5f})")
        
        # Query POI data from Overpass API
        poi_data = query_all_categories(lat, lon)
        
        # Estimate additional features
        foot_traffic = estimate_foot_traffic(poi_data)
        road_distance = estimate_distance_to_main_road(lat, lon)
        
        # Combine all features
        features = {
            **poi_data, 
            "foot_traffic_score": foot_traffic,
            "distance_to_main_road": road_distance
        }
        
        # Apply labeling
        label = label_point(features)
        
        # Add to dataset
        data.append({
            "latitude": lat,
            "longitude": lon,
            "label": label,
            **features
        })
        
        # Save intermediate data periodically
        if (i + 1) % 5 == 0 or i == len(points) - 1:
            print(f"Saving intermediate data after {i+1} points...")
            intermediate_df = pd.DataFrame(data)
            intermediate_df.to_csv(f"{OUTPUT_CSV}.intermediate", index=False)
    
    # Create final DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    df.to_csv(OUTPUT_CSV, index=False)
    print("\nData collection complete!")
    print("Sample data:")
    print(df.head())
    label_distribution = df['label'].value_counts()
    print(f"Label distribution: {label_distribution}") 