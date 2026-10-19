# SentinelEdge implementation

- DONE: Inspected instructions, repository and Windows AMD64 environment; verified official PS3 requirements on 2026-10-19.
- DONE: Offline FastAPI API, safe URL/SMS detectors, trained local artifacts, opt-in in-memory history, bounded CSV anomaly analysis, template fallback, and React dashboard are present and exercised.
- DONE: Reproducible training/evaluation pipeline and reports for URL/SMS datasets; source metadata, splitting and limitations documented.
- DONE: Genuine Llama + ExecuTorch adapter, export command, isolated worker, readiness diagnostics and real-inference verification command are implemented. It does not substitute a hosted model or a different runtime.
- DONE: Added README plus architecture, datasets, model card, privacy, threat-model, ExecuTorch, Arm64 deployment, benchmarking, report and demo documents.
- DONE: Current local checks: `pytest -q` = 42 passed (one upstream deprecation warning); `npm test` = 3 passed; `npm run build` passed; Ruff check and format check passed.
- DONE: Authenticated export of `meta-llama/Llama-3.2-1B-Instruct` to a local 5.99 GB XNNPACK `model.pte`; the strict verifier returned `mode=llama-executorch` with all readiness fields true.
- BLOCKED: No Arm hardware is available, so Arm deployment/benchmark claims are intentionally absent.

Next prerequisite: run and record the Arm benchmark on target hardware. Re-run `scripts/verify_llama.py` after any model/runtime upgrade.

## Llama follow-up, 2026-10-19

- HISTORICAL: The earlier unauthenticated access check returned HTTP 401; it was superseded by the authenticated export recorded below.
- DONE: Fixed runtime detection to test native imports in isolation, kept the probe offline, and clear stale success after failed generation. Added regression tests; 42 backend tests pass.
- DONE: Export checks access/model identity before expensive work and uses the CLI belonging to its Python environment. Added exact Windows login/export/verification commands to docs/EXECUTORCH.md.
- DONE: Installed isolated .venv-llama with ExecuTorch 1.5.1, PyTorch 2.14.0+cpu and the pinned Optimum revision. pip check passes; full adapter imports pass. A real tensor-model export/execution passes (not Llama). Saved requirements-lock-llama-windows.txt.
- HISTORICAL: Before account authorization and export, the verifier exited 1 with missing model/tokenizer. The successful current result is recorded below.

- DONE: Fixed Transformers 5 chat-template output to request a token list explicitly (return_dict=False); regression test covers the worker/library boundary with stubs, not real inference. Ruff check and format check pass.

## Authenticated Llama export, 2026-10-19

- DONE: Saved Hugging Face login was recognized; the full Llama 3.2 1B model was exported through Optimum + ExecuTorch XNNPACK on Windows AMD64.
- DONE: Installed `coremltools` because Optimum discovers its Core ML recipe before selecting XNNPACK, and installed the FlatBuffers `flatc` compiler through `winget install --exact --id Google.flatbuffers`; both are now documented setup prerequisites.
- DONE: `scripts/verify_llama.py` ran against `models/llama` with `.venv-llama\\Scripts\\python.exe` and exited 0: `model_files=true`, `tokenizer=true`, `runtime=true`, `inference_succeeded=true`, `mode=llama-executorch`.
- DONE: A fresh FastAPI `/api/v1/analyze/sms` request with the same configured worker returned HTTP 200, `llama-executorch`, and all explainer readiness fields true.
- DONE: Current checks: backend `pytest -q` = 42 passed (one upstream deprecation warning), Ruff check/format passed, frontend `npm test` = 3 passed, and `npm run build` passed.
- BLOCKED: This Windows AMD64 verification is not Arm64 deployment or performance evidence; target hardware remains required for that claim.
