import json
import math
from flask import Flask, request, jsonify

app = Flask(__name__)

with open("q-vercel-latency.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

def p95(values):
    vals = sorted(values)
    if not vals:
        return None
    idx = math.ceil(0.95 * len(vals)) - 1
    return vals[idx]

@app.after_request
def add_cors_headers(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp

@app.route("/api/latency", methods=["POST", "OPTIONS"])
def latency():
    if request.method == "OPTIONS":
        return ("", 200)

    payload = request.get_json(force=True)
    regions = payload.get("regions", [])
    threshold_ms = payload.get("threshold_ms", 180)

    result = {}
    for region in regions:
        rows = [r for r in DATA if r.get("region") == region]
        latencies = [r["latency_ms"] for r in rows]
        uptimes = [r["uptime"] for r in rows]

        result[region] = {
            "avg_latency": (sum(latencies) / len(latencies)) if latencies else None,
            "p95_latency": p95(latencies) if latencies else None,
            "avg_uptime": (sum(uptimes) / len(uptimes)) if uptimes else None,
            "breaches": sum(1 for x in latencies if x > threshold_ms),
        }

    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)