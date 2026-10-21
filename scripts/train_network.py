"""Train/evaluate one labelled flow dataset at a time; never mix CICIDS2017 and UNSW-NB15."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def prepare(path, dataset):
    data = pd.read_csv(path, low_memory=False)
    data.columns = [str(c).strip().lower() for c in data.columns]
    if "label" not in data:
        raise ValueError("Expected a Label/label column from the official flow CSV export.")
    labels = data.pop("label")
    y = (
        labels.astype(str).str.strip().str.lower().ne("benign").astype(int)
        if dataset == "cicids2017"
        else pd.to_numeric(labels, errors="coerce")
    )
    if y.isna().any() or not set(y.unique()).issubset({0, 1}):
        raise ValueError("UNSW-NB15 requires its binary label column (0 benign, 1 attack).")
    x = data.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan)
    if x.shape[1] < 3 or y.value_counts().min() < 20:
        raise ValueError("Need at least three numeric features and 20 rows per class.")
    return x, y.astype(int), list(x.columns)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", choices=("cicids2017", "unsw-nb15"))
    parser.add_argument("--data", required=True, help="One official labelled CSV export")
    parser.add_argument("--reports", default="reports")
    args = parser.parse_args()
    x, y, features = prepare(args.data, args.dataset)
    train, test = train_test_split(np.arange(len(y)), test_size=0.2, stratify=y, random_state=42)
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42),
    )
    model.fit(x.iloc[train], y.iloc[train])
    pred = model.predict(x.iloc[test])
    matrix = confusion_matrix(y.iloc[test], pred, labels=[0, 1]).tolist()
    report = {
        "dataset": args.dataset,
        "source_sha256": hashlib.sha256(Path(args.data).read_bytes()).hexdigest(),
        "seed": 42,
        "split": "80/20 stratified row split; do not compare or combine with another dataset schema",
        "features": features,
        "rows": int(len(y)),
        "class_distribution": {str(k): int(v) for k, v in y.value_counts().items()},
        "metrics": classification_report(y.iloc[test], pred, output_dict=True, zero_division=0),
        "confusion_matrix": matrix,
        "false_positive_rate": matrix[0][1] / sum(matrix[0]) if sum(matrix[0]) else None,
        "false_negative_rate": matrix[1][0] / sum(matrix[1]) if sum(matrix[1]) else None,
        "sklearn": sklearn.__version__,
        "model": "median-imputation + standardization + balanced logistic regression",
    }
    Path(args.reports).mkdir(parents=True, exist_ok=True)
    output = Path(args.reports) / f"network-{args.dataset}-evaluation.json"
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
