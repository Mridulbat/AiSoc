"""Real runtime smoke test. This does NOT verify Llama inference."""

import torch
from executorch.exir import to_edge
from executorch.extension.pybindings.portable_lib import _load_for_executorch_from_buffer


class Add(torch.nn.Module):
    def forward(self, x):
        return x + x


def main():
    x = torch.tensor([1.0, 2.0])
    program = to_edge(torch.export.export(Add(), (x,))).to_executorch()
    model = _load_for_executorch_from_buffer(program.buffer)
    result = model.forward((x,))[0]
    if not torch.equal(result, torch.tensor([2.0, 4.0])):
        raise SystemExit("ExecuTorch returned an incorrect result")
    print("PASS: real ExecuTorch export and CPU execution; NOT Llama inference")


if __name__ == "__main__":
    main()
