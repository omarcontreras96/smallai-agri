#!/usr/bin/env bash
# Render the still frames to 1920x1080 PNGs with headless Chrome (throwaway profile).
# Usage: bash docs/slides/frames/render.sh
# Headless Chrome on macOS can stay alive after writing the screenshot, so we wait for
# the file and then stop that Chrome instance (only the one using our temp profile).
set -euo pipefail
cd "$(dirname "$0")"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
for f in frame_a_problem frame_b_stack; do
  out="$PWD/../$f.png"
  rm -f "$out"
  profile="$(mktemp -d)"
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --user-data-dir="$profile" --window-size=1920,1080 \
    --screenshot="$out" "file://$PWD/$f.html" >/dev/null 2>&1 &
  for _ in $(seq 1 60); do [ -s "$out" ] && break; sleep 0.5; done
  sleep 0.5
  pkill -f "user-data-dir=$profile" || true
  rm -rf "$profile"
  [ -s "$out" ] && echo "wrote docs/slides/$f.png" || { echo "failed: $f"; exit 1; }
done
