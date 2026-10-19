# Threat model

| Asset / boundary | Threat | Mitigation | Residual risk |
|---|---|---|---|
| Submitted URL | SSRF, malware visit, DNS leak | Parse only; no fetch/resolve code | Parsing bugs and deceptive Unicode remain possible |
| Submitted message | Prompt injection / HTML execution | Treat as data; no raw text enters Llama prompt; React text rendering | Detector may still misclassify content |
| Uploaded CSV | Resource exhaustion, malformed values | 2 MB body limit, 10,000-row cap, strict CSV, finite numeric bounds | IsolationForest fit still consumes bounded local CPU |
| Joblib artifacts | Deserialisation code execution | Load only locally trained, trusted artifacts; compatibility checks | A replaced local model file is still untrusted |
| Llama output | Unsafe or fabricated advice | Restricted ID schema, known advice allowlist, fallback on failure | Model quality needs real-device validation |
| Local API | Cross-origin/browser abuse | loopback binding, trusted host, origin allowlist, no-store headers | A local malicious process remains in the local trust boundary |

Users should independently verify through known official contact channels and never share credentials/OTP values in response to an unsolicited message.
