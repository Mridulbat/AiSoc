import pandas as pd
import pytest

from scripts.train_network import prepare


def test_prepare_cic_and_unsw_labels(tmp_path):
    values = list(range(40))
    labels = ["BENIGN", "Attack"] * 20
    cic = tmp_path / "cic.csv"
    pd.DataFrame({"Flow Bytes/s": values, "Packets": values, "Duration": values, "Label": labels}).to_csv(
        cic, index=False
    )
    _, y, features = prepare(cic, "cicids2017")
    assert y.tolist() == [0, 1] * 20 and "flow bytes/s" in features
    unsw = tmp_path / "unsw.csv"
    pd.DataFrame({"dur": values, "sbytes": values, "dbytes": values, "label": [0, 1] * 20}).to_csv(
        unsw, index=False
    )
    assert prepare(unsw, "unsw-nb15")[1].tolist() == [0, 1] * 20


def test_prepare_rejects_unknown_unsw_label(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"a": [1, 2, 3], "b": [1, 2, 3], "c": [1, 2, 3], "label": [0, 2, 1]}).to_csv(
        path, index=False
    )
    with pytest.raises(ValueError, match="binary label"):
        prepare(path, "unsw-nb15")
