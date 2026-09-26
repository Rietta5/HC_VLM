import os
import glob
import re
import math
import numpy as np
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def natural_sort_key(s):
    """Sort strings containing numbers in human/natural order (e.g. 2B, 4B, 8B, 14B)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]

def resolve_path(path):
    if os.path.isabs(path):
        return path
    if os.path.exists(path):
        return path
    candidate = os.path.join(BASE_DIR, path)
    if os.path.exists(candidate):
        return candidate
    parent_public = os.path.join(BASE_DIR, "..", "public", path)
    if os.path.exists(parent_public):
        return parent_public
    return path

def parse_csv_filename(filename):
    """
    Extracts model name and image format (png/jpeg) from a CSV filename.
    Examples:
      - 'HC_qwen_3_5_9B_png.csv' -> ('qwen_3_5_9B', 'png')
      - 'results_HC_InternVL3.5-2B_png.csv' -> ('InternVL3.5-2B', 'png')
      - 'results_HC_InternVL3.5-8B_jpeg.csv' -> ('InternVL3.5-8B', 'jpeg')
      - 'results_HC_InternVL3.5-4B.csv' -> ('InternVL3.5-4B', 'png')
    """
    name = filename
    if name.endswith('.csv'):
        name = name[:-4]
        
    img_format = 'png'
    if name.lower().endswith('_png'):
        img_format = 'png'
        name = name[:-4]
    elif name.lower().endswith('.png'):
        img_format = 'png'
        name = name[:-4]
    elif name.lower().endswith('_jpeg'):
        img_format = 'jpeg'
        name = name[:-5]
    elif name.lower().endswith('.jpeg'):
        img_format = 'jpeg'
        name = name[:-5]
    elif name.lower().endswith('_jpg'):
        img_format = 'jpeg'
        name = name[:-4]
    elif name.lower().endswith('.jpg'):
        img_format = 'jpeg'
        name = name[:-4]
        
    # Strip common prefixes
    for prefix in ['results_HC_', 'results_', 'HC_']:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
            
    return name, img_format

class DataLoader:
    def __init__(self, data_dir=None, rgb_path="HC_RGB.csv"):
        self.data_dir = data_dir if data_dir and os.path.isabs(data_dir) else BASE_DIR
        self.rgb_path = resolve_path(rgb_path)
        
        self.board_cells = []
        self.board_map = {}
        self.row_letters = []
        self.inv_row_map = {}
        self.col_numbers = list(range(1, 31))
        
        # Key: (model_name, img_format) -> pd.DataFrame
        self.datasets = {}
        
        self.load_board()
        self.load_models()

    def load_board(self):
        """Loads RGB board coordinate mappings (16 rows A-P, 30 cols 1-30)."""
        if not os.path.exists(self.rgb_path):
            print(f"[DataLoader] Warning: RGB map not found at {self.rgb_path}")
            return
            
        rgb_df = pd.read_csv(self.rgb_path)
        rgb_df['coordenada_x'] = rgb_df['coordenada_x'].astype(str).str.strip().str.upper()
        rgb_df['coordenada_y'] = rgb_df['coordenada_y'].astype(int)
        
        self.row_letters = sorted(rgb_df['coordenada_x'].unique())
        row_map = {r: i for i, r in enumerate(self.row_letters)}
        self.inv_row_map = {i: r for i, r in enumerate(self.row_letters)}
        
        for _, row in rgb_df.iterrows():
            x = row['coordenada_x']
            y = int(row['coordenada_y'])
            coord = f"{x}{y}"
            r, g, b = int(row['R']), int(row['G']), int(row['B'])
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            
            cell_data = {
                "coord": coord,
                "row": x,
                "col": y,
                "row_idx": row_map[x],
                "col_idx": y - 1,
                "r": r,
                "g": g,
                "b": b,
                "hex": hex_color
            }
            self.board_cells.append(cell_data)
            self.board_map[coord] = cell_data

    def load_models(self):
        """Discovers and loads all CSV result files in data_dir."""
        pattern = os.path.join(self.data_dir, "*.csv")
        csv_files = [f for f in glob.glob(pattern) if os.path.basename(f) != "HC_RGB.csv"]
        
        self.datasets = {}
        for file_path in sorted(csv_files, key=natural_sort_key):
            filename = os.path.basename(file_path)
            model_name, img_format = parse_csv_filename(filename)
                
            try:
                df = pd.read_csv(file_path)
                if 'Palabra' in df.columns:
                    # Normalize word: strip whitespace unless it's only spaces (then keep single space)
                    df['Palabra'] = df['Palabra'].fillna(' ').astype(str).apply(lambda x: x.strip().upper() if x.strip() else ' ')
                self.datasets[(model_name, img_format)] = df
                print(f"[DataLoader] Loaded model '{model_name}' [{img_format.upper()}] ({len(df)} words) from {filename}")
            except Exception as e:
                print(f"[DataLoader] Error loading {filename}: {e}")

    def get_models(self):
        """Returns unique list of model names sorted naturally."""
        models = set(m for (m, fmt) in self.datasets.keys())
        return sorted(list(models), key=natural_sort_key)

    def get_formats(self):
        """Returns unique list of image formats available."""
        formats = set(fmt for (m, fmt) in self.datasets.keys())
        return sorted(list(formats))

    def get_model_formats_map(self):
        """Returns map of { model_name: [list of available formats] }."""
        mapping = {}
        for (m, fmt) in self.datasets.keys():
            if m not in mapping:
                mapping[m] = []
            mapping[m].append(fmt)
        for m in mapping:
            mapping[m].sort()
        return mapping

    def get_entries(self):
        """Returns list of all available (model, format) combinations."""
        entries = []
        for (m, fmt) in sorted(self.datasets.keys(), key=lambda x: (natural_sort_key(x[0]), x[1])):
            entries.append({
                "model": m,
                "format": fmt,
                "key": f"{m}__{fmt}",
                "display_name": f"{m} ({fmt.upper()})"
            })
        return entries

    def get_board_grid(self):
        """Returns board setup details including dimensions and cell info."""
        return {
            "rows": self.row_letters,
            "cols": self.col_numbers,
            "total_cells": len(self.board_cells),
            "cells": self.board_cells,
            "cell_map": self.board_map
        }

    def _get_answers_list(self, df_row):
        """Extracts and normalizes answers from a dataframe row."""
        cols = [c for c in df_row.index if c != 'Palabra']
        answers = []
        for c in cols:
            val = str(df_row[c]).strip().upper()
            if val and val != 'NAN' and val != 'NONE':
                answers.append(val)
        return answers

    def _calc_manhattan_median(self, answers):
        """
        Computes the spatial median grid coordinate that minimizes the sum of Manhattan distances:
        argmin_{(r, c) \in Board} \sum_{i=1}^N (|r - r_i| + |c - c_i|)
        Returns (median_coord, avg_manhattan_distance).
        """
        valid_coords = [a for a in answers if a in self.board_map]
        if not valid_coords:
            return None, 0.0
            
        rows = [self.board_map[c]['row_idx'] for c in valid_coords]
        cols = [self.board_map[c]['col_idx'] for c in valid_coords]
        r_mean = sum(rows) / len(rows)
        c_mean = sum(cols) / len(cols)
        
        # 1D search for row minimizing sum of distances (with tie-breaker closest to mean)
        best_r = min(range(len(self.row_letters)), key=lambda r: (sum(abs(r - ri) for ri in rows), abs(r - r_mean)))
        # 1D search for col minimizing sum of distances (with tie-breaker closest to mean)
        best_c = min(range(len(self.col_numbers)), key=lambda c: (sum(abs(c - ci) for ci in cols), abs(c - c_mean)))
        
        best_coord = f"{self.inv_row_map[best_r]}{best_c + 1}"
        total_dist = sum(abs(best_r - ri) + abs(best_c - ci) for ri, ci in zip(rows, cols))
        avg_dist = round(total_dist / len(valid_coords), 2)
        
        return best_coord, avg_dist

    def get_words_list(self):
        """Returns list of unique words with summary stats across all datasets."""
        if not self.datasets:
            return []
            
        all_words = set()
        for df in self.datasets.values():
            if 'Palabra' in df.columns:
                all_words.update(df['Palabra'].dropna().tolist())
                
        # Sort words alphabetically, putting space/blank at beginning or end
        sorted_words = sorted(list(all_words), key=lambda x: (x == ' ', x))
        words_summary = []
        
        entries = self.get_entries()
        for word in sorted_words:
            model_summaries = {}
            for entry in entries:
                key = entry["key"]
                m_tuple = (entry["model"], entry["format"])
                df = self.datasets.get(m_tuple)
                if df is None:
                    continue
                match = df[df['Palabra'] == word]
                if not match.empty:
                    answers = self._get_answers_list(match.iloc[0])
                    if answers:
                        from collections import Counter
                        counts = Counter(answers)
                        mode_coord, mode_count = counts.most_common(1)[0]
                        cell_mode = self.board_map.get(mode_coord, {})
                        
                        med_coord, med_dist = self._calc_manhattan_median(answers)
                        cell_med = self.board_map.get(med_coord, {})
                        
                        model_summaries[key] = {
                            "model_name": entry["model"],
                            "img_format": entry["format"],
                            "display_name": entry["display_name"],
                            "total_samples": len(answers),
                            "unique_coords": len(counts),
                            "mode_coord": mode_coord,
                            "mode_count": mode_count,
                            "mode_percentage": round((mode_count / len(answers)) * 100, 1),
                            "mode_hex": cell_mode.get('hex', '#888888'),
                            "median_coord": med_coord,
                            "median_hex": cell_med.get('hex', '#888888'),
                            "median_avg_dist": med_dist
                        }
                        
            words_summary.append({
                "word": word,
                "models": model_summaries
            })
            
        return words_summary

    def _calc_grid_distance(self, coord_a, coord_b):
        """Euclidean distance on the 16x30 board grid."""
        cell_a = self.board_map.get(coord_a)
        cell_b = self.board_map.get(coord_b)
        if not cell_a or not cell_b:
            return None
        dr = cell_a['row_idx'] - cell_b['row_idx']
        dc = cell_a['col_idx'] - cell_b['col_idx']
        return round(math.sqrt(dr*dr + dc*dc), 2)

    def _calc_rgb_distance(self, coord_a, coord_b):
        """Color distance (Euclidean in RGB space)."""
        cell_a = self.board_map.get(coord_a)
        cell_b = self.board_map.get(coord_b)
        if not cell_a or not cell_b:
            return None
        dr = cell_a['r'] - cell_b['r']
        dg = cell_a['g'] - cell_b['g']
        db = cell_a['b'] - cell_b['b']
        return round(math.sqrt(dr*dr + dg*dg + db*db), 1)

    def _calc_entropy(self, counts, total):
        """Shannon entropy (spread/uncertainty metric)."""
        if total == 0:
            return 0.0
        entropy = 0.0
        for count in counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        return round(entropy, 2)

    def get_word_analysis(self, word_name, model_name=None, img_format=None):
        """
        Returns full response analysis for a single word.
        Can filter by specific model_name and/or img_format.
        """
        if word_name is None:
            return None
        word_norm = word_name.strip().upper() if word_name.strip() else ' '
        
        entries = self.get_entries()
        
        # Filter entries if requested
        if model_name and img_format:
            target_key = f"{model_name}__{img_format}"
            entries_to_process = [e for e in entries if e["key"] == target_key]
            # Fallback if format not exact match
            if not entries_to_process:
                entries_to_process = [e for e in entries if e["model"] == model_name]
        elif model_name:
            entries_to_process = [e for e in entries if e["model"] == model_name]
        elif img_format:
            entries_to_process = [e for e in entries if e["format"] == img_format]
        else:
            entries_to_process = entries
            
        results = {}
        for entry in entries_to_process:
            key = entry["key"]
            m_tuple = (entry["model"], entry["format"])
            df = self.datasets.get(m_tuple)
            if df is None:
                continue
            match = df[df['Palabra'] == word_norm]
            if match.empty:
                continue
                
            answers = self._get_answers_list(match.iloc[0])
            total = len(answers)
            if total == 0:
                continue
                
            from collections import Counter
            counts_dict = dict(Counter(answers))
            max_count = max(counts_dict.values()) if counts_dict else 0
            
            top_coords = []
            for coord, count in sorted(counts_dict.items(), key=lambda x: x[1], reverse=True):
                cell = self.board_map.get(coord, {})
                top_coords.append({
                    "coordinate": coord,
                    "count": count,
                    "percentage": round((count / total) * 100, 1),
                    "hex": cell.get('hex', '#888888'),
                    "rgb": [cell.get('r', 0), cell.get('g', 0), cell.get('b', 0)]
                })
                
            mode_coord = top_coords[0]["coordinate"] if top_coords else None
            mode_hex = top_coords[0]["hex"] if top_coords else "#888888"
            mode_percentage = top_coords[0]["percentage"] if top_coords else 0
            
            # Manhattan median calculation
            median_coord, median_avg_dist = self._calc_manhattan_median(answers)
            median_cell = self.board_map.get(median_coord, {}) if median_coord else {}
            median_hex = median_cell.get('hex', '#888888')
            median_count = counts_dict.get(median_coord, 0)
            median_percentage = round((median_count / total) * 100, 1)
            
            entropy = self._calc_entropy(counts_dict, total)
            
            results[key] = {
                "key": key,
                "model_name": entry["model"],
                "img_format": entry["format"],
                "display_name": entry["display_name"],
                "total_samples": total,
                "unique_coords_count": len(counts_dict),
                "entropy": entropy,
                "counts_per_coord": counts_dict,
                "max_count": max_count,
                "mode_coord": mode_coord,
                "mode_hex": mode_hex,
                "mode_percentage": mode_percentage,
                "median_coord": median_coord,
                "median_hex": median_hex,
                "median_avg_dist": median_avg_dist,
                "median_count": median_count,
                "median_percentage": median_percentage,
                "top_coords": top_coords
            }
            
        # Single requested key return
        if model_name and img_format:
            target_key = f"{model_name}__{img_format}"
            if target_key in results:
                single = results[target_key]
                single["word"] = word_norm
                return single
                
        # Comparison logic between first two entries if available
        comparison = {}
        keys_list = list(results.keys())
        if len(keys_list) >= 2:
            k1, k2 = keys_list[0], keys_list[1]
            c1 = results[k1]["counts_per_coord"]
            c2 = results[k2]["counts_per_coord"]
            t1 = results[k1]["total_samples"]
            t2 = results[k2]["total_samples"]
            
            all_coords = set(c1.keys()).union(set(c2.keys()))
            overlap_pct = sum(min(c1.get(k, 0)/t1, c2.get(k, 0)/t2) for k in all_coords) * 100
            
            mode1 = results[k1]["mode_coord"]
            mode2 = results[k2]["mode_coord"]
            med1 = results[k1]["median_coord"]
            med2 = results[k2]["median_coord"]
            
            grid_dist = self._calc_grid_distance(mode1, mode2) if mode1 and mode2 else None
            rgb_dist = self._calc_rgb_distance(mode1, mode2) if mode1 and mode2 else None
            
            med_grid_dist = self._calc_grid_distance(med1, med2) if med1 and med2 else None
            med_rgb_dist = self._calc_rgb_distance(med1, med2) if med1 and med2 else None
            
            comparison = {
                "dataset_a": k1,
                "dataset_b": k2,
                "model_a": results[k1]["model_name"],
                "format_a": results[k1]["img_format"],
                "model_b": results[k2]["model_name"],
                "format_b": results[k2]["img_format"],
                "overlap_percentage": round(overlap_pct, 1),
                "mode_agreement": mode1 == mode2,
                "mode_grid_distance": grid_dist,
                "mode_rgb_distance": rgb_dist,
                "median_agreement": med1 == med2,
                "median_grid_distance": med_grid_dist,
                "median_rgb_distance": med_rgb_dist
            }
            
        return {
            "word": word_norm,
            "models": results,
            "comparison": comparison
        }

    def get_benchmark_summary(self, format_filter=None):
        """Returns full comparative benchmark data across all words."""
        words_list = self.get_words_list()
        entries = self.get_entries()
        
        if format_filter and format_filter.lower() != 'all':
            entries = [e for e in entries if e["format"] == format_filter.lower()]
            
        summary_rows = []
        for item in words_list:
            word = item['word']
            row = {"word": word}
            
            modes = {}
            medians = {}
            for entry in entries:
                key = entry["key"]
                if key in item['models']:
                    m_stat = item['models'][key]
                    row[f"{key}_mode"] = m_stat['mode_coord']
                    row[f"{key}_pct"] = m_stat['mode_percentage']
                    row[f"{key}_hex"] = m_stat['mode_hex']
                    row[f"{key}_median"] = m_stat['median_coord']
                    row[f"{key}_med_hex"] = m_stat['median_hex']
                    row[f"{key}_med_dist"] = m_stat['median_avg_dist']
                    modes[key] = m_stat['mode_coord']
                    medians[key] = m_stat['median_coord']
                else:
                    row[f"{key}_mode"] = "-"
                    row[f"{key}_pct"] = 0
                    row[f"{key}_hex"] = "#888888"
                    row[f"{key}_median"] = "-"
                    row[f"{key}_med_hex"] = "#888888"
                    row[f"{key}_med_dist"] = 0.0
                    
            if len(entries) >= 2:
                k1, k2 = entries[0]["key"], entries[1]["key"]
                coord1 = modes.get(k1)
                coord2 = modes.get(k2)
                med1 = medians.get(k1)
                med2 = medians.get(k2)
                
                if coord1 and coord2 and coord1 != '-' and coord2 != '-':
                    row["agreement"] = coord1 == coord2
                    row["grid_dist"] = self._calc_grid_distance(coord1, coord2)
                    row["rgb_dist"] = self._calc_rgb_distance(coord1, coord2)
                else:
                    row["agreement"] = False
                    row["grid_dist"] = None
                    row["rgb_dist"] = None
                    
                if med1 and med2 and med1 != '-' and med2 != '-':
                    row["med_agreement"] = med1 == med2
                    row["med_grid_dist"] = self._calc_grid_distance(med1, med2)
                else:
                    row["med_agreement"] = False
                    row["med_grid_dist"] = None
                    
            summary_rows.append(row)
            
        return {
            "entries": entries,
            "total_words": len(summary_rows),
            "rows": summary_rows
        }
