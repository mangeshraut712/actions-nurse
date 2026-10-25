"""Actions Nurse — Gemma 4 GitHub Actions triage for Hack Day Pune."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"

app = FastAPI(title="Actions Nurse", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(ROOT / "web")), name="static")


class TriageRequest(BaseModel):
    log: str = Field(..., min_length=1)
    model: str = "gemma-4-26b-a4b-it"


class TriageResult(BaseModel):
    summary: str
    failing_step: str
    root_cause: str
    suggested_fix: str
    confidence: str
    engine: str
    patterns: list[str] = []


RULES: list[tuple[str, dict[str, str]]] = [
    (
        r"TS2305|has no exported member|tsc --noEmit|error TS\d+",
        {
            "failing_step": "Typecheck / tsc",
            "root_cause": "TypeScript compile errors — missing exports or stale types after a merge.",
            "suggested_fix": "Align types/scoring exports with imports, or rebase onto main and restore missing named exports.",
            "confidence": "high",
            "summary": "CI failed on TypeScript typecheck (missing module exports).",
        },
    ),
    (
        r"AssertionError|FAILED tests/|pytest|short test summary",
        {
            "failing_step": "Unit tests / pytest",
            "root_cause": "A unit test assertion no longer matches the computed result.",
            "suggested_fix": "Open the named test, recompute expected values from fixtures, or fix the code under test.",
            "confidence": "high",
            "summary": "CI failed because a pytest assertion did not match.",
        },
    ),
    (
        r"heap out of memory|JavaScript heap|exit code 134|Killed",
        {
            "failing_step": "Build / bundler",
            "root_cause": "Node process ran out of memory (OOM / exit 134).",
            "suggested_fix": "Raise NODE_OPTIONS=--max-old-space-size=4096 in the workflow, or split the build job.",
            "confidence": "high",
            "summary": "CI was killed by a JavaScript heap out-of-memory error.",
        },
    ),
    (
        r"npm ERR!|ERESOLVE|peer dep",
        {
            "failing_step": "npm install",
            "root_cause": "Dependency resolution failed (peer dependency conflict).",
            "suggested_fix": "Pin compatible versions or commit an updated lockfile and use npm ci.",
            "confidence": "medium",
            "summary": "CI failed while installing npm dependencies.",
        },
    ),
]


def rule_triage(log: str) -> TriageResult:
    for pattern, payload in RULES:
        if re.search(pattern, log, re.I):
            return TriageResult(
                summary=payload["summary"],
                failing_step=payload["failing_step"],
                root_cause=payload["root_cause"],
                suggested_fix=payload["suggested_fix"],
                confidence=payload["confidence"],
                engine="rules",
                patterns=[pattern],
            )
    step = "Unknown step"
    m = re.search(r"^##\[group\]Run (.+)$", log, re.M) or re.search(r"^Run (.+)$", log, re.M)
    if m:
        step = m.group(1).strip()
    return TriageResult(
        summary="CI failed; no known pattern matched — inspect the last error block.",
        failing_step=step,
        root_cause="Unrecognized failure signature in the pasted log.",
        suggested_fix="Scroll to the first Error: line, fix that root cause, and re-run the job.",
        confidence="low",
        engine="rules",
        patterns=[],
    )


def gemma_triage(log: str, model: str) -> Optional[TriageResult]:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        return None
    try:
        import httpx
    except ImportError:
        return None
    prompt = (
        "You are Actions Nurse. Reply ONLY JSON with keys summary, failing_step, "
        "root_cause, suggested_fix, confidence (high|medium|low).\n\nLOG:\n" + log[:12000]
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    try:
        r = httpx.post(url, params={"key": key}, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return None
        data = json.loads(m.group(0))
        return TriageResult(
            summary=str(data.get("summary", "Gemma triage complete."))[:500],
            failing_step=str(data.get("failing_step", "Unknown"))[:200],
            root_cause=str(data.get("root_cause", ""))[:800],
            suggested_fix=str(data.get("suggested_fix", ""))[:800],
            confidence=str(data.get("confidence", "medium"))[:20],
            engine="gemma",
        )
    except Exception:
        return None


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ROOT / "web" / "index.html")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "gemma_key": bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")),
        "event": "Hacktoberfest Hack Day Pune x Cloud Native Pune",
    }


@app.get("/api/fixtures")
def list_fixtures() -> dict[str, list[str]]:
    return {"fixtures": sorted(p.name for p in FIXTURES.glob("*.txt"))}


@app.get("/api/fixtures/{name}")
def get_fixture(name: str) -> JSONResponse:
    path = FIXTURES / Path(name).name
    if not path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse({"name": path.name, "log": path.read_text()})


@app.post("/api/triage", response_model=TriageResult)
def triage(req: TriageRequest) -> TriageResult:
    return gemma_triage(req.log, req.model) or rule_triage(req.log)


@app.post("/api/triage-image", response_model=TriageResult)
async def triage_image(
    log: str = Form(""),
    image: UploadFile = File(...),
    model: str = Form("gemma-4-26b-a4b-it"),
) -> TriageResult:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    raw = await image.read()
    if not key or not raw:
        base = rule_triage(log or "screenshot uploaded without API key")
        base.summary = "No GEMINI_API_KEY — used rules on the text log (image ignored)."
        return base
    import base64
    import httpx

    b64 = base64.b64encode(raw).decode()
    mime = image.content_type or "image/png"
    prompt = (
        "Screenshot of failed CI. Reply ONLY JSON: summary, failing_step, root_cause, "
        "suggested_fix, confidence (high|medium|low)."
    )
    if log.strip():
        prompt += "\n\nLog:\n" + log[:4000]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime, "data": b64}},
            ]
        }]
    }
    try:
        r = httpx.post(url, params={"key": key}, json=body, timeout=90)
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            data = json.loads(m.group(0))
            return TriageResult(
                summary=str(data.get("summary", "Screenshot reviewed."))[:500],
                failing_step=str(data.get("failing_step", "CI"))[:200],
                root_cause=str(data.get("root_cause", ""))[:800],
                suggested_fix=str(data.get("suggested_fix", ""))[:800],
                confidence=str(data.get("confidence", "medium"))[:20],
                engine="gemma",
            )
    except Exception:
        pass
    return rule_triage(log or "image triage failed; falling back")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("nurse:app", host="127.0.0.1", port=8787, reload=False)
