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

read_env_value() {
  local key="$1"
  sed -n "s/^${key}=//p" "$ENV_FILE" | tail -1
}

export ZETARIS_LOCAL_UI_URL="${ZETARIS_LOCAL_UI_URL:-http://127.0.0.1:3000}"
export ZETARIS_LOCAL_ADMIN_EMAIL="$(read_env_value ZETARIS_ADMIN_EMAIL)"
export ZETARIS_LOCAL_ADMIN_PASSWORD="$(read_env_value ZETARIS_ADMIN_PASSWORD)"
export ZETARIS_CI_EVIDENCE_TABLE="${ZETARIS_CI_EVIDENCE_TABLE:-actions_nurse_demo_20261027_f9de7301.ci_failure_signatures}"
export ZETARIS_EVIDENCE_PROVENANCE="${ZETARIS_EVIDENCE_PROVENANCE:-synthetic-local-demo}"
: "${ZETARIS_LOCAL_ADMIN_EMAIL:?Missing local administrator email.}"
: "${ZETARIS_LOCAL_ADMIN_PASSWORD:?Missing local administrator password.}"

cd "$ROOT"
exec "${PYTHON:-python3}" -m uvicorn nurse:app --host 127.0.0.1 --port "${NURSE_PORT:-8787}"
