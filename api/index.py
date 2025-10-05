from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from pathlib import Path
import json

app = FastAPI()

# Enable CORS for all origins - this allows your API to be called from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods, including POST
    allow_headers=["*"],  # Allows all headers
)

# Load the dataset when the app starts
# We use pathlib to ensure we find the file correctly
DATA_FILE = Path(__file__).parent / "q-vercel-latency.json"

# Load the JSON data into a pandas DataFrame for easy analysis
try:
    df = pd.read_json(DATA_FILE)
    print(f"Successfully loaded data with {len(df)} records")
except Exception as e:
    print(f"Error loading data: {e}")
    df = pd.DataFrame()  # Empty dataframe as fallback

@app.get("/")
async def root():
    """Simple health check endpoint"""
    return {
        "message": "Latency Analytics API is running", 
        "status": "healthy",
        "data_records": len(df) if not df.empty else 0
    }

@app.post("/api/")
async def analyze_latency(request: Request):
    """
    Main analytics endpoint
    Expected JSON payload:
    {
        "regions": ["apac", "amer", "emea"],
        "threshold_ms": 180
    }
    """
    try:
        # Get the JSON data from the request
        payload = await request.json()
        
        # Extract regions and threshold from the payload
        regions_to_process = payload.get("regions", [])
        threshold = payload.get("threshold_ms", 200)
        
        print(f"Processing regions: {regions_to_process} with threshold: {threshold}ms")
        
        # If no regions specified, return empty result
        if not regions_to_process:
            return {"regions": []}
        
        # If we failed to load data, return error
        if df.empty:
            return {"error": "Data not available", "regions": []}
        
        results = []
        
        # Calculate statistics for each requested region
        for region in regions_to_process:
            # Filter data for the current region
            region_data = df[df["region"] == region]
            
            if not region_data.empty:
                # Calculate average latency
                avg_latency = round(region_data["latency_ms"].mean(), 2)
                
                # Calculate 95th percentile latency
                p95_latency = round(np.percentile(region_data["latency_ms"], 95), 2)
                
                # Calculate average uptime percentage
                avg_uptime = round(region_data["uptime_pct"].mean(), 3)
                
                # Count how many records exceed the threshold
                breaches = int(region_data[region_data["latency_ms"] > threshold].shape[0])
                
                # Add to results
                results.append({
                    "region": region,
                    "avg_latency": avg_latency,
                    "p95_latency": p95_latency,
                    "avg_uptime": avg_uptime,
                    "breaches": breaches,
                })
            else:
                # Region not found in data
                results.append({
                    "region": region,
                    "avg_latency": 0,
                    "p95_latency": 0,
                    "avg_uptime": 0,
                    "breaches": 0,
                    "error": "Region not found in data"
                })
        
        return {"regions": results}
        
    except Exception as e:
        # Return error if something goes wrong
        return {"error": f"Processing failed: {str(e)}", "regions": []}
