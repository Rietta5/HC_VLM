import os
import glob
import math
import numpy as np
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

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

class DataLoader:
    def __init__(self, data_dir=None, rgb_path="HC_RGB.csv"):
        self.data_dir = data_dir if data_dir and os.path.isabs(data_dir) else BASE_DIR
        self.rgb_path = resolve_path(rgb_path)
        
        self.board_cells = []
        self.board_map = {}
        self.row_letters = []
        self.inv_row_map = {}
        self.col_numbers = list(range(1, 31))
        
        self.models_data = {}  # {model_name: pd.DataFrame}
        
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
        """Discovers and loads all results_HC_*.csv in data_dir (all words preserved)."""
        pattern = os.path.join(self.data_dir, "results_HC_*.csv")
        csv_files = glob.glob(pattern)
        
        for file_path in sorted(csv_files):
            filename = os.path.basename(file_path)
            model_name = filename
            if filename.startswith("results_HC_") and filename.endswith(".csv"):
                model_name = filename[len("results_HC_"):-len(".csv")]
                
            try:
                df = pd.read_csv(file_path)
                if 'Palabra' in df.columns:
                    # Normalize word: strip whitespace unless it's only spaces (then keep single space)
                    df['Palabra'] = df['Palabra'].fillna(' ').astype(str).apply(lambda x: x.strip().upper() if x.strip() else ' ')
                self.models_data[model_name] = df
                print(f"[DataLoader] Loaded model '{model_name}' ({len(df)} words) from {filename}")
            except Exception as e:
                print(f"[DataLoader] Error loading {filename}: {e}")

    def get_models(self):
        """Returns list of available model names."""
        return list(self.models_data.keys())

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
        """Returns list of unique words with summary stats across models."""
        if not self.models_data:
            return []
            
        all_words = set()
        for df in self.models_data.values():
            if 'Palabra' in df.columns:
                all_words.update(df['Palabra'].dropna().tolist())
                
        # Sort words alphabetically, putting space/blank at beginning or end
        sorted_words = sorted(list(all_words), key=lambda x: (x == ' ', x))
        words_summary = []
        
        for word in sorted_words:
            model_summaries = {}
            for model_name, df in self.models_data.items():
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
                        
                        model_summaries[model_name] = {
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

    def get_word_analysis(self, word_name, model_name=None):
        """Returns full response analysis for a single word and model(s)."""
        if word_name is None:
            return None
        word_norm = word_name.strip().upper() if word_name.strip() else ' '
        
        models_to_process = [model_name] if model_name and model_name in self.models_data else list(self.models_data.keys())
        
        results = {}
        for m_name in models_to_process:
            df = self.models_data.get(m_name)
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
            
            results[m_name] = {
                "model_name": m_name,
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
            
        if model_name and model_name in results:
            single = results[model_name]
            single["word"] = word_norm
            return single
            
        comparison = {}
        models_list = list(results.keys())
        if len(models_list) >= 2:
            m1, m2 = models_list[0], models_list[1]
            c1 = results[m1]["counts_per_coord"]
            c2 = results[m2]["counts_per_coord"]
            t1 = results[m1]["total_samples"]
            t2 = results[m2]["total_samples"]
            
            all_coords = set(c1.keys()).union(set(c2.keys()))
            overlap_pct = sum(min(c1.get(k, 0)/t1, c2.get(k, 0)/t2) for k in all_coords) * 100
            
            mode1 = results[m1]["mode_coord"]
            mode2 = results[m2]["mode_coord"]
            med1 = results[m1]["median_coord"]
            med2 = results[m2]["median_coord"]
            
            grid_dist = self._calc_grid_distance(mode1, mode2) if mode1 and mode2 else None
            rgb_dist = self._calc_rgb_distance(mode1, mode2) if mode1 and mode2 else None
            
            med_grid_dist = self._calc_grid_distance(med1, med2) if med1 and med2 else None
            med_rgb_dist = self._calc_rgb_distance(med1, med2) if med1 and med2 else None
            
            comparison = {
                "model_a": m1,
                "model_b": m2,
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

    def get_benchmark_summary(self):
        """Returns full comparative benchmark data across all words."""
        words_list = self.get_words_list()
        models = self.get_models()
        
        summary_rows = []
        for item in words_list:
            word = item['word']
            row = {"word": word}
            
            modes = {}
            medians = {}
            for m in models:
                if m in item['models']:
                    m_stat = item['models'][m]
                    row[f"{m}_mode"] = m_stat['mode_coord']
                    row[f"{m}_pct"] = m_stat['mode_percentage']
                    row[f"{m}_hex"] = m_stat['mode_hex']
                    row[f"{m}_median"] = m_stat['median_coord']
                    row[f"{m}_med_hex"] = m_stat['median_hex']
                    row[f"{m}_med_dist"] = m_stat['median_avg_dist']
                    modes[m] = m_stat['mode_coord']
                    medians[m] = m_stat['median_coord']
                else:
                    row[f"{m}_mode"] = "-"
                    row[f"{m}_pct"] = 0
                    row[f"{m}_hex"] = "#888888"
                    row[f"{m}_median"] = "-"
                    row[f"{m}_med_hex"] = "#888888"
                    row[f"{m}_med_dist"] = 0.0
                    
            if len(models) >= 2:
                m1, m2 = models[0], models[1]
                coord1 = modes.get(m1)
                coord2 = modes.get(m2)
                med1 = medians.get(m1)
                med2 = medians.get(m2)
                
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
            "models": models,
            "total_words": len(summary_rows),
            "rows": summary_rows
        }
