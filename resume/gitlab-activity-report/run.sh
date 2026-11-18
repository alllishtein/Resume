#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "Python is not installed." >&2
  exit 1
fi

"$PY" -m pip install -r requirements.txt || "$PY" -m pip install --user -r requirements.txt
"$PY" fetch_events.py
"$PY" generate_report.py
echo "Wrote report.html"
