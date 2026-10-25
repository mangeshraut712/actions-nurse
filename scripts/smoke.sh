#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-http://127.0.0.1:8787}"
echo "== health =="
curl -fsS "$BASE/api/health" | python3 -m json.tool
echo "== rules-only typecheck =="
LOG=$(python3 -c 'print(open("fixtures/npm-typecheck.txt").read())')
curl -fsS -X POST "$BASE/api/triage" -H 'content-type: application/json' \
  -d "$(python3 -c 'import json,sys; print(json.dumps({"log":sys.argv[1], "rules_only":True}))' "$LOG")" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["engine"] == "rules"; assert d["fix_commands"]; print("rules=", d["engine"], "step=", d["failing_step"])'
echo "== rules-only disk full =="
DISK_LOG=$(python3 -c 'print(open("fixtures/disk-full.txt").read())')
curl -fsS -X POST "$BASE/api/triage" -H 'content-type: application/json' \
  -d "$(python3 -c 'import json,sys; print(json.dumps({"log":sys.argv[1], "rules_only":True}))' "$DISK_LOG")" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["engine"] == "rules"; assert d["failing_step"] == "Runner filesystem"; print("rules=", d["engine"], "step=", d["failing_step"])'
echo "== compare =="
curl -fsS -X POST "$BASE/api/compare" -H 'content-type: application/json' \
  -d "$(python3 -c 'import json,sys; print(json.dumps({"log":sys.argv[1]}))' "$LOG")" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["rules"]["engine"] == "rules"; print("rules=", d["rules"]["engine"], "gemma=", (d.get("gemma") or {}).get("engine"))'
echo "SMOKE_OK"
