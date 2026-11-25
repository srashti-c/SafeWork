"""SafeWork complaint-category SUGGESTION (Phase 4).

suggest_categories(text) returns the top 3 suggested categories with scores.
It is a suggestion for a HUMAN reviewer only. It never decides truth or guilt.

Try it:   python predict.py "your complaint text here"
"""
import math
import os

import joblib

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(BASE, "models", "best_model.joblib")

MAX_CHARS = 5000   # longer text is cut (keeps the function fast and safe)
TOP_K = 3

NOTICE = (
    "SUGGESTION ONLY, for a human reviewer. These categories are an automatic guess "
    "from a model trained on synthetic (made-up) data. The scores are model scores, "
    "not certainty. This does NOT decide what happened, who is at fault, or whether "
    "anyone is guilty. Only the human reviewers and the Internal Committee decide."
)

_cache = {}


def _load():
    """Loads the saved model once and keeps it in memory.
    Only load model files made by our own train_evaluate.py (joblib files can run code)."""
    if "bundle" not in _cache:
        if not os.path.exists(MODEL_FILE):
            raise FileNotFoundError(
                "Model file not found: " + MODEL_FILE + "  (run train_evaluate.py first)")
        bundle = joblib.load(MODEL_FILE)
        embedder = None
        if bundle["kind"] == "embed":
            from sentence_transformers import SentenceTransformer
            embedder = SentenceTransformer(bundle["embed_model"])
        _cache["bundle"] = bundle
        _cache["embedder"] = embedder
    return _cache["bundle"], _cache["embedder"]


def _softmax(values):
    top = max(values)
    exps = [math.exp(v - top) for v in values]
    total = sum(exps)
    return [e / total for e in exps]


def _scores_for(text):
    bundle, embedder = _load()
    model = bundle["model"]
    if embedder is not None:
        x = embedder.encode([text], normalize_embeddings=True, show_progress_bar=False)
    else:
        x = [text]
    if hasattr(model, "predict_proba"):
        scores = list(model.predict_proba(x)[0])
    else:  # linear SVM has no probabilities: turn its scores into 0..1 with softmax
        scores = _softmax(list(model.decision_function(x)[0]))
    return [str(c) for c in model.classes_], [float(s) for s in scores]


def suggest_categories(text, top_k=TOP_K):
    """Returns a dict:
       suggestions: list of {rank, category, score} (score between 0 and 1)
       notice:      the 'suggestion only' text (always present)
       message:     short note (for example when no text was given)
       model:       name of the model used
    Empty, blank or non-text input gives NO suggestions (never a made-up guess)."""
    result = {"suggestions": [], "notice": NOTICE, "message": "", "model": None}
    if not isinstance(text, str) or not text.strip():
        result["message"] = "No text was given, so no category is suggested."
        return result

    clean = " ".join(text.split())[:MAX_CHARS]
    classes, scores = _scores_for(clean)
    top_k = max(1, min(int(top_k), len(classes)))
    ranked = sorted(zip(classes, scores), key=lambda p: p[1], reverse=True)[:top_k]
    result["suggestions"] = [
        {"rank": i, "category": c, "score": round(min(max(s, 0.0), 1.0), 4)}
        for i, (c, s) in enumerate(ranked, start=1)
    ]
    result["model"] = _load()[0]["name"]
    return result


if __name__ == "__main__":
    import sys
    sample = " ".join(sys.argv[1:]) or \
        "My manager keeps sending me suggestive messages late at night."
    out = suggest_categories(sample)
    print(out["notice"])
    print()
    for s in out["suggestions"]:
        print(f'{s["rank"]}. {s["category"]}   score={s["score"]}')
    print("model:", out["model"])