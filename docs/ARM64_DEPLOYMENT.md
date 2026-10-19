# Arm64 deployment (Raspberry Pi 5 / Arm Linux)

This document is a reproducible target procedure, not a completed hardware-validation claim.

1. Use a 64-bit Arm Linux image with sufficient free storage/RAM and a current Python/Node toolchain. Clone the repository locally.
2. Run `bash scripts/setup.sh` to install the API/frontend dependencies and build the UI.
3. Follow [EXECUTORCH.md](EXECUTORCH.md) in a target-compatible runtime; use an Arm-compatible ExecuTorch/XNNPACK export and run `scripts/verify_llama.py` on the device.
4. Start `bash scripts/run.sh`, then use the local browser at `http://127.0.0.1:8000`. Use an explicit reverse proxy/network bind only after adding suitable authentication and transport controls.
5. Benchmark after successful model verification: `python scripts/benchmark.py --runs 30 > reports/benchmark-arm64.json`. Record device/OS, model/export, thermal state, runtime, and detector/explainer mode.

Llama runs through ExecuTorch on the Arm CPU. No Hailo/NPU claim is made; the current URL/SMS models are scikit-learn CPU artifacts and network analysis is CPU-based. Validate responsiveness, memory pressure, thermals, and the exact exported operators before a demo.
