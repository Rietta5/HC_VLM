# Hues & Cues VLM Model Visualizer

An interactive web application built with Flask, HTML5, CSS3, and JavaScript for visualizing and analyzing Vision-Language Models (VLM) predictions on the **Hues and Cues** colorboard (16 × 30 grid = 480 cells).

---

## Features

1. **Automatic Model & Image Format Detection**:
   - Automatically scans and parses any result CSV in the folder (e.g. `results_HC_InternVL3.5-2B_png.csv`, `HC_qwen_3_5_9B_png.csv`, `..._jpeg.csv`, etc.).
   - Extracts both **Model Name** and **Image Format** (`PNG` / `JPEG`).
   - Parses the 100 sample answers per word across all 116 words.

2. **Single Model & Format Visualizer**:
   - **Model & Format Selectors**: Choose model and image format (`PNG` / `JPEG`) directly from dropdowns.
   - **Interactive 16×30 Colorboard Grid**: Renders exact RGB colors loaded from `HC_RGB.csv`.
   - **Heatmap Overlay**: Visualizes prediction density and confidence across the board.
   - **Mode Marker**: Highlights the model's consensus coordinate with a gold crown 👑.
   - **Manhattan Median Marker**: Highlights the spatial median coordinate minimizing Manhattan distance with a target icon 🎯.
   - **Word Navigator**: Live search filtering, word dropdown, Prev/Next/Random navigation, and Left/Right keyboard arrow support.
   - **Word Summary & Analytics**: Total samples, unique cells chosen, Shannon entropy (spread/uncertainty), and top predicted coordinates with frequency bars and color swatches.

3. **Side-by-Side Comparison**:
   - Compares any two datasets (e.g. `InternVL3.5-2B (PNG)` vs `qwen_3_5_9B (PNG)`, or `PNG` vs `JPEG` for the same model).
   - Computes distribution overlap percentage, mode agreement (Match vs Divergence), Manhattan median agreement, grid distance (cells), and color distance (ΔRGB).

4. **Global Benchmark Table**:
   - Complete table comparing mode and Manhattan median predictions across all 116 words.
   - Filter by image format (`All Formats`, `PNG Only`, `JPEG Only`) and agreement status.
   - Jump directly to any word on the board with one click.

---

## How to Run

You can launch the visualizer directly with the launcher script:

```bash
./run_visualizer.sh
```

Or using `uv`:

```bash
uv run --with flask --with pandas python AppVisualizer/app.py
```

Then open your browser at:
`http://localhost:5001` (or the port indicated in the terminal).
