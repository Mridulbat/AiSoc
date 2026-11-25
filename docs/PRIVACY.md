# Privacy and offline behaviour

Normal analysis has no cloud model, analytics, telemetry, DNS lookup, reputation lookup, or URL fetch. The API listens on `127.0.0.1` by default and its test suite patches socket calls during analysis to verify no network dependency.

Raw URL, SMS, and CSV content are processed in memory and are not written to the API history, logs, or response history. History is off by default. When enabled it stores only scan ID, type, risk, and duration in process memory; disabling it, deleting it, or restarting clears it.

Model and dataset setup can require an internet connection. That is distinct from runtime analysis. The Llama worker sets Hugging Face offline environment variables and local-files-only loaders; it receives derived evidence rather than raw user text.

Avoid sharing the working directory when it contains downloaded datasets or private model files. `.gitignore` excludes data, model artifacts, virtual environments, logs, and `.env`.

## Offline exercise

After completing setup, disconnect the machine from the network, start the service, and run the URL, SMS, and network CSV scans. With a configured local export, also run `scripts/verify_llama.py`. All four paths must work without a connection; setup/download commands are deliberately separate and require internet.
