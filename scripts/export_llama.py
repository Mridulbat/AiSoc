"""Setup-only export; requires approved Meta model access and a dedicated runtime."""

import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="models/llama")
    parser.add_argument("--model", default="meta-llama/Llama-3.2-1B-Instruct")
    args = parser.parse_args()
    from transformers import AutoTokenizer, AutoConfig

    # Resolve access and model identity before starting the expensive export.
    config = AutoConfig.from_pretrained(args.model, trust_remote_code=False)
    if config.model_type != "llama":
        raise SystemExit("A Llama-family model is required.")
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=False)
    cli = Path(sys.executable).parent / ("optimum-cli.exe" if sys.platform == "win32" else "optimum-cli")
    if not cli.is_file():
        raise SystemExit("Install requirements-executorch.txt in this Python environment first.")
    subprocess.run(
        [
            str(cli),
            "export",
            "executorch",
            "--model",
            args.model,
            "--recipe",
            "xnnpack",
            "--dtype",
            "float32",
            "--max_seq_len",
            "1024",
            "--output_dir",
            args.output,
        ],
        check=True,
    )
    tokenizer.save_pretrained(args.output)
    config.save_pretrained(args.output)
    Path(args.output, "environment.txt").write_text(
        subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
    )
    print("Exported. Run scripts/verify_llama.py before claiming readiness.")


if __name__ == "__main__":
    main()
