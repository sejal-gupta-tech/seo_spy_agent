#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
  exec python3 run_project.py "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python run_project.py "$@"
fi

echo "Python 3 is required but was not found in PATH." >&2
exit 1
