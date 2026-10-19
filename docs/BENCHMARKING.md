# Benchmarking

Start the local service, then run `python scripts/benchmark.py --runs 30`. It performs one warm-up plus measured loopback HTTP URL scans and records median/p95 wall time, platform, architecture, detector mode, and explainer mode. It excludes startup, model export/download, UI rendering, and unmeasured resource usage.

`reports/benchmark-windows.json` is the only committed benchmark: Windows AMD64, 30 warm URL scans, template explanation, median 21.34 ms and p95 32.04 ms. It is not an Arm, Llama, energy, or throughput result.

For comparable target results, use an idle device with the same artifact/runtime, include the command output, and report whether `inference_succeeded` is true. Do not compare a template result with a Llama generation result as if they measured the same workload.
