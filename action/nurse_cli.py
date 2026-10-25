#!/usr/bin/env python3
"""CLI triage for the Actions Nurse GitHub Action (rules + optional Gemma 4)."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
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
    (r"No space left on device|ENOSPC", {
        "summary": "CI failed because the runner filesystem is full.",
        "failing_step": "Runner filesystem",
        "root_cause": "The runner ran out of disk space while writing build or cache files.",
        "suggested_fix": "Remove oversized caches/artifacts, prune build output, or use a larger self-hosted runner.",
        "confidence": "high",
        "fix_commands": ["df -h", "du -sh ./* | sort -h"],
    }),
    (r"Permission denied|fatal: could not read Username|Authentication failed|Repository not found", {
        "summary": "CI failed because checkout or repository authentication was denied.",
        "failing_step": "Checkout / repository access",
        "root_cause": "The runner could not authenticate to, or lacked permission for, a repository or protected resource.",
        "suggested_fix": "Check the checkout token, repository permissions, and any required PAT or deploy key; do not print credentials in logs.",
        "confidence": "high",
        "fix_commands": ["git remote -v", "git ls-remote origin"],
    }),
]


def rule_triage(log: str) -> dict:
    # Check the specific runner-capacity signal before broad package-manager noise.
    for pattern, payload in sorted(RULES, key=lambda item: "ENOSPC" not in item[0]):
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
    """Gemma-first triage with a total 12-second budget before rules."""
    prompt = (
        "You are Actions Nurse. Reply ONLY JSON with keys summary, failing_step, "
        "root_cause, suggested_fix, confidence (high|medium|low), "
        "fix_commands (array of short, non-destructive shell commands). Do not invent evidence.\n\nLOG:\n" + log[:12000]
    )
    models = [model]
    if "gemma-4" in model.lower():
        models += ["gemma-4-31b-it", "gemma-4-26b-it"]
    models = list(dict.fromkeys(models))
    deadline = time.monotonic() + 12
    for m_name in models:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            + urllib.parse.quote(m_name, safe="")
            + ":generateContent?key="
            + urllib.parse.quote(key)
        )
        body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=max(1, remaining)) as resp:
                data = json.loads(resp.read().decode())
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                m = re.search(r"\{[\s\S]*\}", text)
                if not m:
                    continue
                parsed = json.loads(m.group(0))
            if not isinstance(parsed, dict):
                continue
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
    """Fetch only failed-step output from the workflow run when gh is available."""
    if not run_id or not os.environ.get("GITHUB_TOKEN"):
        return None
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        return None
    try:
        return subprocess.check_output(
            ["gh", "run", "view", run_id, "--repo", repo, "--log-failed"],
            text=True, timeout=45, stderr=subprocess.DEVNULL,
        )
    except Exception as exc:
        print(f"gh log fetch skipped: {exc}", file=sys.stderr)
        return None


def main() -> int:
    log_path_raw = os.environ.get("NURSE_LOG_PATH", "").strip()
    log_path = Path(log_path_raw) if log_path_raw else None
    out_path = Path(os.environ.get("NURSE_OUTPUT", "nurse-report.md"))
    model = os.environ.get("NURSE_MODEL", "gemma-4-26b-a4b-it")
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
    rules_only = os.environ.get("NURSE_RULES_ONLY", "").strip().lower() in {"1", "true", "yes"}
    run_id = os.environ.get("NURSE_WORKFLOW_RUN_ID", "")

    log = ""
    if log_path and log_path.is_file():
        log = log_path.read_text(errors="replace")
    elif run_id:
        fetched = maybe_fetch_failed_job_log(run_id)
        if fetched:
            log = fetched
    if not log:
        print("No log available (set NURSE_LOG_PATH or NURSE_WORKFLOW_RUN_ID)", file=sys.stderr)
        return 1

    result = (gemma_triage(log, model, key) if key and not rules_only else None) or rule_triage(log)
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
