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


from http.server import BaseHTTPRequestHandler
import json

class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Your existing GET logic here
        with open('q-vercel-latency.json', 'r') as f:
            data = f.read()
        self.wfile.write(data.encode())
    
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_heads()
        
        # Handle POST request
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        response = {
            "message": "POST received successfully",
            "status": "success",
            "your_data": json.loads(post_data)
        }
        self.wfile.write(json.dumps(response).encode())
