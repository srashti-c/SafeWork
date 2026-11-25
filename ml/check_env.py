import importlib

print("--- package check ---")
for name in ["numpy", "pandas", "scipy", "sklearn", "matplotlib",
             "joblib", "torch", "transformers", "sentence_transformers"]:
    try:
        m = importlib.import_module(name)
        print(f"{name:22} OK  {getattr(m, '__version__', '?')}")
    except Exception as e:
        print(f"{name:22} FAILED  {e}")

print("--- model check (first run downloads about 90 MB) ---")
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    vec = model.encode(["He keeps insulting me in meetings."])
    print("model OK, embedding shape:", vec.shape)
except Exception as e:
    print("model FAILED:", e)