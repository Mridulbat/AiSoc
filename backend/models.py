import os
from pathlib import Path
import joblib
import sklearn


class Classifiers:
    def __init__(self):
        self.models = {}
        self.status = {}
        for kind in ("url", "sms"):
            path = Path(os.getenv("SENTINEL_MODEL_DIR", "models")) / (kind + ".joblib")
            self.status[kind] = "unavailable: artifact missing"
            if path.is_file():
                try:
                    artifact = joblib.load(
                        path
                    )  # Trusted locally trained artifacts only: pickle can execute code.
                    if (
                        artifact["schema"] != 1
                        or artifact["kind"] != kind
                        or artifact["sklearn"] != sklearn.__version__
                    ):
                        raise ValueError("incompatible artifact")
                    self.models[kind] = artifact["pipeline"]
                    self.status[kind] = "loaded: trained classifier"
                except Exception:
                    self.status[kind] = "unavailable: incompatible or damaged artifact"

    def predict(self, kind, value):
        if kind not in self.models:
            return None
        try:
            model = self.models[kind]
            return float(model.predict_proba([value])[0][list(model.classes_).index(1)])
        except Exception:
            self.status[kind] = "unavailable: inference failed"
            return None
