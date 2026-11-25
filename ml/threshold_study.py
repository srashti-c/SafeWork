"""Phase 6 threshold study: what does each similarity threshold actually give?

DATA IS SYNTHETIC (420 made-up complaints, 84 base sentences, each used 5 times).
Ground truth used here: two rows are a "true similar pair" if they come from the SAME
base sentence (same core_id). This is a weak stand-in for real similarity, because
rows with different base sentences can also be similar in meaning. So "false alarms"
below may be partly real similarity, and precision is probably UNDER-estimated.
Real complaints will behave differently.

Rule agreed BEFORE the run: choose the LOWEST threshold (steps of 0.01, from 0.30)
whose precision is at least 0.90. Nothing is promised in advance; the numbers are
whatever this script prints.

Run from the ml folder:  python threshold_study.py
"""
import os

import numpy as np
import pandas as pd

from common import EMBED_MODEL, RESULTS_DIR, load_data

PRECISION_RULE = 0.90
SHOW = [0.30, 0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]


def study(sims_upper, same_core, same_cat, thresholds):
    total_true = int(same_core.sum())
    rows = []
    for t in thresholds:
        flagged = sims_upper >= t
        n = int(flagged.sum())
        tp = int((flagged & same_core).sum())
        fp = n - tp
        fp_same_cat = int((flagged & ~same_core & same_cat).sum())
        prec = tp / n if n else float("nan")
        rec = tp / total_true if total_true else float("nan")
        f1 = 2 * prec * rec / (prec + rec) if n and (prec + rec) > 0 else 0.0
        rows.append({"threshold": round(float(t), 2), "flagged_pairs": n, "true_pairs": tp,
                     "false_alarms": fp, "false_same_category": fp_same_cat,
                     "precision": round(prec, 3), "recall": round(rec, 3), "f1": round(f1, 3)})
    return pd.DataFrame(rows), total_true


def main():
    df = load_data()
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBED_MODEL)
    emb = model.encode(df["text"].tolist(), normalize_embeddings=True, show_progress_bar=False)
    sims = np.asarray(emb) @ np.asarray(emb).T
    iu = np.triu_indices(len(df), k=1)
    s = np.round(sims[iu], 4)
    core = df["core_id"].to_numpy()
    cat = df["category"].to_numpy()
    same_core = core[iu[0]] == core[iu[1]]
    same_cat = cat[iu[0]] == cat[iu[1]]

    full, total_true = study(s, same_core, same_cat, np.round(np.arange(0.30, 1.0, 0.01), 2))
    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_file = os.path.join(RESULTS_DIR, "pattern_threshold.csv")
    full.to_csv(out_file, index=False)

    shown = full[full["threshold"].isin(SHOW)]
    print("SYNTHETIC data. Rows:", len(df), "| all pairs:", len(s),
          "| true pairs (same base sentence):", total_true)
    print("Mean similarity: same base sentence = %.3f, different base sentence = %.3f"
          % (s[same_core].mean(), s[~same_core].mean()))
    print(shown.to_string(index=False))
    ok = full[(full["flagged_pairs"] > 0) & (full["precision"] >= PRECISION_RULE)]
    if len(ok):
        r = ok.iloc[0]
        print("RULE (lowest threshold with precision >= %.2f): threshold = %.2f "
              "(precision %.3f, recall %.3f, flagged pairs %d)"
              % (PRECISION_RULE, r["threshold"], r["precision"], r["recall"], r["flagged_pairs"]))
    else:
        print("RULE: no threshold from 0.30 to 0.99 reached precision %.2f." % PRECISION_RULE)
    print("Full table saved to:", out_file)


if __name__ == "__main__":
    main()