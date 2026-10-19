# SentinelEdge technical report

## Problem and objective

PS3 requires local detection of network anomalies, phishing/scam communications, understandable explanations, recommendations, and Llama through ExecuTorch on Arm hardware. SentinelEdge provides a loopback-only local web application for these tasks.

## Method

URL analysis safely canonicalises an HTTP(S) input and uses structural features plus explicit rules. SMS analysis uses normalised TF-IDF/bigram logistic regression plus rules. The network tool validates three numeric flow features and flags batch-relative outliers with IsolationForest. Evidence is aggregated into low/review/high concern with uncertainty text.

The explanation adapter sends only structured evidence to a local Llama/ExecuTorch worker. It validates structured generated IDs and otherwise uses a deterministic template. This preserves usability if models are unavailable while making the mode visible.

## Evaluation

Reproducible held-out reports are stored in `reports/`. URL phishing-class precision/recall/F1 on its test partition are 0.976/0.918/0.946; SMS spam values are 0.938/0.948/0.943. These figures are dataset-specific, uncalibrated, and not a guarantee for current threats. The local Windows warm URL benchmark is documented in [BENCHMARKING.md](BENCHMARKING.md).

## Security and privacy

The system does not fetch URLs, resolve hostnames, call cloud services during analysis, store raw inputs in history, or render input as HTML. Request and CSV bounds, strict Pydantic models, output validation, security headers, and local-only binding reduce risk. See [THREAT_MODEL.md](THREAT_MODEL.md) and [PRIVACY.md](PRIVACY.md).

## Constraints and next validation

The authenticated Llama 3.2 1B XNNPACK export and strict local generation verifier passed on Windows AMD64 with the compatible ExecuTorch environment. No Arm device was available, so no Arm performance or inference result is claimed. Next work is an Arm64 export/inference run, benchmark capture, and a target-device video.
