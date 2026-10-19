# Llama + ExecuTorch setup and verification

This path is intentionally separate from the lightweight application environment. The selected candidate is `meta-llama/Llama-3.2-1B-Instruct`; access requires accepting Meta's licence and authenticating with Hugging Face. No weights are committed or downloaded at application startup.

1. Create an isolated supported Linux/WSL2 or Arm64 environment. Install `requirements-executorch.txt` after confirming the pinned versions work for that target.
2. Authenticate to Hugging Face after licence approval. Run `python scripts/export_llama.py --output /absolute/path/to/models/llama` from that environment. The script uses Optimum's documented `optimum-cli export executorch --recipe xnnpack` route and preserves tokenizer/configuration beside `model.pte`.
3. Set `SENTINEL_LLAMA_DIR` to that output. If it is a separate environment, set `SENTINEL_LLAMA_PYTHON` to its Python executable.
4. Run `python scripts/verify_llama.py`. It must exit zero and print `"mode": "llama-executorch"` plus `inference_succeeded: true` before claiming real integration.
5. Start SentinelEdge and check `/api/v1/health`; all of `model_files`, `tokenizer`, `runtime`, and `inference_succeeded` should be true.

The adapter loads `ExecuTorchModelForCausalLM` and `AutoTokenizer` with `local_files_only=True`. The worker validates a Llama `config.json`, uses the exported model, and restricts output to evidence/advice IDs. The local Windows AMD64 procedure completed on 2026-10-19; the strict verifier exercised actual Llama generation through this path. This does not establish Arm64 target compatibility.

References: [Optimum ExecuTorch quickstart](https://huggingface.co/docs/optimum-executorch/quickstart), [ExecuTorch documentation](https://docs.pytorch.org/executorch/), and [challenge PS3](https://arm-education.github.io/Arm-Developer-Labs/Bharat_AI_SoC_2026_27.html).

## Windows setup and account prerequisite

On 2026-10-19, the authenticated Windows AMD64 setup exported and verified the
selected Llama model locally. This is real local CPU inference evidence, but it
is not Arm64 deployment or performance evidence. ExecuTorch 1.5.1 publishes a
Windows AMD64 Python 3.10 wheel; wheel availability alone still does not prove
compatibility for a different target.

The pinned setup includes `coremltools`: Optimum's current recipe discovery
imports its Core ML recipe even when the requested target is XNNPACK. On Windows
it emits unavailable-Core-ML proxy warnings; the XNNPACK route does not use Core
ML. It also needs the FlatBuffers compiler, installable with
`winget install --exact --id Google.flatbuffers`. Restart PowerShell after that
install so `flatc` is on `PATH`.

Request access on https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct using
your own account and accept its terms. Do not put a token in source files or chat.
After approval, run from the repository root in PowerShell:

```powershell
.\.venv\Scripts\python -m venv .venv-llama
.\.venv-llama\Scripts\python -m pip install --upgrade pip
.\.venv-llama\Scripts\python -m pip install -r requirements-executorch.txt
.\.venv-llama\Scripts\hf auth login
# Setup requires downloads; these overrides apply only to this shell.
$env:HF_HUB_OFFLINE = "0"
$env:TRANSFORMERS_OFFLINE = "0"
.\.venv-llama\Scripts\python scripts/export_llama.py --output models/llama
$env:SENTINEL_LLAMA_DIR = (Resolve-Path models/llama).Path
$env:SENTINEL_LLAMA_PYTHON = (Resolve-Path .venv-llama/Scripts/python.exe).Path
.\.venv\Scripts\python scripts/verify_llama.py
.\scripts\run.ps1
```

The application and its runtime import probe force offline settings regardless of
the setup shell settings. Export selects `optimum-cli` beside its own interpreter
and checks the model config/access before starting export. Readiness checks native
imports in a subprocess; a failed generation clears the previous success status.
A verification exit of 1 with template mode is a failure to demonstrate Llama,
not a successful model test. The explainer currently uses the model to select
validated evidence/advice IDs and renders trusted sentences from those selections.
It does not expose arbitrary model-generated prose.

PyTorch 2.14.0 and TorchAO 0.18.0 are pinned to the versions named by the
[ExecuTorch v1.5.1 release setup](https://github.com/pytorch/executorch/blob/v1.5.1/install_requirements.py).

## Measured local runtime result (2026-10-19)

Installed the dedicated Windows AMD64 Python 3.10 environment in `.venv-llama`.
`pip check` passes, and both the portable ExecuTorch loader and
`ExecuTorchModelForCausalLM` import successfully. The native tensor-model smoke
check passed; reproduce it with:

```powershell
.\.venv-llama\Scripts\python scripts/verify_executorch.py
```

This verifies real export and CPU execution of addition, **not a Llama model or
XNNPACK Llama export**. The resolved environment is recorded in
`requirements-lock-llama-windows.txt`. Cold imports were slow on this machine,
so the isolated readiness probe allows up to 120 seconds.

The initial export attempt exposed two environment omissions: Optimum imported
the unused Core ML recipe without `coremltools`, then XNNPACK lowering required
the unavailable `flatc` executable. After installing those prerequisites, the
export completed and produced `models/llama/model.pte` (5,994,339,456 bytes),
plus config/tokenizer files. The strict verifier exited 0 with
`model_files=true`, `tokenizer=true`, `runtime=true`, and
`inference_succeeded=true`, using `mode=llama-executorch`. No Arm hardware was
tested.
