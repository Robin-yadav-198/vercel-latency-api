from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load data function
def load_data():
    try:
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_file = os.path.join(current_dir, "q-vercel-latency.json")
        
        print(f"Looking for data file at: {data_file}")
        
        with open(data_file, 'r') as f:
            data = json.load(f)
            print(f"Successfully loaded {len(data)} records")
            return data
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return []

# Load data when the app starts
telemetry_data = load_data()

@app.get("/")
async def root():
    return {
        "message": "Latency Analytics API", 
        "status": "running",
        "data_records": len(telemetry_data)
    }

@app.post("/api/")
async def analyze_latency(request: Request):
    try:
        # Get request data
        body = await request.json()
        regions = body.get("regions", [])
        threshold = body.get("threshold_ms", 180)
        
        print(f"Processing regions: {regions}, threshold: {threshold}")
        
        results = []
        
        for region in regions:
            # Filter data for the region
            region_data = [item for item in telemetry_data if item.get("region") == region]
            
            if region_data:
                # Extract values
                latencies = [item["latency_ms"] for item in region_data]
                uptimes = [item["uptime_pct"] for item in region_data]
                
                # Calculate statistics
                avg_latency = round(sum(latencies) / len(latencies), 2)
                
                # Calculate 95th percentile
                sorted_latencies = sorted(latencies)
                index_95 = int(0.95 * len(sorted_latencies))
                p95_latency = round(sorted_latencies[index_95], 2)
                
                avg_uptime = round(sum(uptimes) / len(uptimes), 3)
                breaches = sum(1 for latency in latencies if latency > threshold)
                
                results.append({
                    "region": region,
                    "avg_latency": avg_latency,
                    "p95_latency": p95_latency,
                    "avg_uptime": avg_uptime,
                    "breaches": breaches
                })
            else:
                # Region not found
                results.append({
                    "region": region,
                    "avg_latency": 0,
                    "p95_latency": 0,
                    "avg_uptime": 0,
                    "breaches": 0,
                    "error": "Region not found"
                })
        
        return {"regions": results}
        
    except Exception as e:
        return {"error": str(e), "regions": []}
