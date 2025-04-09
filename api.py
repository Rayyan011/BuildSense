from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
import os

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/predict")
async def predict(request: Request):
    try:
        # Return a mock prediction with the structure expected by the frontend
        return {
            "prediction": "Café",
            "confidence_scores": {
                "Café": 0.85,
                "Clinic": 0.10,
                "Park": 0.03,
                "Residential": 0.02
            },
            "why": "Recommended 'Café' based on nearby features: cafes=3, groceries=1, schools=1, houses=8, parks=1, clinics=1, foot traffic=75, dist. to road=150m.",
            "features": {
                "nearby_cafes": 3,
                "nearby_groceries": 1,
                "nearby_schools": 1,
                "nearby_houses": 8,
                "nearby_parks": 1,
                "nearby_clinics": 1,
                "foot_traffic_score": 75,
                "distance_to_main_road": 150
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
