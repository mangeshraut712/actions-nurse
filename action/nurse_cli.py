#!/usr/bin/env python3
"""CLI triage for the Actions Nurse GitHub Action (rules + optional Gemma 4)."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RULES = [
    (r"TS2305|has no exported member|tsc --noEmit|error TS\d+", {
        "summary": "CI failed on TypeScript typecheck (missing module exports).",
        "failing_step": "Typecheck / tsc",
        "root_cause": "TypeScript compile errors — missing exports or stale types after a merge.",
        "suggested_fix": "Align exports with imports, or rebase onto main and restore missing named exports.",
        "confidence": "high",
        "fix_commands": ["npm run typecheck", "git rebase origin/main"],
    }),
    (r"AssertionError|FAILED tests/|pytest|short test summary", {
        "summary": "CI failed because a pytest assertion did not match.",
        "failing_step": "Unit tests / pytest",
        "root_cause": "A unit test assertion no longer matches the computed result.",
        "suggested_fix": "Open the named test, recompute expected values, or fix the code under test.",
        "confidence": "high",
        "fix_commands": ["pytest -q"],
    }),
    (r"heap out of memory|JavaScript heap|exit code 134|Killed", {
        "summary": "CI was killed by a JavaScript heap out-of-memory error.",
        "failing_step": "Build / bundler",
        "root_cause": "Node process ran out of memory (OOM / exit 134).",
        "suggested_fix": "Raise NODE_OPTIONS=--max-old-space-size=4096 in the workflow, or split the build job.",
        "confidence": "high",
        "fix_commands": ['echo "NODE_OPTIONS=--max-old-space-size=4096" >> $GITHUB_ENV'],
    }),
    (r"npm ERR!|ERESOLVE|peer dep", {
        "summary": "CI failed while installing npm dependencies.",
        "failing_step": "npm install",
        "root_cause": "Dependency resolution failed (peer dependency conflict).",
        "suggested_fix": "Pin compatible versions or commit an updated lockfile and use npm ci.",
        "confidence": "medium",
        "fix_commands": ["npm ci"],
    }),
]


def rule_triage(log: str) -> dict:
    for pattern, payload in RULES:
        if re.search(pattern, log, re.I):
            return {**payload, "engine": "rules", "patterns": [pattern]}
    step = "Unknown step"
    m = re.search(r"^##\[group\]Run (.+)$", log, re.M) or re.search(r"^Run (.+)$", log, re.M)
    if m:
        step = m.group(1).strip()
    return {
        "summary": "CI failed; no known pattern matched — inspect the last error block.",
        "failing_step": step,
        "root_cause": "Unrecognized failure signature in the pasted log.",
        "suggested_fix": "Scroll to the first Error: line, fix that root cause, and re-run the job.",
        "confidence": "low",
        "fix_commands": [],
        "engine": "rules",
        "patterns": [],
    }


def gemma_triage(log: str, model: str, key: str) -> dict | None:
    prompt = (
        "You are Actions Nurse. Reply ONLY JSON with keys summary, failing_step, "
        "root_cause, suggested_fix, confidence (high|medium|low), "
        "fix_commands (array of shell commands).\n\nLOG:\n" + log[:12000]
    )
    models = [model]
    if "gemma-4" in model:
        models += ["gemma-4-31b-it", "gemini-2.5-flash", "gemini-flash-latest"]
    for m_name in models:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            + urllib.parse.quote(m_name, safe="")
            + ":generateContent?key="
            + urllib.parse.quote(key)
        )
        body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode())
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            m = re.search(r"\{[\s\S]*\}", text)
            if not m:
                continue
            parsed = json.loads(m.group(0))
            cmds = parsed.get("fix_commands") or []
            if not isinstance(cmds, list):
                cmds = []
            return {
                "summary": str(parsed.get("summary", "Gemma triage complete."))[:500],
                "failing_step": str(parsed.get("failing_step", "Unknown"))[:200],
                "root_cause": str(parsed.get("root_cause", ""))[:800],
                "suggested_fix": str(parsed.get("suggested_fix", ""))[:800],
                "confidence": str(parsed.get("confidence", "medium"))[:20],
                "fix_commands": [str(c)[:200] for c in cmds][:8],
                "engine": "gemma",
                "patterns": [],
                "model": m_name,
            }
        except Exception:
            continue
    return None


def to_markdown(result: dict) -> str:
    cmds = result.get("fix_commands") or []
    cmd_block = "\n".join(f"- `{c}`" for c in cmds) if cmds else "_None suggested_"
    return f"""# 🩺 Actions Nurse report

**Engine:** `{result.get('engine')}` · **Confidence:** `{result.get('confidence')}`

## Summary
{result.get('summary')}

## Failing step
{result.get('failing_step')}

## Root cause
{result.get('root_cause')}

## Suggested fix
{result.get('suggested_fix')}

## Fix commands
{cmd_block}

---
Built for Hacktoberfest Hack Day Pune x Cloud Native Pune · Gemma 4 + offline rules
"""


def maybe_fetch_failed_job_log(run_id: str) -> str | None:
    """Optional: download first failed job log via gh when GITHUB_TOKEN is present."""
    if not run_id or not os.environ.get("GITHUB_TOKEN"):
        return None
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        return None
    try:
        jobs = subprocess.check_output(
            [
                "gh", "api",
                f"/repos/{repo}/actions/runs/{run_id}/jobs",
                "--jq",
                ".jobs[] | select(.conclusion==\"failure\") | .id",
            ],
            text=True,
            timeout=30,
        ).strip().splitlines()
        if not jobs:
            return None
        job_id = jobs[0].strip()
        log = subprocess.check_output(
            ["gh", "api", f"/repos/{repo}/actions/jobs/{job_id}/logs"],
            text=True,
            timeout=60,
            stderr=subprocess.DEVNULL,
        )
        return log
    except Exception as exc:
        print(f"gh log fetch skipped: {exc}", file=sys.stderr)
        return None


def main() -> int:
    log_path = Path(os.environ.get("NURSE_LOG_PATH", ""))
    out_path = Path(os.environ.get("NURSE_OUTPUT", "nurse-report.md"))
    model = os.environ.get("NURSE_MODEL", "gemma-4-26b-a4b-it")
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
    run_id = os.environ.get("NURSE_WORKFLOW_RUN_ID", "")

    log = ""
    if log_path and log_path.exists():
        log = log_path.read_text(errors="replace")
    elif run_id:
        fetched = maybe_fetch_failed_job_log(run_id)
        if fetched:
            log = fetched
    if not log:
        print("No log available (set NURSE_LOG_PATH or NURSE_WORKFLOW_RUN_ID)", file=sys.stderr)
        return 1

    result = (gemma_triage(log, model, key) if key else None) or rule_triage(log)
    out_path.write_text(to_markdown(result))
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            summary = (result.get("summary") or "").replace("\n", " ")
            f.write(f"summary={summary}\n")
            f.write(f"engine={result.get('engine')}\n")
            f.write(f"report_path={out_path}\n")
    print(json.dumps({"engine": result.get("engine"), "summary": result.get("summary"), "report": str(out_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
