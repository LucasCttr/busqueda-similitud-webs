#!/usr/bin/env python3
"""Rebuild FAISS index from the dataset pickle.

This script will:
- Load models/dataset_1_Layers_avg_pool.pkl
- Filter out entries whose files do not exist under backend/sitios/
- (Optionally) write a backup of the original pickle and write a cleaned pickle
- Build a FAISS IndexFlatL2 from the remaining feature vectors
- Write the index to models/faiss_index_f.idx

Usage: run from the repository root (or use full path):
    python3 backend/scripts/rebuild_faiss_index.py
"""
import sys
from pathlib import Path
import pickle
import numpy as np
import faiss


BASE = Path(__file__).resolve().parents[1]  # backend/
MODELS_DIR = BASE / "models"
DATASET_PKL = MODELS_DIR / "dataset_1_Layers_avg_pool.pkl"
INDEX_PATH = MODELS_DIR / "faiss_index_f.idx"
SITIOS_DIR = BASE / "sitios"


def load_dataset(pkl_path: Path):
    if not pkl_path.exists():
        raise FileNotFoundError(f"Dataset pickle not found: {pkl_path}")
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)
    feats = data.get("features")
    paths = data.get("paths")
    if feats is None or paths is None:
        raise ValueError("Pickle does not contain expected keys 'features' and 'paths'.")
    return list(feats), list(paths)


def clean_by_existing_files(feats, paths: list):
    """Return feats_filtered, paths_filtered; only keep entries whose file exists, using the same
    path-normalization logic as `backend/main.py` so we detect the same files.
    """
    valid_feats = []
    valid_paths = []
    for feat, p in zip(feats, paths):
        fname = Path(p).name
        rel_dir = Path("sitios/") if not ("sitios" in fname) else Path("")
        rel = str(rel_dir / fname).replace("\\", "/")
        full_path = BASE / rel
        if full_path.exists():
            valid_feats.append(np.array(feat))
            valid_paths.append(p)
        else:
            print(f"[SKIP] Missing file for entry, skipping: {full_path}")

    if len(valid_feats) == 0:
        raise RuntimeError("No valid entries found: none of the dataset paths point to existing files in 'sitios/'.")

    feats_arr = np.vstack(valid_feats).astype("float32")
    return feats_arr, valid_paths


def build_and_write_index(features: np.ndarray, index_path: Path):
    d = features.shape[1]
    print(f"[INFO] Building IndexFlatL2 with dimension={d}, n_items={features.shape[0]}")
    index = faiss.IndexFlatL2(d)
    index.add(features)
    faiss.write_index(index, str(index_path))
    print(f"[INFO] Wrote FAISS index to {index_path} (ntotal={index.ntotal})")


def main():
    try:
        feats, paths = load_dataset(DATASET_PKL)
        print(f"[INFO] Loaded dataset: features.shape={getattr(feats, 'shape', None)}, paths={len(paths)}")
        feats_clean, paths_clean = clean_by_existing_files(feats, paths)

        with open(DATASET_PKL, "wb") as f:
            pickle.dump({"features": feats_clean, "paths": paths_clean}, f)
        print(f"[INFO] Wrote cleaned dataset pickle with {len(paths_clean)} entries")

        build_and_write_index(feats_clean, INDEX_PATH)

        print("[DONE] FAISS index rebuild complete.")
    except Exception as e:
        print(f"[ERROR] {e}")
        raise


if __name__ == '__main__':
    main()
