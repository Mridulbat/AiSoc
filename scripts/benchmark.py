"""Reproducible loopback API benchmarks; never reports an Arm result."""

import argparse
import json
import platform
import statistics
import time
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser()
parser.add_argument("--kind", choices=("url", "sms"), default="url")
parser.add_argument("--runs", type=int, default=30)
args = parser.parse_args()
if not 2 <= args.runs <= 1000:
    parser.error("runs must be between 2 and 1000")
text = "https://example.com/" if args.kind == "url" else "Reminder: your bank appointment is tomorrow."
body = json.dumps({"text": text}).encode()
samples = []
for i in range(args.runs + 1):
    start = time.perf_counter()
    request = Request(
        "http://127.0.0.1:8000/api/v1/analyze/" + args.kind,
        data=body,
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
            "analysis_kind": args.kind,
            "input_bytes": len(body),
            "runs": args.runs,
            "median_ms": statistics.median(samples),
            "p95_ms": sorted(samples)[int(0.95 * (len(samples) - 1))],
            "detector": result["detector"],
            "explainer": result["explanation"]["mode"],
            "scope": "warm local HTTP analysis; excludes startup, model export and Arm claims",
        },
        indent=2,
    )
)
