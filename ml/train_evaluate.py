"""Trains 3 models, evaluates them on the held-out test set, saves tables, images
and the best model.   Run from the ml folder:   python train_evaluate.py"""
import os
import re

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, precision_recall_fscore_support)
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from common import (EMBED_MODEL, LABELS, MODELS_DIR, RESULTS_DIR, SEED,
                    load_data, split_data)


def make_tfidf():
    return TfidfVectorizer(lowercase=True, ngram_range=(1, 2), sublinear_tf=True)


MODELS = [
    ("TF-IDF + Logistic Regression", "tfidf",
     Pipeline([("tfidf", make_tfidf()), ("clf", LogisticRegression(C=10, max_iter=1000))])),
    ("TF-IDF + Linear SVM", "tfidf",
     Pipeline([("tfidf", make_tfidf()), ("clf", LinearSVC(C=1.0, random_state=SEED))])),
    ("MiniLM embeddings + Logistic Regression", "embed",
     LogisticRegression(C=10, max_iter=1000)),
]


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def save_confusion_image(cm, title, path):
    n = len(LABELS)
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(n))
    ax.set_xticklabels(LABELS, rotation=45, ha="right")
    ax.set_yticks(range(n))
    ax.set_yticklabels(LABELS)
    ax.set_xlabel("Predicted category")
    ax.set_ylabel("True category")
    ax.set_title(title + "\n(synthetic test set)")
    limit = cm.max() / 2
    for i in range(n):
        for j in range(n):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > limit else "black")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)

    train, test = split_data(load_data())
    print("train rows:", len(train), "| test rows:", len(test))
    print("test rows per class:", test["category"].value_counts().to_dict())
    assert not set(train["core_id"]) & set(test["core_id"]), "leakage!"

    y_train, y_test = train["category"].tolist(), test["category"].tolist()
    groups = train["core_id"].tolist()

    print("making embeddings (first time may take a minute)...")
    embedder = SentenceTransformer(EMBED_MODEL)
    emb_train = embedder.encode(train["text"].tolist(), batch_size=32,
                                normalize_embeddings=True, show_progress_bar=False)
    emb_test = embedder.encode(test["text"].tolist(), batch_size=32,
                               normalize_embeddings=True, show_progress_bar=False)

    cv = GroupKFold(n_splits=4)
    results, per_class_rows, fitted = [], [], {}

    for name, kind, model in MODELS:
        if kind == "embed":
            x_train, x_test = emb_train, emb_test
        else:
            x_train, x_test = train["text"].tolist(), test["text"].tolist()

        # model choice uses ONLY the training data (grouped cross-validation)
        cv_f1 = cross_val_score(model, x_train, y_train, groups=groups,
                                cv=cv, scoring="f1_macro").mean()
        model.fit(x_train, y_train)
        pred = model.predict(x_test)

        acc = accuracy_score(y_test, pred)
        p, r, f, _ = precision_recall_fscore_support(
            y_test, pred, average="macro", zero_division=0)
        report = classification_report(y_test, pred, labels=LABELS,
                                       output_dict=True, zero_division=0)
        for label in LABELS:
            per_class_rows.append({
                "model": name, "class": label,
                "precision": report[label]["precision"],
                "recall": report[label]["recall"],
                "f1": report[label]["f1-score"],
                "support": int(report[label]["support"])})

        cm = confusion_matrix(y_test, pred, labels=LABELS)
        pd.DataFrame(cm, index=LABELS, columns=LABELS).to_csv(
            os.path.join(RESULTS_DIR, "confusion_matrix_" + slug(name) + ".csv"))
        save_confusion_image(cm, name, os.path.join(
            RESULTS_DIR, "confusion_matrix_" + slug(name) + ".png"))

        results.append({"model": name, "kind": kind, "cv_macro_f1_train": cv_f1,
                        "test_accuracy": acc, "test_macro_precision": p,
                        "test_macro_recall": r, "test_macro_f1": f})
        fitted[name] = model

    # ---- comparison table (one table, all models) ----
    comp = pd.DataFrame(results).drop(columns=["kind"]).round(3)
    comp.to_csv(os.path.join(RESULTS_DIR, "comparison.csv"), index=False)
    lines = ["| " + " | ".join(comp.columns) + " |",
             "|" + "---|" * len(comp.columns)]
    for _, row in comp.iterrows():
        lines.append("| " + " | ".join(str(v) for v in row.values) + " |")
    with open(os.path.join(RESULTS_DIR, "comparison.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    pd.DataFrame(per_class_rows).round(3).to_csv(
        os.path.join(RESULTS_DIR, "per_class_metrics.csv"), index=False)

    # ---- choose the best model (training data only) ----
    best_cv = max(r["cv_macro_f1_train"] for r in results)
    close = [r for r in results if best_cv - r["cv_macro_f1_train"] <= 0.01]
    embed_close = [r for r in close if r["kind"] == "embed"]
    chosen = embed_close[0] if embed_close else max(
        close, key=lambda r: r["cv_macro_f1_train"])
    # rule: highest CV macro-F1; if within 0.01, prefer the sentence-transformer
    # (it understands new wording better than word counts)

    bundle = {"name": chosen["model"], "kind": chosen["kind"],
              "model": fitted[chosen["model"]], "labels": LABELS,
              "embed_model": EMBED_MODEL if chosen["kind"] == "embed" else None,
              "seed": SEED, "trained_on_rows": len(train)}
    joblib.dump(bundle, os.path.join(MODELS_DIR, "best_model.joblib"))

    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 20)
    print()
    print(comp.to_string(index=False))
    print()
    print("BEST MODEL SAVED:", chosen["model"])
    print("results folder:", RESULTS_DIR)


if __name__ == "__main__":
    main()