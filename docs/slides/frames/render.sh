#!/usr/bin/env bash
# Render the still frames to 1920x1080 PNGs with headless Chrome (throwaway profile).
# Usage: bash docs/slides/frames/render.sh
# Headless Chrome on macOS can stay alive after writing the screenshot, so we wait for
# the file and then stop that Chrome instance (only the one using our temp profile).
set -euo pipefail
cd "$(dirname "$0")"
if [ -z "${CHROME:-}" ]; then
  for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
           "/c/Program Files/Google/Chrome/Application/chrome.exe" \
           "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"; do
    [ -x "$c" ] && CHROME="$c" && break
  done
fi
# Windows (Git Bash): Chrome/Edge need Windows-style paths
winpath() { if command -v cygpath >/dev/null; then cygpath -m "$1"; else echo "$1"; fi; }
for f in frame_a_problem frame_b_stack frame_d_question frame_e_sourcespot frame_f_no frame_g_end frame_h_name; do
  out="$PWD/../$f.png"
  rm -f "$out"
  profile="$(mktemp -d)"
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --user-data-dir="$(winpath "$profile")" --window-size=1920,1080 --virtual-time-budget=3000 \
    --screenshot="$(winpath "$out")" "file:///$(winpath "$PWD" | sed 's|^/||')/$f.html" >/dev/null 2>&1 &
  for _ in $(seq 1 60); do [ -s "$out" ] && break; sleep 0.5; done
  sleep 0.5
  if command -v pkill >/dev/null; then pkill -f "user-data-dir=$profile" || true; fi
  rm -rf "$profile"
  [ -s "$out" ] && echo "wrote docs/slides/$f.png" || { echo "failed: $f"; exit 1; }
done
