import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import time
import uvicorn
import os
import json
import hashlib
from datetime import datetime, timedelta
import random

# --- Constants ---
POI_RADIUS_METERS = 200
HULHUMALE_BOUNDS = {
    'min_lat': 4.2090,  # Southern boundary
    'max_lat': 4.2400,  # Northern boundary
    'min_lon': 73.5350, # Western boundary
    'max_lon': 73.5450  # Eastern boundary
}

# Features expected by the model (ensure order matches training)
MODEL_FEATURES = [
    'nearby_cafes', 'nearby_groceries', 'nearby_schools',
    'nearby_houses', 'nearby_parks', 'nearby_clinics',
    'foot_traffic_score', 'distance_to_main_road'
]
MODEL_PATH = "model.pkl"

# Cache settings
CACHE_DIR = "cache"
CACHE_EXPIRY_HOURS = 24  # Cache entries expire after 24 hours

# --- Cache Functions ---
def get_cache_key(lat: float, lon: float) -> str:
    """Generate a unique cache key for a location."""
    # Round coordinates to 5 decimal places to group nearby points
    lat_rounded = round(lat, 5)
    lon_rounded = round(lon, 5)
    key_string = f"{lat_rounded}_{lon_rounded}"
    return hashlib.md5(key_string.encode()).hexdigest()

def get_cached_data(cache_key: str) -> dict:
    """Retrieve cached data if it exists and hasn't expired."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
            # Check if cache has expired
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cache_time > timedelta(hours=CACHE_EXPIRY_HOURS):
                return None
            return cache_data['data']
    except Exception as e:
        print(f"Error reading cache: {e}")
        return None

def save_to_cache(cache_key: str, data: dict):
    """Save data to cache with timestamp."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    try:
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
    except Exception as e:
        print(f"Error saving to cache: {e}")

# --- Synthetic Data Generation Function ---
def generate_feature_values(lat: float, lon: float) -> dict:
    """
    Generate synthetic feature values based on position.
    This matches the function in generate_synthetic_data.py
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

def generate_additional_features() -> dict:
    """Generate additional features with random values."""
    return {
        'foot_traffic_score': random.randint(1, 101),  # 1-100 score
        'distance_to_main_road': random.uniform(10, 500)  # 10-500 meters
    }

def get_features_for_point(lat: float, lon: float) -> dict:
    """Get features for a point, using cache if available."""
    cache_key = get_cache_key(lat, lon)
    
    # Try to get data from cache first
    cached_data = get_cached_data(cache_key)
    if cached_data is not None:
        print(f"Using cached data for ({lat:.5f}, {lon:.5f})")
        return cached_data
    
    # If not in cache, generate synthetic data
    print(f"Generating synthetic data for ({lat:.5f}, {lon:.5f})...")
    poi_counts = generate_feature_values(lat, lon)
    additional_features = generate_additional_features()
    features = {**poi_counts, **additional_features}
    
    # Save to cache before returning
    save_to_cache(cache_key, features)
    print(f"  Generated data: {features}")
    return features

# --- FastAPI Setup ---
app = FastAPI(title="BuildSense API")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")
# Setup templates
templates = Jinja2Templates(directory="templates")

# --- Load Model ---
model_data = None
model = None
label_classes = None
if os.path.exists(MODEL_PATH):
    try:
        model_data = joblib.load(MODEL_PATH)
        model = model_data['model']
        label_classes = model_data['label_classes']
        print(f"Model loaded successfully from {MODEL_PATH}")
        print(f"Label classes: {label_classes}")
    except Exception as e:
        print(f"Error loading model: {e}")
        model = None # Ensure model is None if loading fails
else:
    print(f"Warning: Model file not found at {MODEL_PATH}. /predict endpoint will not work.")

# --- Pydantic Models ---
class PredictRequest(BaseModel):
    lat: float
    lon: float

class PredictResponse(BaseModel):
    prediction: str
    confidence_scores: dict[str, float]
    why: str
    features: dict # Return the features used for prediction

# --- API Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/predict", response_model=PredictResponse)
async def predict_development(request: PredictRequest):
    """Predicts the best development type for a given lat/lon."""
    if not model or label_classes is None:
        raise HTTPException(status_code=500, detail="Model not loaded. Cannot make predictions.")

    lat = request.lat
    lon = request.lon

    # Get features using synthetic data generation (using cache if available)
    features = get_features_for_point(lat, lon)

    # Ensure all required features are present, fill missing with 0
    input_data = {}
    for feature_name in MODEL_FEATURES:
        input_data[feature_name] = features.get(feature_name, 0)

    # Create DataFrame in the correct column order for the model
    input_df = pd.DataFrame([input_data], columns=MODEL_FEATURES)

    # Predict using the loaded model
    try:
        prediction_idx = model.predict(input_df)[0]
        probabilities = model.predict_proba(input_df)[0]
    except Exception as e:
        print(f"Error during prediction: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed.")

    # Format the response
    prediction_label = label_classes[prediction_idx]
    confidence_scores = {label: float(prob) for label, prob in zip(label_classes, probabilities)}

    # Generate a simple explanation
    explanation = f"Recommended '{prediction_label}' based on nearby features: "
    explanation += ", ".join([f"{k.replace('nearby_','')}={v}" for k, v in features.items() if k.startswith('nearby_')])
    explanation += f", foot traffic={features['foot_traffic_score']}"
    explanation += f", dist. to road={features['distance_to_main_road']:.0f}m."

    return PredictResponse(
        prediction=prediction_label,
        confidence_scores=confidence_scores,
        why=explanation,
        features=input_data
    )

# --- Run the API ---
if __name__ == "__main__":
    # Check if model exists before starting
    if not model:
        print("ERROR: Model could not be loaded. API starting but /predict will fail.")
        print(f"Ensure '{MODEL_PATH}' exists and is valid. Run train_model.py.")
    # Use uvicorn to run the app
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
