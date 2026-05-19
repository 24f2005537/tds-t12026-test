import json
import os
import statistics
from http.server import BaseHTTPRequestHandler

# Load the JSON bundle once at startup
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'q-vercel-latency.json')
with open(DATA_PATH) as f:
    RAW_DATA = json.load(f)

# RAW_DATA is expected to be a list of records like:
# {"region": "amer", "latency_ms": 120, "uptime": 0.99}


def compute_metrics(records, threshold_ms):
    latencies = [r["latency_ms"] for r in records]
    uptimes   = [r["uptime"] for r in records]
    avg_latency  = statistics.mean(latencies)
    p95_latency  = sorted(latencies)[int(len(latencies) * 0.95)]
    avg_uptime   = statistics.mean(uptimes)
    breaches     = sum(1 for l in latencies if l > threshold_ms)
    return {
        "avg_latency": avg_latency,
        "p95_latency": p95_latency,
        "avg_uptime":  avg_uptime,
        "breaches":    breaches,
    }


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self._send_cors_headers(200)

    def do_POST(self):
        length  = int(self.headers.get("Content-Length", 0))
        body    = self.rfile.read(length)
        payload = json.loads(body)

        regions      = payload.get("regions", [])
        threshold_ms = payload.get("threshold_ms", 180)

        result = {}
        for region in regions:
            records = [r for r in RAW_DATA if r["region"] == region]
            if records:
                result[region] = compute_metrics(records, threshold_ms)
            else:
                result[region] = None

        response = json.dumps(result).encode()
        self._send_cors_headers(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def _send_cors_headers(self, code):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if code != 200:
            self.end_headers()