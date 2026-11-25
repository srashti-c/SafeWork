"""The ONLY place where the backend reaches the ml folder (Phase 4 model).

It loads ml\predict.py by file path. Nothing is copied. If we move to Docker
later, only this file changes.
"""
import importlib.util
from pathlib import Path

# app\services\ml_bridge.py -> parents[3] is the project root (folder with backend and ml)
PREDICT_FILE = Path(__file__).resolve().parents[3] / "ml" / "predict.py"
_module = None


class MlUnavailable(Exception):
    """The model code or the saved model could not be loaded."""


def _load_predict():
    global _module
    if _module is None:
        if not PREDICT_FILE.exists():
            raise MlUnavailable("ml\\predict.py not found")
        spec = importlib.util.spec_from_file_location("safework_ml_predict", PREDICT_FILE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _module = mod
    return _module


def suggest(text):
    """Return the dict from ml\\predict.suggest_categories (suggestions, notice, message, model)."""
    try:
        return _load_predict().suggest_categories(text)
    except MlUnavailable:
        raise
    except Exception as exc:  # missing model file, missing package, etc.
        raise MlUnavailable(type(exc).__name__) from exc