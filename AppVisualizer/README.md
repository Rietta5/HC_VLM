# Hues & Cues VLM Model Visualizer

An interactive web application built with Flask, HTML5, CSS3, and JavaScript for visualizing and analyzing Vision-Language Models (VLM) predictions on the **Hues and Cues** colorboard (16 × 30 grid = 480 cells).

---

## Features

1. **Automatic Model Detection**:
   - Automatically scans and loads any `results_HC_<model_name>.csv` in the folder (e.g. `InternVL3.5-4B`, `InternVL3.5-8B`, etc.).
   - Parses the 100 sample answers per word across all 116 words.

2. **Single Model Visualizer**:
   - **Interactive 16×30 Colorboard Grid**: Renders exact RGB colors loaded from `HC_RGB.csv`.
   - **Heatmap Overlay**: Visualizes prediction density and confidence across the board.
   - **Mode Marker**: Highlights the model's consensus coordinate with a gold crown 👑.
   - **Word Navigator**: Live search filtering, word dropdown, Prev/Next/Random navigation, and Left/Right keyboard arrow support.
   - **Word Summary & Analytics**: Total samples, unique cells chosen, Shannon entropy (spread/uncertainty), and top predicted coordinates with frequency bars and color swatches.

3. **Side-by-Side Model Comparison**:
   - Compares any two models (e.g. `InternVL3.5-4B` vs `InternVL3.5-8B`) side-by-side.
   - Computes distribution overlap percentage, mode agreement (Match vs Divergence), grid distance (cells), and color distance (ΔRGB).

4. **Global Benchmark Table**:
   - Complete table comparing mode predictions across all 116 words.
   - Filter by agreement (Matches vs Differences) or search by word name.
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
