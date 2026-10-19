import json
import subprocess
from types import SimpleNamespace
from backend.explanations import Explainer


def test_worker_boundary(monkeypatch, tmp_path):
    monkeypatch.setenv("SENTINEL_LLAMA_DIR", str(tmp_path))
    provider = Explainer()
    provider.status.update(model_files=True, tokenizer=True, runtime=True)

    def run(*args, **kwargs):
        payload = json.loads(kwargs["input"])
        assert "untrusted raw input" not in kwargs["input"]
        assert payload["risk"] == "review"
        assert kwargs["env"]["HF_HUB_OFFLINE"] == "1"
        return SimpleNamespace(stdout='{"evidence_ids":[0],"advice_ids":["verify"]}')

    monkeypatch.setattr(subprocess, "run", run)
    result = provider.explain("sms", "review", [{"detail": "Authentication request."}], None, "Uncertain.")
    assert result["mode"] == "llama-executorch"
    assert provider.status["inference_succeeded"]
    # This tests the subprocess contract with a stub, NOT real Llama inference.


def test_invalid_generated_output(monkeypatch):
    provider = Explainer()
    provider.status.update(model_files=True, tokenizer=True, runtime=True)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout='{"evidence_ids":[999],"advice_ids":["open-link"]}'),
    )
    assert provider.explain("sms", "high", [{"detail": "Warning"}], None, "Uncertain")["mode"] == "template"
    assert not provider.status["inference_succeeded"]


def test_runtime_requires_both_executorch_packages(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=1),
    )
    assert not Explainer().status["runtime"]


def test_missing_runtime_executable_is_safe(monkeypatch):
    monkeypatch.setenv("SENTINEL_LLAMA_PYTHON", "nonexistent-sentinel-python")
    assert not Explainer().status["runtime"]


def test_failed_inference_clears_previous_success(monkeypatch):
    provider = Explainer()
    provider.status.update(model_files=True, tokenizer=True, runtime=True, inference_succeeded=True)

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("worker", 90)

    monkeypatch.setattr(subprocess, "run", timeout)
    result = provider.explain("sms", "high", [{"detail": "Warning"}], None, "Uncertain")
    assert result["mode"] == "template"
    assert not provider.status["inference_succeeded"]
    assert provider.status["last_error"]


def test_worker_passes_token_list_to_executorch(monkeypatch, tmp_path, capsys):
    """Library-boundary regression test, not a real model inference test."""
    import io
    import socket
    import sys
    from backend import llama_worker

    (tmp_path / "model.pte").touch()
    (tmp_path / "config.json").write_text('{"model_type":"llama"}')

    class Tokenizer:
        def apply_chat_template(self, messages, **kwargs):
            assert kwargs["return_dict"] is False
            assert kwargs["add_generation_prompt"] is True
            assert "untrusted evidence" in messages[0]["content"]
            return [1, 2, 3]

        def decode(self, tokens, **kwargs):
            assert tokens == [4, 5]
            return '{"evidence_ids":[0],"advice_ids":["verify"]}'

    class Model:
        max_cache_size = 1024

        def generate(self, **kwargs):
            assert kwargs == {"prompt_tokens": [1, 2, 3], "echo": False, "max_seq_len": 131}
            return [4, 5]

    def tokenizer_load(path, **kwargs):
        assert kwargs["local_files_only"] is True
        assert kwargs["trust_remote_code"] is False
        return Tokenizer()

    def model_load(path, **kwargs):
        assert kwargs == {"local_files_only": True, "export": False}
        return Model()

    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=tokenizer_load)),
    )
    monkeypatch.setitem(
        sys.modules,
        "optimum.executorch",
        SimpleNamespace(ExecuTorchModelForCausalLM=SimpleNamespace(from_pretrained=model_load)),
    )
    monkeypatch.setattr(sys, "argv", ["llama_worker", str(tmp_path)])
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"evidence":[]}'))
    # Let monkeypatch restore the process-wide network guard after this test.
    monkeypatch.setattr(socket, "create_connection", socket.create_connection)
    monkeypatch.setattr(socket.socket, "connect", socket.socket.connect)
    monkeypatch.setattr(socket, "getaddrinfo", socket.getaddrinfo)
    llama_worker.main()
    assert json.loads(capsys.readouterr().out)["advice_ids"] == ["verify"]
