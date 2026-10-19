"""Deterministic held-out evaluation; no website access."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from urllib.parse import urlsplit
from backend.detectors import normalize_message, url_features


def prepare(path, kind):
    if kind == "sms":
        data = pd.read_csv(path, sep="\t", header=None, names=["label", "text"], keep_default_na=False)
        mapping = {"ham": 0, "spam": 1}
        data["text"] = data["text"].map(normalize_message)
    else:
        raw = pd.read_csv(path, usecols=["URL", "label"], keep_default_na=False)
        data = raw.rename(columns={"URL": "text"})
        mapping = {1: 0, 0: 1}  # UCI PhiUSIIL: 1 legitimate, 0 phishing.

        def canonical(text):
            try:
                return url_features(text)[0]
            except ValueError:
                return None

        data["text"] = data["text"].map(canonical)
    if not data.label.isin(mapping).all():
        raise ValueError("Unknown labels; check source schema and explicit mapping.")
    data["label"] = data.label.map(mapping)
    invalid = int(data.text.isna().sum())
    data = data.dropna(subset=["text"])
    conflicts = data.groupby("text").label.nunique()
    data = data[~data.text.isin(conflicts[conflicts > 1].index)]
    before = len(data)
    data = data.drop_duplicates("text").reset_index(drop=True)
    if (data.text.str.len() == 0).any() or data.label.value_counts().min() < 20:
        raise ValueError("Dataset needs nonempty inputs and at least 20 unique examples per class.")
    return data, dict(
        invalid_rows=invalid,
        duplicates_removed=before - len(data),
        conflicting_inputs_removed=int((conflicts > 1).sum()),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["sms", "url"])
    parser.add_argument("--data", required=True)
    parser.add_argument("--models", default="models")
    parser.add_argument("--reports", default="reports")
    args = parser.parse_args()
    data, cleaning = prepare(args.data, args.kind)
    indices = np.arange(len(data))
    if args.kind == "sms":
        train, other = train_test_split(indices, test_size=0.3, stratify=data.label, random_state=42)
        valid, test = train_test_split(other, test_size=0.5, stratify=data.label.iloc[other], random_state=42)
        x = data.text.tolist()
        pipeline = make_pipeline(
            TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, max_features=50000),
            LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42),
        )
        split = "70/15/15 stratified, normalized exact-input deduplication; near-template leakage remains possible"
    else:
        # Group by exact hostname to prevent same-host leakage; related parent domains remain a limitation.
        groups = data.text.map(lambda s: urlsplit(s).hostname)
        train, other = next(
            GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=42).split(indices, data.label, groups)
        )
        vi, ti = next(
            GroupShuffleSplit(n_splits=1, test_size=0.5, random_state=42).split(
                other, data.label.iloc[other], groups.iloc[other]
            )
        )
        valid, test = other[vi], other[ti]
        x = [url_features(s)[1] for s in data.text]
        pipeline = make_pipeline(
            DictVectorizer(sparse=False),
            StandardScaler(),
            LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42),
        )
        split = "70/15/15 approximate, exact-host grouped; related parent domains may overlap; no webpage-derived features"
    for part in (train, valid, test):
        if len(set(data.label.iloc[part])) != 2:
            raise ValueError("Each partition must contain both classes.")
    pipeline.fit([x[i] for i in train], data.label.iloc[train])
    report = dict(
        kind=args.kind,
        source_sha256=hashlib.sha256(Path(args.data).read_bytes()).hexdigest(),
        seed=42,
        split=split,
        cleaning=cleaning,
        sklearn=sklearn.__version__,
        threshold=0.5,
        calibrated=False,
        partitions={},
    )
    for name, part in [("train", train), ("validation", valid), ("test", test)]:
        y = data.label.iloc[part]
        pred = pipeline.predict([x[i] for i in part])
        report["partitions"][name] = dict(
            count=len(part),
            class_distribution={str(k): int(v) for k, v in y.value_counts().items()},
            metrics=classification_report(y, pred, output_dict=True, zero_division=0),
            confusion_matrix=confusion_matrix(y, pred, labels=[0, 1]).tolist(),
            membership_sha256=hashlib.sha256(",".join(map(str, sorted(part))).encode()).hexdigest(),
        )
    Path(args.models).mkdir(parents=True, exist_ok=True)
    Path(args.reports).mkdir(parents=True, exist_ok=True)
    joblib.dump(
        dict(schema=1, kind=args.kind, sklearn=sklearn.__version__, pipeline=pipeline),
        Path(args.models) / (args.kind + ".joblib"),
    )
    (Path(args.reports) / (args.kind + "-evaluation.json")).write_text(json.dumps(report, indent=2))
    print(json.dumps(report["partitions"]["test"], indent=2))


if __name__ == "__main__":
    main()
