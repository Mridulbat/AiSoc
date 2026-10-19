"""Fails unless real local generation returns validated evidence/advice IDs."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.explanations import Explainer

provider = Explainer()
result = provider.explain(
    "sms",
    "high",
    [{"code": "secrets", "detail": "The message requests an authentication secret.", "weight": 2}],
    None,
    "This evidence does not prove fraud.",
)
print(json.dumps({"readiness": provider.status, "result": result}, indent=2))
if result["mode"] != "llama-executorch":
    raise SystemExit("Real Llama + ExecuTorch inference NOT verified.")
