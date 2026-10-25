#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-http://127.0.0.1:8787}"
echo "== health =="
curl -fsS "$BASE/api/health" | python3 -m json.tool
echo "== triage fixture =="
LOG=$(python3 -c 'print(open("fixtures/npm-typecheck.txt").read())')
curl -fsS -X POST "$BASE/api/triage" -H 'content-type: application/json' \
  -d "$(python3 -c 'import json,sys; print(json.dumps({"log":sys.argv[1]}))' "$LOG")" \
  | python3 -m json.tool | head -40
echo "== compare =="
curl -fsS -X POST "$BASE/api/compare" -H 'content-type: application/json' \
  -d "$(python3 -c 'import json,sys; print(json.dumps({"log":sys.argv[1]}))' "$LOG")" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print("rules=", d["rules"]["engine"], "gemma=", (d.get("gemma") or {}).get("engine"), (d.get("gemma") or {}).get("model"))'
echo "SMOKE_OK"
