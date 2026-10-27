#!/usr/bin/env bash
# Fresh-store H-MEM proof: pass one remembers a prior triage; pass two recalls it.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" && -z "${PYTHON:-}" ]]; then
  PYTHON_BIN="$ROOT/.venv/bin/python"
fi

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Fresh-store, two-pass H-MEM prior triage provenance proof.

Pass one records the deterministic typecheck triage. Pass two must retrieve the
same memory ID. The output shows remembered and recalled IDs as provenance; it
does not claim that a repair was applied or that diagnostic correctness changed.

The script never installs H-MEM. If the local Meterless vendor source is absent,
it reports setup_required rather than manufacturing a memory result.
EOF
  exit 0
fi

cd "$ROOT"
exec "$PYTHON_BIN" scripts/hmem_two_pass_demo.py
