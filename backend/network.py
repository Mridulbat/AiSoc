import csv
import io
import numpy as np
from sklearn.ensemble import IsolationForest

COLUMNS = ["duration", "bytes", "packets"]
DETECTOR_VERSION = "isolation-forest-log1p-v1"


def analyze_csv(raw, columns=None):
    columns = columns or COLUMNS
    if len(columns) != 3 or len(set(columns)) != 3:
        raise ValueError("Map exactly three distinct columns: duration, bytes, packets.")
    try:
        reader = csv.reader(io.StringIO(raw.decode("utf-8-sig")), strict=True)
        header = next(reader)
        if len(header) != len(set(header)) or not set(columns).issubset(header):
            raise ValueError("CSV must contain unique mapped columns: " + ", ".join(columns))
        indices = [header.index(c) for c in columns]
        rows = []
        for row in reader:
            if len(rows) >= 10000:
                raise ValueError("Maximum 10,000 rows per file.")
            if len(row) != len(header):
                raise ValueError("Every CSV row must match the header.")
            values = [float(row[i]) for i in indices]
            if any(not np.isfinite(v) or v < 0 or v > 1e15 for v in values):
                raise ValueError("Flow statistics must be finite, nonnegative numbers below 1e15.")
            rows.append(values)
    except (UnicodeError, StopIteration, csv.Error):
        raise ValueError("Upload a nonempty UTF-8 CSV with a header.") from None
    except OverflowError:
        raise ValueError("Numeric value is too large.") from None
    if len(rows) < 20:
        raise ValueError(
            "At least 20 observations are required; small samples cannot support anomaly analysis."
        )
    x = np.asarray(rows)
    model = IsolationForest(n_estimators=100, contamination="auto", random_state=42, n_jobs=1).fit(
        np.log1p(x)
    )
    scores = model.decision_function(np.log1p(x))
    med = np.median(x, axis=0)
    scale = np.maximum(np.median(np.abs(x - med), axis=0), 1)
    result = []
    for i, (values, score) in enumerate(zip(x, scores)):
        deviation = np.abs(values - med) / scale
        result.append(
            dict(
                row=i + 2,
                anomaly=bool(score < 0),
                score=float(score),
                statistics=dict(zip(columns, values.tolist())),
                largest_deviation=columns[int(np.argmax(deviation))],
            )
        )
    return dict(
        rows=result,
        count=len(rows),
        anomalies=sum(r["anomaly"] for r in result),
        detector=DETECTOR_VERSION,
        input_schema={
            "required_numeric_columns": columns,
            "optional_metadata_columns": ["protocol", "source", "destination", "start_time"],
            "pcap_support": False,
            "limitations": "CSV rows are pre-aggregated flows. Protocol and endpoint metadata are not used by this detector.",
        },
        semantics="IsolationForest decision function: negative means unusual relative to this uploaded batch, not confirmed malicious. Largest deviation is descriptive, not model attribution.",
    )
