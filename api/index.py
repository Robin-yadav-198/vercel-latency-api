from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os

app = FastAPI()

# Enhanced CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Load data function
def load_data():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_file = os.path.join(current_dir, "q-vercel-latency.json")
        with open(data_file, 'r') as f:
            data = json.load(f)
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

# Add explicit OPTIONS handler for CORS preflight
@app.options("/api/")
async def options_api():
    return JSONResponse(
        content={"message": "CORS preflight"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@app.post("/api/")
async def analyze_latency(request: Request):
    try:
        # Add CORS headers to response
        body = await request.json()
        regions = body.get("regions", [])
        threshold = body.get("threshold_ms", 180)
        
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
            else:
                results.append({
                    "region": region,
                    "avg_latency": 0,
                    "p95_latency": 0,
                    "avg_uptime": 0,
                    "breaches": 0
                })
        
        # Return with explicit CORS headers
        response = JSONResponse(content={"regions": results})
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        
        return response
        
    except Exception as e:
        error_response = JSONResponse(
            content={"error": str(e), "regions": []},
            status_code=500
        )
        error_response.headers["Access-Control-Allow-Origin"] = "*"
        return error_response
