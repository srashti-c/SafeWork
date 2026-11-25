"""Extra evaluation of the SAVED model on the same held-out test set:
top-1 / top-2 / top-3 accuracy, and a list of the wrongly predicted texts.
Run from the ml folder:   python evaluate_extra.py"""
import os

import pandas as pd

import predict
from common import RESULTS_DIR, load_data, split_data


def main():
    _, test = split_data(load_data())
    hits = {1: 0, 2: 0, 3: 0}
    wrong = []
    for _, row in test.iterrows():
        out = predict.suggest_categories(row["text"])
        names = [s["category"] for s in out["suggestions"]]
        for k in (1, 2, 3):
            if row["category"] in names[:k]:
                hits[k] += 1
        if names[0] != row["category"]:
            wrong.append({"core_id": row["core_id"], "true_category": row["category"],
                          "predicted_first": names[0], "top3": " | ".join(names),
                          "text": row["text"]})

    n = len(test)
    table = pd.DataFrame([{"top_k": k, "correct": hits[k], "total": n,
                           "accuracy": round(hits[k] / n, 3)} for k in (1, 2, 3)])
    os.makedirs(RESULTS_DIR, exist_ok=True)
    table.to_csv(os.path.join(RESULTS_DIR, "top3_accuracy.csv"), index=False)
    wrong_df = pd.DataFrame(wrong)
    wrong_df.to_csv(os.path.join(RESULTS_DIR, "wrong_predictions.csv"), index=False)

    print("model:", predict._load()[0]["name"])
    print(table.to_string(index=False))
    print("wrong rows:", len(wrong_df), "| base sentences involved:",
          wrong_df["core_id"].nunique() if len(wrong_df) else 0)
    if len(wrong_df):
        print(wrong_df.groupby(["core_id", "true_category", "predicted_first"])
              .size().reset_index(name="rows").to_string(index=False))


if __name__ == "__main__":
    main()