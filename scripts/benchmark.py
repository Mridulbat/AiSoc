"""Local API benchmark; latency includes HTTP overhead. No user inputs retained."""

import argparse
import json
import platform
import statistics
import time
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser()
parser.add_argument("--runs", type=int, default=30)
args = parser.parse_args()
if not 2 <= args.runs <= 1000:
    parser.error("runs must be between 2 and 1000")
samples = []
for i in range(args.runs + 1):
    start = time.perf_counter()
    request = Request(
        "http://127.0.0.1:8000/api/v1/analyze/url",
        data=json.dumps({"text": "https://example.com/"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=120) as response:
        result = json.load(response)
    if i:
        samples.append((time.perf_counter() - start) * 1000)
print(
    json.dumps(
        {
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "runs": args.runs,
            "median_ms": statistics.median(samples),
            "p95_ms": sorted(samples)[int(0.95 * (len(samples) - 1))],
            "detector": result["detector"],
            "explainer": result["explanation"]["mode"],
            "scope": "warm local HTTP URL scan; excludes service startup; no Arm claim",
        },
        indent=2,
    )
)
