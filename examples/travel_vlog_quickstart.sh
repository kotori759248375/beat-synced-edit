#!/usr/bin/env bash
# Travel vlog quickstart — documents the one-command pipeline.
# Works in Git Bash / WSL / macOS / Linux. On Windows cmd, use the same python lines.
#
# Usage:
#   ./examples/travel_vlog_quickstart.sh              # print commands only
#   ./examples/travel_vlog_quickstart.sh --synth       # make tiny synthetic media (needs ffmpeg)
#   ./examples/travel_vlog_quickstart.sh --run         # synth + full travel_vlog (needs pip deps)

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Prefer venv python if present
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  PY=python
fi

echo "== Travel vlog commands (trip folder + bgm) =="
cat <<'CMDS'

# 1) Install (once)
#    Windows: winget install ffmpeg
#    python -m pip install -r requirements.txt
#    python travel_vlog.py --doctor

# 2) One-command (horizontal)
python travel_vlog.py bgm.mp3 path/to/trip_folder/ -o out/travel_vlog.mp4

# 3) Douyin vertical 9:16
python travel_vlog.py bgm.mp3 path/to/trip_folder/ --vertical -o out/douyin.mp4

# 4) Breathe more / full song
python travel_vlog.py bgm.mp3 path/to/trip_folder/ --beat-stride 3 --full -o out/scenic.mp4

# 5) Same stages manually (upstream CLI unchanged)
python beat_map.py bgm.mp3 -o work/beatmap.json
python clip_tag.py path/to/trip_folder/ -o work/clips.json
python plan_edit.py work/beatmap.json work/clips.json --beat-stride 2 -o work/edl.json
python render_edit.py work/edl.json -a bgm.mp3 -v path/to/first.mp4 -o out/edit.mp4

CMDS

if [[ "${1:-}" == "--synth" || "${1:-}" == "--run" ]]; then
  if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "ffmpeg missing — skip synth. Install ffmpeg, then re-run."
    exit 0
  fi
  DEMO="$ROOT/examples/_travel_synth"
  mkdir -p "$DEMO/clips" "$DEMO/out"
  # Rhythmic 120 BPM click bed (plain sine has 0 detectable beats)
  "$PY" - <<'PY'
import wave
from pathlib import Path
import numpy as np
demo = Path("examples/_travel_synth")
sr, duration, bpm = 22050, 12.0, 120
t = np.arange(int(sr * duration)) / sr
audio = 0.05 * np.sin(2 * np.pi * 110 * t)
interval = 60.0 / bpm
i = 0.0
while i < duration:
    n0 = int(i * sr)
    n1 = min(len(audio), n0 + int(0.04 * sr))
    audio[n0:n1] += np.sin(2 * np.pi * 880 * (t[n0:n1] - i)) * np.linspace(1, 0, n1 - n0)
    i += interval
audio = np.clip(audio, -1, 1)
with wave.open(str(demo / "bgm.wav"), "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((audio * 32767).astype(np.int16).tobytes())
print("wrote", demo / "bgm.wav")
PY
  ffmpeg -y -i "$DEMO/bgm.wav" -c:a libmp3lame "$DEMO/bgm.mp3" 2>/dev/null
  ffmpeg -y -f lavfi -i "color=c=blue:s=1280x720:d=4" -f lavfi -i "sine=frequency=200:duration=4" \
    -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "$DEMO/clips/establishing.mp4" 2>/dev/null
  ffmpeg -y -f lavfi -i "testsrc2=s=1280x720:r=30:d=5" -f lavfi -i "sine=frequency=600:duration=5" \
    -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "$DEMO/clips/landmark.mp4" 2>/dev/null
  echo "Synthetic media at $DEMO"
  echo "Try: $PY travel_vlog.py $DEMO/bgm.mp3 $DEMO/clips -o $DEMO/out/vlog.mp4 --beat-stride 2 --full"
  if [[ "${1:-}" == "--run" ]]; then
    "$PY" travel_vlog.py "$DEMO/bgm.mp3" "$DEMO/clips" -o "$DEMO/out/vlog.mp4" --beat-stride 2 --calm-open 1 --full
  fi
fi
