# SentinelEdge

**Offline AI for Safer Digital Communication.** SentinelEdge is a local-first dashboard for inspecting URLs, suspicious messages, and flow-statistics CSV files. It never resolves or opens submitted URLs and does not use cloud AI, DNS, or threat-intelligence services during analysis.

## What is implemented

- URL parsing, canonicalisation, interpretable rules, and an optional local scikit-learn classifier.
- SMS normalisation, TF-IDF/logistic-regression scoring, and supporting scam signals.
- Offline CSV anomaly analysis with `IsolationForest`; unusual means unusual within the uploaded batch, not malicious.
- A React dashboard with accessible forms, diagnostics, bounded in-memory opt-in history, and clear fallback status.
- A Llama/ExecuTorch explanation adapter. The authenticated local Llama 3.2 1B XNNPACK export and strict generation verifier pass on this Windows AMD64 machine; Arm validation remains unperformed.

## Quick start (Windows)

```powershell
./scripts/setup.ps1
./scripts/run.ps1
```

Open `http://127.0.0.1:8000`. The service binds to loopback only. For Linux/macOS, use `bash scripts/setup.sh` then `bash scripts/run.sh`.

## Verify

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check backend scripts tests
.\.venv\Scripts\python -m ruff format --check backend scripts tests
Push-Location frontend; npm test; npm run build; Pop-Location
```

The committed evaluation reports were produced with scikit-learn 1.6.1. Reproduce them with:

```powershell
.\.venv\Scripts\python scripts/train.py sms --data data/SMSSpamCollection
.\.venv\Scripts\python scripts/train.py url --data data/PhiUSIIL_Phishing_URL_Dataset.csv
```

See [DATASETS.md](docs/DATASETS.md), [MODEL_CARD.md](docs/MODEL_CARD.md), [BENCHMARKING.md](docs/BENCHMARKING.md), and [EVALUATION.md](docs/EVALUATION.md) before interpreting results.

## Llama + ExecuTorch

This is a required competition path but needs separately approved Meta model access and a compatible dedicated runtime. Follow [EXECUTORCH.md](docs/EXECUTORCH.md), then run `python scripts/verify_llama.py`. Only its successful exit proves the real local generation path; the dashboard reports its exact readiness fields.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Privacy](docs/PRIVACY.md)
- [Threat model](docs/THREAT_MODEL.md)
- [Arm64 deployment](docs/ARM64_DEPLOYMENT.md)
- [Technical report](docs/TECHNICAL_REPORT.md)

