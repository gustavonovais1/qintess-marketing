#!/usr/bin/env bash
set -e
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &
for i in $(seq 1 20); do
  xdpyinfo -display :99 >/dev/null 2>&1 && break
  sleep 0.5
done
fluxbox &
x11vnc -display :99 -forever -xkb -rfbport 5900 -shared &
websockify -D --web=/usr/share/novnc/ 6080 localhost:5900 &
python -m src.main "$@"