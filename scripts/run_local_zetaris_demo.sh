#!/usr/bin/env bash
# Start Actions Nurse against an already-seeded local Zetaris evaluation stack.
# Credentials are read from the platform .env into this process only; nothing is
# printed, written into this repository, or exposed beyond loopback.
set -euo pipefail

if [[ -z "${ZETARIS_PLATFORM_DIR:-}" ]]; then
  echo "Set ZETARIS_PLATFORM_DIR to the local Zetaris bundle directory." >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ZETARIS_LOCAL_ENV_FILE:-$ZETARIS_PLATFORM_DIR/.env}"
[[ -f "$ENV_FILE" ]] || { echo "Missing local Zetaris environment file." >&2; exit 1; }
DEMO_TABLE="actions_nurse_demo_20261027_f9de7301.ci_failure_signatures"
DEMO_PROVENANCE="synthetic-local-demo"

if [[ -n "${ZETARIS_CI_EVIDENCE_TABLE+x}" && "$ZETARIS_CI_EVIDENCE_TABLE" != "$DEMO_TABLE" ]]; then
  echo "Refusing an inherited noncanonical owned demo identity." >&2
  exit 2
fi
if [[ -n "${ZETARIS_EVIDENCE_PROVENANCE+x}" && "$ZETARIS_EVIDENCE_PROVENANCE" != "$DEMO_PROVENANCE" ]]; then
  echo "Refusing an inherited noncanonical owned demo identity." >&2
  exit 2
fi

read_env_value() {
  local key="$1"
  sed -n "s/^${key}=//p" "$ENV_FILE" | tail -1
}

export ZETARIS_LOCAL_UI_URL="${ZETARIS_LOCAL_UI_URL:-http://127.0.0.1:3000}"
export ZETARIS_LOCAL_ADMIN_EMAIL="$(read_env_value ZETARIS_ADMIN_EMAIL)"
export ZETARIS_LOCAL_ADMIN_PASSWORD="$(read_env_value ZETARIS_ADMIN_PASSWORD)"
export ZETARIS_CI_EVIDENCE_TABLE="$DEMO_TABLE"
export ZETARIS_EVIDENCE_PROVENANCE="$DEMO_PROVENANCE"
: "${ZETARIS_LOCAL_ADMIN_EMAIL:?Missing local administrator email.}"
: "${ZETARIS_LOCAL_ADMIN_PASSWORD:?Missing local administrator password.}"

# This launcher is a demo helper. Keep its new activity records outside the
# repository unless a caller deliberately supplies a different local path.
if [[ -z "${NURSE_ACTIVITY_LOG:-}" ]]; then
  RUNTIME_STATE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/actions-nurse-zetaris-demo.XXXXXX")"
  export NURSE_ACTIVITY_LOG="$RUNTIME_STATE_DIR/trace.jsonl"
fi

cd "$ROOT"
exec "${PYTHON:-python3}" -m uvicorn nurse:app --host 127.0.0.1 --port "${NURSE_PORT:-8787}"
