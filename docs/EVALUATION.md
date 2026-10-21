# Evaluation workflow

Run the reproducible URL/SMS evaluations from the repository root:

```powershell
.\.venv\Scripts\python scripts\train.py sms --data data/SMSSpamCollection
.\.venv\Scripts\python scripts\train.py url --data data/PhiUSIIL_Phishing_URL_Dataset.csv
```

Each command fits preprocessing only on the training partition and writes `reports/<kind>-evaluation.json`. The JSON includes SHA-256 source identity, seed, cleaning counts, class distribution, per-class precision/recall/F1/support, confusion matrix, split-membership hash, threshold and calibration status. False positives and false negatives are the off-diagonal confusion-matrix cells; divide by actual negative or positive support for FPR/FNR.

The fixed threshold is 0.5. Scores are uncalibrated classifier estimates, not fraud probability. URL splitting groups exact hostnames; SMS splitting is stratified exact-text deduplicated. Neither result establishes performance on new campaigns, related domains, or arbitrary traffic.

Network analysis is unsupervised batch anomaly detection, not an evaluated intrusion classifier. `fixtures/network-DEMO-ONLY.csv` is synthetic and demonstrates input validation and traceability only. A labelled network evaluation is blocked until a compatible, licensed CICIDS/UNSW-style flow dataset is reviewed and a separate train/validation/test schema is implemented.

For CICIDS2017 or UNSW-NB15, use `scripts/train_network.py` with a manually obtained official CSV. It uses an isolated binary experiment per dataset, median-imputes numeric features inside the training pipeline, and saves machine-readable held-out metrics, FPR/FNR, source hash, and exact feature names. It never combines the datasets or routes their model into the live CSV detector without a separately validated deployment schema.

Hand-authored robustness tests in `tests/` cover IP literals, IDN/punycode, encoded and malformed URLs, urgency/secrets/payment SMS language, benign lower-risk examples, oversized input, malformed CSV, and unusual-but-not-confirmed network flows. They are regression tests, not representative evaluation data.
