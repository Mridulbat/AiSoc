import json
import time
from collections import deque
from pathlib import Path
from threading import Lock
from typing import Literal
from uuid import uuid4
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.middleware.trustedhost import TrustedHostMiddleware
from backend.detectors import normalize_message, risk, sms_rules, url_features, url_rules
from backend.explanations import Explainer
from backend.models import Classifiers
from backend.network import analyze_csv


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=10000)

    @field_validator("text")
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError("Input must not be blank")
        return value


class Privacy(BaseModel):
    enabled: bool


class Result(BaseModel):
    id: str
    kind: Literal["url", "sms", "network"]
    risk: Literal["low", "review", "high"]
    score: float | None
    score_semantics: str
    evidence: list[dict]
    uncertainty: str
    explanation: dict
    detector: str
    readiness: dict
    duration_ms: float
    network: dict | None = None


class Limits:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        origin = headers.get(b"origin")
        if origin and origin not in (
            b"http://127.0.0.1:8000",
            b"http://localhost:8000",
            b"http://127.0.0.1:5173",
            b"http://localhost:5173",
        ):
            return await JSONResponse({"detail": "Origin is not allowed."}, 403)(scope, receive, send)
        chunks, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > 2_100_000:
                return await JSONResponse({"detail": "Request exceeds 2 MB limit."}, 413)(
                    scope, receive, send
                )
            chunks.append(message.get("body", b""))
            if not message.get("more_body", False):
                break
        consumed = False

        async def replay():
            nonlocal consumed
            if consumed:
                return await receive()
            consumed = True
            return {"type": "http.request", "body": b"".join(chunks), "more_body": False}

        async def secure_send(message):
            if message["type"] == "http.response.start":
                message["headers"] += [
                    (b"cache-control", b"no-store"),
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                    (
                        b"content-security-policy",
                        b"default-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'",
                    ),
                ]
            await send(message)

        await self.app(scope, replay, secure_send)


app = FastAPI(title="SentinelEdge", version="1.0.0")
app.add_middleware(Limits)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])
models, explainer = Classifiers(), Explainer()
history = deque(maxlen=100)
history_enabled = False
history_lock = Lock()


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse(
        {"detail": "Invalid input. Provide nonempty text (up to 10,000 characters) or a valid CSV upload."},
        422,
    )


@app.exception_handler(Exception)
async def internal_error(request, exc):
    return JSONResponse(
        {"detail": "Analysis unavailable. Check local model configuration and try again."}, 500
    )


@app.get("/api/v1/health")
def health():
    return dict(
        status="ok",
        detectors=models.status,
        explainer=explainer.status,
        history_enabled=history_enabled,
        offline=True,
    )


@app.get("/api/v1/history")
def get_history():
    with history_lock:
        return list(history)


@app.delete("/api/v1/history")
def delete_history():
    with history_lock:
        history.clear()
    return {"deleted": True}


@app.put("/api/v1/history/settings")
def settings(value: Privacy):
    global history_enabled
    with history_lock:
        history_enabled = value.enabled
        if not value.enabled:
            history.clear()
    return {"enabled": history_enabled}


def finish(kind, evidence, score, started, network=None):
    level = risk(evidence, score)
    uncertainty = "Low concern does not establish safety. Offline signals can miss new threats."
    if kind == "sms":
        uncertainty += " A spam prediction is not confirmation of fraud."
    if kind == "network":
        uncertainty = "Unusual traffic is not proof of intrusion; batch composition affects these findings."
    explanation = explainer.explain(kind, level, evidence, score, uncertainty)
    detector = (
        "batch-isolation-forest"
        if network
        else "trained-classifier + rules"
        if score is not None
        else "rules-only"
    )
    result = Result(
        id=str(uuid4()),
        kind=kind,
        risk=level,
        score=score,
        score_semantics=(
            "Uncalibrated classifier estimate of "
            + ("spam" if kind == "sms" else "phishing")
            + " class; not certainty."
        )
        if score is not None
        else "No probability available.",
        evidence=evidence,
        uncertainty=uncertainty,
        explanation=explanation,
        detector=detector,
        readiness=health(),
        duration_ms=round((time.perf_counter() - started) * 1000, 2),
        network=network,
    )
    with history_lock:
        if history_enabled:
            history.appendleft(dict(id=result.id, kind=kind, risk=level, duration_ms=result.duration_ms))
    return result


@app.post("/api/v1/analyze/url", response_model=Result)
def url(value: Input):
    started = time.perf_counter()
    try:
        _, features = url_features(value.text)
    except ValueError as e:
        raise HTTPException(422, str(e)) from None
    return finish("url", url_rules(features), models.predict("url", features), started)


@app.post("/api/v1/analyze/sms", response_model=Result)
def sms(value: Input):
    started = time.perf_counter()
    return finish("sms", sms_rules(value.text), models.predict("sms", normalize_message(value.text)), started)


@app.post("/api/v1/analyze/network-csv", response_model=Result)
def network(file: UploadFile = File(...), columns: str = Form('["duration","bytes","packets"]')):
    started = time.perf_counter()
    raw = file.file.read(2_000_001)
    if len(raw) > 2_000_000:
        raise HTTPException(413, "CSV exceeds 2 MB.")
    try:
        mapping = json.loads(columns)
        if not isinstance(mapping, list) or any(not isinstance(c, str) or len(c) > 100 for c in mapping):
            raise ValueError("Column mapping must be a JSON list of three names.")
        result = analyze_csv(raw, mapping)
    except (ValueError, TypeError) as e:
        detail = str(e) if not isinstance(e, (json.JSONDecodeError, TypeError)) else "Invalid column mapping."
        # Numeric parsing errors must not echo raw uploaded values.
        if "could not convert" in detail:
            detail = "Mapped columns must contain numeric flow statistics."
        raise HTTPException(422, detail) from None
    evidence = (
        [
            dict(
                code="outliers",
                detail=f"{result['anomalies']} of {result['count']} flows are unusual within this batch.",
                weight=1,
            )
        ]
        if result["anomalies"]
        else []
    )
    return finish("network", evidence, None, started, result)


static = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if static.is_dir():
    app.mount("/", StaticFiles(directory=static, html=True), name="frontend")
