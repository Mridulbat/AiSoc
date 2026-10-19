# Architecture

```text
React/Vite UI -> FastAPI /api/v1 -> URL or SMS classifier + rules -> validated evidence
                                  -> CSV validator -> IsolationForest -> batch findings
                                  -> explanation adapter -> Llama/ExecuTorch OR template
```

`backend/main.py` is the boundary: it validates requests, enforces a 2 MB body limit, does not persist inputs by default, and adds no-store/security headers. `detectors.py` canonicalises URLs without network activity and produces explainable features/rules. `models.py` loads only compatible local joblib artifacts and degrades to rules-only if absent or invalid. `network.py` parses UTF-8 CSV with the standard library and bounds rows before fitting a deterministic IsolationForest.

`explanations.py` passes compact detector output—not raw submitted text—to `llama_worker.py`. The worker disables common socket entry points, uses local-files-only loading, validates the model metadata, and outputs constrained evidence/advice IDs. Generated output is schema-checked before it can affect the displayed explanation. Any failure returns the deterministic template mode.

The browser consumes only versioned `/api/v1` endpoints. In a production launch FastAPI serves the built UI; Vite is development-only.
