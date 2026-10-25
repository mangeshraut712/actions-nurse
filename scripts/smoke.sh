#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-http://127.0.0.1:8787}"
RULES_ONLY=true
echo "== Gemma category validator unit tests =="
TEST_PYTHON="${PYTHON:-python3}"
if [[ -x .venv/bin/python && -z "${PYTHON:-}" ]]; then TEST_PYTHON=".venv/bin/python"; fi
"$TEST_PYTHON" -m unittest discover -s tests -v
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
echo "== rules-only screenshot triage =="
curl -fsS -X POST "$BASE/api/triage-image" \
  -F 'log=<fixtures/checkout-auth.txt' \
  -F 'image=@docs/fixtures-img/red-actions-permission-failure.png;type=image/png' \
  -F 'rules_only=true' \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["engine"] == "rules"; assert d["failing_step"] == "Checkout / repository access"; print("rules=", d["engine"], "step=", d["failing_step"])'
echo "== rules-only screenshot compare =="
curl -fsS -X POST "$BASE/api/compare-image" \
  -F 'log=<fixtures/checkout-auth.txt' \
  -F 'image=@docs/fixtures-img/red-actions-permission-failure.png;type=image/png' \
  -F 'rules_only=true' \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["rules"]["engine"] == "rules"; assert d["rules"]["failing_step"] == "Checkout / repository access"; assert d["gemma"] is None; print("rules=", d["rules"]["engine"], "gemma=skipped")'
echo "== compare =="
curl -fsS -X POST "$BASE/api/compare" -H 'content-type: application/json' \
  -d "$(python3 -c 'import json,sys; print(json.dumps({"log":sys.argv[1], "rules_only":sys.argv[2].lower() in ("1", "true", "yes")}))' "$LOG" "$RULES_ONLY")" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["rules"]["engine"] == "rules"; assert d.get("gemma") is None; print("rules=", d["rules"]["engine"], "gemma=skipped")'
if [[ "${NURSE_PROBE_GEMMA:-0}" == "1" ]]; then
  echo "== optional Gemma probe (3s client cap) =="
  curl --max-time 3 -sS -X POST "$BASE/api/triage" -H 'content-type: application/json' \
    -d "$(python3 -c 'import json,sys; print(json.dumps({"log":sys.argv[1], "rules_only":False}))' "$LOG")" \
    | python3 -c 'import json,sys; print("engine=", json.load(sys.stdin).get("engine"))' || echo "Gemma probe timed out or is unavailable (expected without a key)."
fi
echo "SMOKE_OK"
