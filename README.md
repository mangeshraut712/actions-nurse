# 🩺 Actions Nurse

**GitHub Actions CI triage powered by open-weight Gemma 4 & deterministic rule engines.**  
Built for **Hacktoberfest Hack Day Pune x Cloud Native Pune** (October 25, 2026).

[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Gemma 4](https://img.shields.io/badge/Model-Gemma_4-purple.svg)](https://ai.google.dev/gemma)

---

## 💡 The Problem

Cloud-native engineers and platform teams spend hours parsing noisy, thousands-of-lines-long GitHub Actions CI logs. When a build goes red, finding the exact failing step, root cause, and remediation usually requires navigating cluttered web consoles.

**Actions Nurse** acts as an instant triage triage room for CI failures:
- Paste a raw log or upload a red CI screenshot.
- Get an immediate, high-signal diagnostic: **Failing Step**, **Root Cause**, **Concrete Fix**, and **Confidence Score**.

---

## ⚡ Dual-Engine Architecture

| Feature | Gemma 4 Engine (`gemma-4-26b-a4b-it`) | Deterministic Rules Fallback |
|---|---|---|
| **Activation** | Set `GEMINI_API_KEY` or `GOOGLE_API_KEY` | Automatic fallback when no key is present |
| **Log Triage** | Semantic reasoning across 12,000+ characters of raw CI trace | High-speed regex matching on verified failure signatures |
| **Screenshot Support** | Multimodal analysis of GitHub Actions UI screenshots | Graceful fallback with actionable guidance |
| **Resilience** | Deep reasoning for bespoke compiler & runtime errors | Zero external dependency; never fails a live demo |

### Supported Failure Signatures (Offline Rules)
1. **TypeScript Typecheck (`tsc --noEmit`, `TS2305`)**: Missing exports, stale type definitions after branch merges.
2. **Unit Test Assertions (`pytest`, `AssertionError`)**: Value mismatches in test suites.
3. **Memory Limits (Exit 134, JavaScript heap out of memory)**: Node bundler OOM memory limit tuning.
4. **Package Resolution (`npm ERR!`, `ERESOLVE`)**: Peer dependency conflicts.

---

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/mangeshraut712/actions-nurse.git
cd actions-nurse

# Create virtual environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment (Optional for Gemma 4)
```bash
export GEMINI_API_KEY="your-gemini-api-key"
```
*(If omitted, Actions Nurse boots seamlessly in deterministic rules mode.)*

### 3. Run the Server
```bash
uvicorn nurse:app --host 127.0.0.1 --port 8787
```
Open **[http://127.0.0.1:8787](http://127.0.0.1:8787)** in your browser.

---

## 🖥️ User Interface & Walkthrough

1. **Sample Fixtures**: Click any fixture chip (`npm-typecheck.txt`, `oom-killed.txt`, `pytest-assert.txt`) to populate realistic CI failures instantly.
2. **One-Click Triage**: Click **Triage with Gemma 4** to execute diagnostics.
3. **Structured Diagnostics**:
   - **Summary**: Plain-English executive briefing of the failure.
   - **Failing Step**: The specific workflow job or command that exited non-zero.
   - **Root Cause**: The technical bug or infrastructure boundary crossed.
   - **Suggested Fix**: Ready-to-apply command or workflow modification.
   - **Engine & Confidence**: Indicates whether Gemma 4 or deterministic rules computed the answer.
4. **Multimodal CI Screenshots**: Attach an image of a red GitHub Actions status dashboard for visual triage.

---

## 🔌 API Reference

### Health Check
```http
GET /api/health
```
**Response:**
```json
{
  "ok": true,
  "gemma_key": true,
  "event": "Hacktoberfest Hack Day Pune x Cloud Native Pune"
}
```

### List Fixtures
```http
GET /api/fixtures
```

### Triage Raw CI Log
```http
POST /api/triage
Content-Type: application/json

{
  "log": "Error: TS2305: Module './types' has no exported member 'ActiveBurnStreakSummary'",
  "model": "gemma-4-26b-a4b-it"
}
```
**Response:**
```json
{
  "summary": "CI failed on TypeScript typecheck (missing module exports).",
  "failing_step": "Typecheck / tsc",
  "root_cause": "TypeScript compile errors — missing exports or stale types after a merge.",
  "suggested_fix": "Align types/scoring exports with imports, or rebase onto main and restore missing named exports.",
  "confidence": "high",
  "engine": "rules",
  "patterns": ["TS2305|has no exported member|tsc --noEmit|error TS\\d+"]
}
```

### Multimodal Screenshot Triage
```http
POST /api/triage-image
Content-Type: multipart/form-data

image: <screenshot.png>
log: <optional contextual log text>
model: "gemma-4-26b-a4b-it"
```

---

## 🏆 MLH Hackathon Prize Targets

- **Best Use of Gemma 4**: Harnesses open-weight Gemma 4's high instruction-following and code reasoning capabilities to parse unstructured terminal stderr, converting raw stack traces into structured, actionable JSON recommendations.
- **Best Open-Source AI Project**: Lightweight, zero-lockin FastAPI backend with a zero-build vanilla JS/CSS frontend. Works completely offline without API keys via an extensible pattern engine.

---

## 📄 License

Distributed under the [MIT License](LICENSE).
