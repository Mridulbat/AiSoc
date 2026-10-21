# Datasets and reproducibility

| Capability | Local input | Source/terms | Label mapping |
|---|---|---|---|
| SMS | `data/SMSSpamCollection` | [UCI SMS Spam Collection](https://archive.ics.uci.edu/dataset/228/sms+spam+collection); check UCI terms | `ham=0`, `spam=1` |
| URL | `data/PhiUSIIL_Phishing_URL_Dataset.csv` | PhiUSIIL phishing URL dataset; source metadata is in `data/url-source.json`; review its upstream licence before redistribution | `1=legitimate (0)`, `0=phishing (1)` |
| Network | `fixtures/network-DEMO-ONLY.csv` | Synthetic fixture made only for UI/tests | no malicious label |
| Network evaluation | CICIDS2017 official labelled flow CSV | [Canadian Institute for Cybersecurity](https://www.unb.ca/cic/datasets/ids-2017.html); cite dataset/paper when used | `BENIGN=0`, other labels=`1` |
| Network evaluation | UNSW-NB15 official labelled flow CSV | [UNSW Canberra](https://research.unsw.edu.au/projects/unsw-nb15-dataset); academic use/citation terms must be followed | official binary `label`: `0=benign`, `1=attack` |

## Network CSV contract

The supported network input is UTF-8 CSV containing at least 20 and at most 10,000 pre-aggregated flow rows. Select exactly three distinct numeric, finite, nonnegative columns in this order: duration, bytes, packets. Default column names are `duration`, `bytes`, `packets`; the UI/API accepts a mapping for equivalent source names. Optional `protocol`, `source`, `destination`, and `start_time` columns are retained only as external metadata and are not detector features. PCAP ingestion is not implemented. An anomaly is batch-relative and is never a labelled intrusion claim.

`scripts/train.py` validates expected columns and labels, canonicalises URLs, removes invalid inputs, removes conflicting exact inputs and duplicates, and records SHA-256 hashes, split membership hashes, class distributions, metrics, and confusion matrices in `reports/*-evaluation.json`.

SMS uses a stratified 70/15/15 split. URL uses a grouped split on exact hostname to reduce same-host leakage; related domains can still overlap. TF-IDF and feature vectorisation are fit only on training partitions. The models are not calibrated, so the returned score is explicitly an uncalibrated classifier estimate—not a probability or fraud verdict.

Do not replace data silently. Re-run `scripts/train.py` and retain the resulting report whenever data, labels, or dependencies change.

For network evaluation, download official CSV files manually after reviewing access terms, then run one dataset at a time: `python scripts/train_network.py cicids2017 --data path/to/cic.csv` or `python scripts/train_network.py unsw-nb15 --data path/to/unsw.csv`. The script intentionally rejects schema mixing and records selected numeric features, source hash, FPR/FNR, confusion matrix, and held-out metrics. These experiment models are evaluation artefacts only; the live network tool remains its separately documented three-feature batch anomaly detector.
