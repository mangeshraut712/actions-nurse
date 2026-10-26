#!/usr/bin/env bash
# End-to-end Agentathon path: deterministic Rules triage plus both sponsor hooks.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON:-python3}"
if [[ -x .venv/bin/python && -z "${PYTHON:-}" ]]; then
  PYTHON_BIN=".venv/bin/python"
fi

BASE="${1:-}"
STATE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/actions-nurse-hmem.XXXXXX")"
SERVER_PID=""
SERVER_LOG="$STATE_DIR/server.log"
ACTIVITY_LOG="demo/activity/trace.jsonl"

cleanup() {
  if [[ -n "$SERVER_PID" ]]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "$STATE_DIR"
}
trap cleanup EXIT

export NURSE_HMEM_DIR="$STATE_DIR/hmem"
export ZETARIS_FIXTURE_MODE=1

if [[ ! -x meterless/node_modules/.bin/tsx || ! -f meterless/vendor/hmem/src/index.ts ]]; then
  echo "H-MEM is not vendored. Run: (cd meterless && npm install && npm run setup)" >&2
  exit 1
fi

if [[ -z "$BASE" ]]; then
  PORT="${NURSE_SMOKE_PORT:-8791}"
  BASE="http://127.0.0.1:${PORT}"
  NURSE_RULES_ONLY=true "$PYTHON_BIN" -m uvicorn nurse:app --host 127.0.0.1 --port "$PORT" >"$SERVER_LOG" 2>&1 &
  SERVER_PID="$!"
  for _ in $(seq 1 50); do
    if curl -fsS "$BASE/api/health" >/dev/null 2>&1; then
      break
    fi
    sleep 0.1
  done
  curl -fsS "$BASE/api/health" >/dev/null
fi

BEFORE_BYTES=0
if [[ -f "$ACTIVITY_LOG" ]]; then
  BEFORE_BYTES=$(wc -c < "$ACTIVITY_LOG")
fi

echo "== health: Rules + sponsor readiness =="
curl -fsS "$BASE/api/health" | "$PYTHON_BIN" -c '
import json, sys
payload = json.load(sys.stdin)
assert payload["rules_only"] is True
assert payload["hmem"]["ready"] is True
assert payload["hmem"]["engine_source"] == "vendor/hmem"
assert payload["zetaris"]["mode"] == "fixture"
print("rules=ready hmem=vendor/hmem zetaris=fixture")
'

echo "== Meterless H-MEM seed + recall =="
SEED_OUTPUT="$(cd meterless && npm --silent run memory -- seed --json)"
printf '%s' "$SEED_OUTPUT" | "$PYTHON_BIN" -c '
import json, sys
payload = json.load(sys.stdin)
assert payload["ok"] is True
assert payload["engine_source"] == "vendor/hmem"
assert "MemoryMiningService" in payload["service"]
assert payload["count"] > 0
print("H-MEM engine source:", payload["engine_source"], "seeded=", payload["count"])
'
ASK_OUTPUT="$(printf '%s' '{"query":"TypeScript missing exports typecheck"}' | (cd meterless && npm --silent run memory -- ask --json))"
printf '%s' "$ASK_OUTPUT" | "$PYTHON_BIN" -c '
import json, sys
payload = json.load(sys.stdin)
assert payload["ok"] is True
assert payload["engine_source"] == "vendor/hmem"
assert payload["service"] == "MemoryRetrievalService"
assert payload["memory_ids"]
print("hmem recall ids=", ",".join(payload["memory_ids"][:3]))
'

echo "== Zetaris read-only preflight (fixture mode) =="
curl -fsS "$BASE/api/zetaris/preflight" | "$PYTHON_BIN" -c '
import json, sys
payload = json.load(sys.stdin)
assert payload["ok"] is True
assert payload["mode"] == "fixture"
assert payload["read_only"] is True
assert len(payload["checks"]) == 2
print("zetaris mode=", payload["mode"], "checks=", ",".join(check["name"] for check in payload["checks"]))
'

echo "== fixture triage: Rules → H-MEM → Zetaris → activity =="
LOG="$(<fixtures/npm-typecheck.txt)"
TRIAGE_OUTPUT="$(curl -fsS -X POST "$BASE/api/triage" -H 'content-type: application/json' \
  -d "$("$PYTHON_BIN" -c 'import json,sys; print(json.dumps({"log":sys.argv[1], "rules_only":True}))' "$LOG")")"
printf '%s' "$TRIAGE_OUTPUT" | "$PYTHON_BIN" -c '
import json, sys
payload = json.load(sys.stdin)
assert payload["engine"] == "rules"
assert payload["failing_step"] == "Typecheck / tsc"
assert payload["zetaris"]["mode"] == "fixture"
assert payload["zetaris"]["result"]["fixture"] == "ci-failure-signatures.json"
assert payload["memory"]["engine_source"] == "vendor/hmem"
assert payload["memory"]["recall_service"] == "MemoryRetrievalService"
assert "MemoryMiningService" in payload["memory"]["remember_service"]
assert payload["activity"]["id"].startswith("act-")
print("triage=rules step=", payload["failing_step"], "activity=", payload["activity"]["id"])
'

AFTER_BYTES=$(wc -c < "$ACTIVITY_LOG")
if (( AFTER_BYTES <= BEFORE_BYTES )); then
  echo "Activity log did not grow: $ACTIVITY_LOG" >&2
  exit 1
fi
rg -q '"event":"triage"' "$ACTIVITY_LOG"
rg -q '"engine_source":"vendor/hmem"' "$ACTIVITY_LOG"
rg -q '"mode":"fixture"' "$ACTIVITY_LOG"
echo "activity=append-only bytes=${BEFORE_BYTES}->${AFTER_BYTES}"
echo "SMOKE_AGENTATHON_OK"
