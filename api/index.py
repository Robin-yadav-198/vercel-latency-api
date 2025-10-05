from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os

app = FastAPI()

# CORS configuration - THIS MUST COME FIRST
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# Load data
def load_data():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_file = os.path.join(current_dir, "q-vercel-latency.json")
        with open(data_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        return []

telemetry_data = load_data()

@app.get("/")
async def root():
    return {
        "message": "Latency Analytics API", 
        "status": "running",
        "data_records": len(telemetry_data)
    }

@app.post("/api/")
async def analyze_latency(request: dict):
    try:
        regions = request.get("regions", [])
        threshold = request.get("threshold_ms", 180)
        
        results = []
        
        for region in regions:
            region_data = [item for item in telemetry_data if item.get("region") == region]
            
            if region_data:
                latencies = [item["latency_ms"] for item in region_data]
                uptimes = [item["uptime_pct"] for item in region_data]
                
                avg_latency = round(sum(latencies) / len(latencies), 2)
                
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
        
        return {"regions": results}
        
    except Exception as e:
        return {"error": str(e)}
