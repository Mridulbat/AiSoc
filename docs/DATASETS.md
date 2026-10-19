# Datasets and reproducibility

| Capability | Local input | Source/terms | Label mapping |
|---|---|---|---|
| SMS | `data/SMSSpamCollection` | [UCI SMS Spam Collection](https://archive.ics.uci.edu/dataset/228/sms+spam+collection); check UCI terms | `ham=0`, `spam=1` |
| URL | `data/PhiUSIIL_Phishing_URL_Dataset.csv` | PhiUSIIL phishing URL dataset; source metadata is in `data/url-source.json`; review its upstream licence before redistribution | `1=legitimate (0)`, `0=phishing (1)` |
| Network | `fixtures/network-DEMO-ONLY.csv` | Synthetic fixture made only for UI/tests | no malicious label |

`scripts/train.py` validates expected columns and labels, canonicalises URLs, removes invalid inputs, removes conflicting exact inputs and duplicates, and records SHA-256 hashes, split membership hashes, class distributions, metrics, and confusion matrices in `reports/*-evaluation.json`.

SMS uses a stratified 70/15/15 split. URL uses a grouped split on exact hostname to reduce same-host leakage; related domains can still overlap. TF-IDF and feature vectorisation are fit only on training partitions. The models are not calibrated, so the returned score is explicitly an uncalibrated classifier estimate—not a probability or fraud verdict.

Do not replace data silently. Re-run `scripts/train.py` and retain the resulting report whenever data, labels, or dependencies change.
