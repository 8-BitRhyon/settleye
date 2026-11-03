#!/usr/bin/env bash
# One command that runs everything a judge would want to see.
#
#   ./tools/judge_audit.sh
#
# Requires uv (backend) and node (frontend). The test, eval-replay, comparison,
# and build steps need no API keys and no model access. The final sweep does call
# the live model, so skip it if you have no BASETEN_API_KEY in .env.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

bold() { printf '\n\033[1m%s\033[0m\n' "$1"; }

bold "Backend: install and test"
( cd backend && uv sync --quiet && uv run pytest -q )

bold "Backend: eval replay against recorded live model output"
( cd backend && uv run pytest -q tests/test_eval_replay.py )

bold "Model comparison table"
python3 bench/score.py

bold "Frontend: install, test, typecheck, build"
( cd frontend && npm ci --silent && npm test --silent && npm run typecheck --silent && npm run build --silent )

bold "Secret scan (tracked files, working tree)"
if command -v gitleaks >/dev/null 2>&1; then
  gitleaks detect --no-git --redact -v || { echo "secret scan failed"; exit 1; }
else
  echo "gitleaks not installed; CI runs it on every push."
fi

bold "Daemon sweep over the eval set (live model, mock ledger)"
( cd backend && uv run python -m app.daemon --dir ../fixtures/eval --ledger mock )

bold "Done"
echo "Landing page: https://8-bitrhyon.github.io/settleye/landing.html"
echo "Inbox with a rendered drift: https://8-bitrhyon.github.io/settleye/index.html?sample=1"
