# Enhancement audit — 2026-10-19

| Capability | Evidence | Status | Gap and improvement | Priority / acceptance |
|---|---|---|---|---|
| URL + SMS local classifiers | `scripts/train.py`, held-out JSON reports, API tests | ALREADY IMPLEMENTED AND VERIFIED | Scores are uncalibrated; retain that label. | A / reports contain held-out metrics and provenance. |
| Network flow analysis | `backend/network.py`, CSV fixture | PARTIALLY IMPLEMENTED | Batch IsolationForest is not intrusion classification. Added versioned detector identity, returned input schema, and traceable mapped statistics. | A / valid CSV produces traceable findings; unsupported PCAP is explicit. |
| Network labelled evaluation | No licensed compatible local flow dataset | BLOCKED BY AN EXTERNAL PREREQUISITE | Do not train a classifier until CICIDS/UNSW data, licence, and matching schema are reviewed. | A / obtain data, train-only preprocessing, held-out evaluation. |
| PCAP ingestion | No packet parser dependency or fixture | MISSING | Deferred: PCAP needs documented packet/flow semantics, not a fake upload label. | B / add only with a licensed fixture and parser tests. |
| Evidence explanations | `Explainer`, worker contract tests | IMPLEMENTED BUT NOT ADEQUATELY VERIFIED | Real local Llama path passed once; tests cover contract/fallback, not every model output. | A / structured IDs remain authoritative. |
| Offline/privacy | socket-intercept API test, loopback bind | IMPLEMENTED BUT NOT ADEQUATELY VERIFIED | Add disconnected full-app manual procedure. | A / documented exercise covers URL, SMS, CSV and configured worker. |
| Benchmarks | `scripts/benchmark.py` | PARTIALLY IMPLEMENTED | URL-only warm loopback timing; no Llama/network/memory breakdown. | B / extend after selecting stable representative inputs. |
| Arm validation | `docs/ARM64_DEPLOYMENT.md` | BLOCKED BY AN EXTERNAL PREREQUISITE | Requires physical Arm64 execution. | A / run verifier and target benchmark. |

The immediate implemented improvement is the network CSV contract and traceability. Optional features are deferred until they have data or hardware evidence.
