"""Actions Nurse — Gemma 4 GitHub Actions triage for Hack Day Pune."""
from __future__ import annotations

import base64
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
MAX_LOG_CHARS = 12_000
MAX_IMAGE_BYTES = 5 * 1024 * 1024
GEMMA_BUDGET_SECONDS = 12
DEFAULT_MODEL = "gemma-4-26b-a4b-it"

app = FastAPI(title="Actions Nurse", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(ROOT / "web")), name="static")


class TriageRequest(BaseModel):
    log: str = Field(..., min_length=1)
    model: str = Field(DEFAULT_MODEL, min_length=1, max_length=120)
    rules_only: bool = False


class TriageResult(BaseModel):
    summary: str
    failing_step: str
    root_cause: str
    suggested_fix: str
    confidence: str
    engine: str
    patterns: list[str] = []
    fix_commands: list[str] = []
    model: str = ""


RULES: list[tuple[str, dict[str, str]]] = [
    (
        r"TS2305|has no exported member|tsc --noEmit|error TS\d+",
        {
            "failing_step": "Typecheck / tsc",
            "root_cause": "TypeScript compile errors — missing exports or stale types after a merge.",
            "suggested_fix": "Align types/scoring exports with imports, or rebase onto main and restore missing named exports.",
            "confidence": "high",
            "summary": "CI failed on TypeScript typecheck (missing module exports).",
            "fix_commands": ["npm run typecheck", "git diff origin/main...HEAD -- src/"],
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
            "fix_commands": ["pytest -q tests/test_tools.py::test_spill_volume_last_month"],
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
            "fix_commands": ["NODE_OPTIONS=--max-old-space-size=4096 npm run build"],
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
            "fix_commands": ["npm ci", "npm explain <package-name>"],
        },
    ),
    (
        r"No space left on device|ENOSPC",
        {
            "failing_step": "Runner filesystem",
            "root_cause": "The runner ran out of disk space while writing build or cache files.",
            "suggested_fix": "Remove oversized caches/artifacts, prune build output, or use a larger self-hosted runner.",
            "confidence": "high",
            "summary": "CI failed because the runner filesystem is full.",
            "fix_commands": ["df -h", "du -sh ./* | sort -h"],
        },
    ),
]


def clean_text(value: Any, limit: int) -> str:
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(value or "")).strip()[:limit]


