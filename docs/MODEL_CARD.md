# Model card

## Intended use

SentinelEdge assists a person reviewing a URL, message, or network-flow batch locally. It is not a blocking control, antivirus engine, malware classifier, or authoritative fraud decision service.

## Models

- **URL:** hostname/path structural features, `DictVectorizer`, `StandardScaler`, balanced logistic regression plus visible rules.
- **SMS:** normalised text, word/bigram TF-IDF, balanced logistic regression plus visible rules.
- **Network:** per-upload `IsolationForest` over `log1p(duration, bytes, packets)`; it has no global malicious/benign labels.
- **Explanation:** template fallback; optional Llama-family model through ExecuTorch only after real local export/verification.

## Evaluation evidence

The held-out reports are [SMS](../reports/sms-evaluation.json) and [URL](../reports/url-evaluation.json), generated under scikit-learn 1.6.1. Their test phishing-class recall is 0.918 and SMS-spam recall is 0.948. These are dataset-specific results, not production guarantees. URL grouped splitting is approximate, and SMS templates may remain similar across partitions.

False negatives may miss novel scams; false positives may inconvenience legitimate senders or domains. HTTPS, a low score, or no rules never means safe. Threshold tuning and calibration require an independent representative validation set.

## Out of scope

No live packet capture, DNS/reputation lookup, webpage fetching, multilingual validation, adversarial robustness claim, Llama quality evaluation, or Arm performance claim has been completed.
