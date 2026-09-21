#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$ROOT/Sonya_Podsolnukh_scenariy_den_rozhdeniya.pdf}"
HTML="file://$ROOT/index.html"
google-chrome \
  --headless \
  --disable-gpu \
  --no-pdf-header-footer \
  --hide-scrollbars \
  --virtual-time-budget=8000 \
  --print-to-pdf="$OUT" \
  "$HTML"
echo "Wrote $OUT"
pdfinfo "$OUT" 2>/dev/null || python3 - <<PY
from pathlib import Path
p = Path("$OUT")
print("size", p.stat().st_size)
PY
