#!/usr/bin/env bash
# Script to launch Hues & Cues VLM Visualizer

cd "$(dirname "$0")"

echo "=========================================="
echo " Starting Hues & Cues VLM Model Visualizer"
echo "=========================================="

if command -v uv >/dev/null 2>&1; then
    uv run --with flask --with pandas python AppVisualizer/app.py
elif [ -x "$HOME/.local/bin/uv" ]; then
    "$HOME/.local/bin/uv" run --with flask --with pandas python AppVisualizer/app.py
else
    python3 AppVisualizer/app.py
fi
