import json
import os
from pathlib import Path
import subprocess
import sys
import threading

ADVICE = {
    "verify": "Verify the sender or organization through an independently known contact.",
    "secrets": "Never share an OTP, password or PIN in response to a message.",
    "links": "Use the official app or type a known website address yourself.",
    "network": "Compare flagged flows with your normal workload before isolating a device.",
    "report": "If you already shared credentials, change them through the official service and contact its support.",
}


class Explainer:
    def __init__(self):
        self.path = Path(os.getenv("SENTINEL_LLAMA_DIR", "models/llama"))
        self.lock = threading.Lock()
        self.python = os.getenv("SENTINEL_LLAMA_PYTHON", sys.executable)
        self.env = dict(
            os.environ, HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1"
        )
        # Import in isolation: installed packages can still have missing native DLLs.
        try:
            runtime = (
                subprocess.run(
                    [
                        self.python,
                        "-c",
                        "from executorch.extension.pybindings.portable_lib import _load_for_executorch; from optimum.executorch import ExecuTorchModelForCausalLM",
                    ],
                    capture_output=True,
                    timeout=120,
                    env=self.env,
                ).returncode
                == 0
            )
        except (OSError, subprocess.TimeoutExpired):
            runtime = False
        self.status = dict(
            model_files=(self.path / "model.pte").is_file(),
            tokenizer=(self.path / "tokenizer.json").is_file(),
            runtime=runtime,
            inference_succeeded=False,
            last_error=None,
        )

    def explain(self, kind, risk, evidence, score, uncertainty):
        ids = ["verify", "network"] if kind == "network" else ["verify", "secrets", "links"]
        mode = "template"
        selected = list(range(len(evidence)))
        if all(self.status[k] for k in ("model_files", "tokenizer", "runtime")):
            payload = dict(
                kind=kind,
                risk=risk,
                score=score,
                evidence=evidence,
                uncertainty=uncertainty,
                allowed_advice=ids,
                style="plain language; cautious",
            )
            if self.lock.acquire(blocking=False):
                try:
                    result = subprocess.run(
                        [self.python, "-m", "backend.llama_worker", str(self.path.resolve())],
                        input=json.dumps(payload),
                        text=True,
                        capture_output=True,
                        timeout=90,
                        env=self.env,
                        cwd=Path(__file__).resolve().parents[1],
                        check=True,
                    )
                    answer = json.loads(result.stdout)
                    if set(answer) != {"evidence_ids", "advice_ids"}:
                        raise ValueError()
                    if not isinstance(answer["evidence_ids"], list) or not isinstance(
                        answer["advice_ids"], list
                    ):
                        raise ValueError()
                    if any(
                        type(i) is not int or i not in range(len(evidence)) for i in answer["evidence_ids"]
                    ) or any(i not in ids for i in answer["advice_ids"]):
                        raise ValueError()
                    if not answer["advice_ids"] or (evidence and not answer["evidence_ids"]):
                        raise ValueError()
                    selected = list(dict.fromkeys(answer["evidence_ids"]))
                    ids = list(dict.fromkeys(answer["advice_ids"]))
                    self.status.update(inference_succeeded=True, last_error=None)
                    mode = "llama-executorch"
                except Exception:
                    self.status["inference_succeeded"] = False
                    self.status["last_error"] = (
                        "Local generation failed, timed out or returned invalid structured output."
                    )
                finally:
                    self.lock.release()
        summary = (
            " ".join(evidence[i]["detail"] for i in selected)
            or "No configured warning signals were detected."
        )
        return dict(
            mode=mode,
            text=f"{risk.capitalize()} concern. {summary} {uncertainty}",
            recommendations=[ADVICE[i] for i in ids],
        )