def clean_commands(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    commands = [clean_text(command, 200) for command in value]
    return [command for command in commands if command][:8]


def result_from_data(data: dict[str, Any], *, engine: str, model: str = "", patterns: Optional[list[str]] = None) -> TriageResult:
    confidence = clean_text(data.get("confidence", "medium"), 20).lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "medium"
    return TriageResult(
        summary=clean_text(data.get("summary", "Triage complete."), 500),
        failing_step=clean_text(data.get("failing_step", "Unknown"), 200),
        root_cause=clean_text(data.get("root_cause"), 800),
        suggested_fix=clean_text(data.get("suggested_fix"), 800),
        confidence=confidence,
        engine=engine,
        patterns=patterns or [],
        fix_commands=clean_commands(data.get("fix_commands")),
        model=model,
    )


def rule_triage(log: str) -> TriageResult:
    # Check the specific runner-capacity signal before broad package-manager noise.
    for pattern, payload in sorted(RULES, key=lambda item: "ENOSPC" not in item[0]):
        if re.search(pattern, log, re.I):
            return result_from_data(payload, engine="rules", patterns=[pattern])
    step = "Unknown step"
    m = re.search(r"^##\[group\]Run (.+)$", log, re.M) or re.search(r"^Run (.+)$", log, re.M)
    if m:
        step = m.group(1).strip()
    return result_from_data({
        "summary": "CI failed; no known pattern matched — inspect the first error block.",
        "failing_step": step,
        "root_cause": "Unrecognized failure signature in the pasted log.",
        "suggested_fix": "Start with the first Error: line, fix that root cause, and re-run the job.",
        "confidence": "low",
    }, engine="rules")


def gemma_models(model: str) -> list[str]:
    """Gemma only: requested model first, compatible aliases second."""
    models = [model]
    if "gemma-4" in model.lower():
        models.extend(["gemma-4-31b-it", "gemma-4-26b-it"])
    return list(dict.fromkeys(models))


def parse_model_json(text: str) -> Optional[dict[str, Any]]:
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None


def gemma_triage(log: str, model: str, image: Optional[tuple[str, bytes]] = None) -> Optional[TriageResult]:
    """Gemma-first triage with a hard 12-second end-to-end budget."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        return None
    try:
        import httpx
    except ImportError:
        return None
    prompt = (
        "You are Actions Nurse. Reply ONLY JSON with keys summary, failing_step, "
        "root_cause, suggested_fix, confidence (high|medium|low), "
        "fix_commands (array of short, non-destructive shell commands). Do not invent evidence.\n\nLOG:\n" + log[:MAX_LOG_CHARS]
    )
    deadline = time.monotonic() + GEMMA_BUDGET_SECONDS
    for m_name in gemma_models(model):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_name}:generateContent"
        parts: list[dict[str, Any]] = [{"text": prompt}]
        if image:
            mime, raw = image
            parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(raw).decode("ascii")}})
        try:
            r = httpx.post(url, params={"key": key}, json={"contents": [{"parts": parts}]}, timeout=max(0.5, remaining))
            if r.status_code == 200:
                text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                data = parse_model_json(text)
                if data:
                    return result_from_data(data, engine="gemma", model=m_name)
        except Exception:
            continue
    return None


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ROOT / "web" / "index.html")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "gemma_key": bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")),
        "gemma_budget_seconds": GEMMA_BUDGET_SECONDS,
        "event": "Hacktoberfest Hack Day Pune x Cloud Native Pune",
    }


@app.get("/api/fixtures")
def list_fixtures() -> dict[str, list[str]]:
    return {"fixtures": sorted(p.name for p in FIXTURES.glob("*.txt"))}


@app.get("/api/fixtures/{name}")
def get_fixture(name: str) -> JSONResponse:
    path = FIXTURES / Path(name).name
    if not path.is_file() or path.suffix != ".txt":
        raise HTTPException(status_code=404, detail="fixture not found")
    return JSONResponse({"name": path.name, "log": path.read_text(encoding="utf-8", errors="replace")})


@app.post("/api/triage", response_model=TriageResult)
def triage(req: TriageRequest) -> TriageResult:
    return rule_triage(req.log) if req.rules_only else (gemma_triage(req.log, req.model) or rule_triage(req.log))


@app.post("/api/triage-image", response_model=TriageResult)
async def triage_image(
    log: str = Form(""),
    image: UploadFile = File(...),
    model: str = Form(DEFAULT_MODEL),
) -> TriageResult:
    raw = await image.read(MAX_IMAGE_BYTES + 1)
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="image must be 5 MB or smaller")
    if not raw:
        raise HTTPException(status_code=422, detail="image is empty")
    result = gemma_triage(log or "Screenshot supplied; no text log was pasted.", model, (image.content_type or "image/png", raw))
    if result:
        return result
    fallback = rule_triage(log or "screenshot uploaded without a usable Gemma response")
    fallback.summary = "Gemma was unavailable within 12 seconds; rules triage used the pasted log."
    return fallback



class CompareResult(BaseModel):
    rules: TriageResult
    gemma: Optional[TriageResult] = None


@app.post("/api/compare", response_model=CompareResult)
def compare(req: TriageRequest) -> CompareResult:
    """Side-by-side rules vs Gemma — great for show-and-tell."""
    rules = rule_triage(req.log)
    gemma = gemma_triage(req.log, req.model)
    return CompareResult(rules=rules, gemma=gemma)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("nurse:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8787")), reload=False)
