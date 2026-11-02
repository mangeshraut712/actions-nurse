#!/usr/bin/env bash
# Seed the explicitly synthetic, local-only Actions Nurse Zetaris demo corpus.
# This script intentionally requires --apply and refuses to overwrite a
# different file or table. It never sources or prints the platform .env file.
set -euo pipefail

if [[ "${1:-}" != "--apply" || "$#" -ne 1 ]]; then
  echo "Refusing to seed demo data without the explicit --apply flag." >&2
  echo "Usage: ZETARIS_PLATFORM_DIR=/path/to/zetaris-platform $0 --apply" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLATFORM_DIR="${ZETARIS_PLATFORM_DIR:?Set ZETARIS_PLATFORM_DIR to the local Zetaris bundle directory.}"
ENV_FILE="${ZETARIS_LOCAL_ENV_FILE:-$PLATFORM_DIR/.env}"
JDBC_JAR="$PLATFORM_DIR/jdbc/ndp-jdbc-driver-2.4.3.1-7eff043-driver.jar"
CSV_SOURCE="$ROOT/demo/zetaris/ci_failure_signatures.csv"
CONTAINER_DIR="/home/zetaris/customer-data/shared/actions-nurse-demo"
CONTAINER_CSV="$CONTAINER_DIR/ci_failure_signatures.csv"

[[ -f "$ENV_FILE" ]] || { echo "Missing local Zetaris environment file." >&2; exit 1; }
[[ -f "$JDBC_JAR" ]] || { echo "Missing bundled Zetaris JDBC driver." >&2; exit 1; }
[[ -f "$CSV_SOURCE" ]] || { echo "Missing tracked synthetic demo CSV." >&2; exit 1; }

read_env_value() {
  local key="$1"
  sed -n "s/^${key}=//p" "$ENV_FILE" | tail -1
}

export ZETARIS_LOCAL_ADMIN_EMAIL="$(read_env_value ZETARIS_ADMIN_EMAIL)"
export ZETARIS_LOCAL_ADMIN_PASSWORD="$(read_env_value ZETARIS_ADMIN_PASSWORD)"
: "${ZETARIS_LOCAL_ADMIN_EMAIL:?Missing local administrator email.}"
: "${ZETARIS_LOCAL_ADMIN_PASSWORD:?Missing local administrator password.}"

DRIVER_ID="$(cd "$PLATFORM_DIR" && docker compose ps -q driver)"
[[ -n "$DRIVER_ID" ]] || { echo "The local Zetaris driver is not running." >&2; exit 1; }

LOCAL_SHA="$(shasum -a 256 "$CSV_SOURCE" | awk '{print $1}')"
if ! REMOTE_STATE="$(docker exec "$DRIVER_ID" sh -c 'if test -e "$1"; then printf present; else printf absent; fi' sh "$CONTAINER_CSV")"; then
  echo "Cannot verify checksum because the local Zetaris container could not be inspected." >&2
  exit 1
fi
REMOTE_SHA=""
if [[ "$REMOTE_STATE" == "present" ]]; then
  if ! REMOTE_SHA="$(docker exec "$DRIVER_ID" sha256sum "$CONTAINER_CSV" | awk '{print $1}')"; then
    echo "Cannot verify checksum for the existing owned demo CSV; refusing to replace it." >&2
    exit 1
  fi
  if [[ -z "$REMOTE_SHA" ]]; then
    echo "Cannot verify checksum for the existing owned demo CSV; refusing to replace it." >&2
    exit 1
  fi
fi
if [[ "$REMOTE_STATE" != "present" && "$REMOTE_STATE" != "absent" ]]; then
  echo "Cannot verify checksum because the local Zetaris container returned an unknown file state." >&2
  exit 1
fi
if [[ -n "$REMOTE_SHA" && "$REMOTE_SHA" != "$LOCAL_SHA" ]]; then
  echo "Refusing to replace a different file in the owned demo directory." >&2
  exit 1
fi
if [[ "$REMOTE_STATE" == "absent" ]]; then
  docker exec "$DRIVER_ID" mkdir -p "$CONTAINER_DIR"
  docker cp "$CSV_SOURCE" "$DRIVER_ID:$CONTAINER_CSV"
fi

BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/actions-nurse-zetaris-seed.XXXXXX")"
cleanup() { rm -rf "$BUILD_DIR"; }
trap cleanup EXIT

javac -proc:none -cp "$JDBC_JAR" -d "$BUILD_DIR" "$ROOT/scripts/ZetarisDemoSeed.java"
java -cp "$BUILD_DIR:$JDBC_JAR" ZetarisDemoSeed
