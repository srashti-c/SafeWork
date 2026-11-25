"""SafeWork pattern alerts (Phase 6).

Finds complaints whose TEXT is similar. It is a prompt for a HUMAN reviewer only.
It reads only: id, category, filed time, title and description of each case.
It never reads who filed a case, and it never names, accuses or identifies anyone.
Similar text does not mean the same person or the same incident.

Pure functions: no database, no API. The embedder (text -> numbers) is passed in,
so tests can use fake vectors. If none is given, the MiniLM model is loaded.
"""
import math
from datetime import datetime, timezone

from app.services import pattern_config as cfg

_cache = {}


def default_embedder(texts):
    """Turns a list of texts into a list of vectors with the sentence-transformer.
    The model is loaded once, the first time it is needed (internet needed once)."""
    if "model" not in _cache:
        from sentence_transformers import SentenceTransformer
        _cache["model"] = SentenceTransformer(cfg.EMBED_MODEL_NAME)
    rows = _cache["model"].encode(list(texts), normalize_embeddings=True,
                                  show_progress_bar=False)
    return [[float(x) for x in row] for row in rows]


def _check_threshold(value):
    if value is None:
        value = cfg.SIMILARITY_THRESHOLD
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("threshold must be a number between 0 and 1")
    if not (0 <= value <= 1):
        raise ValueError("threshold must be a number between 0 and 1")
    return float(value)


def _utc(value):
    if not isinstance(value, datetime):
        raise ValueError("created_at must be a datetime")
    if value.tzinfo is None:          # SQLite gives back times without a zone: assume UTC
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _text_of(case):
    parts = []
    for key in ("title", "description"):
        v = case.get(key)
        if isinstance(v, str) and v.strip():
            parts.append(" ".join(v.split()))
    return ". ".join(parts)[: cfg.MAX_TEXT_CHARS]


def _prepare(cases):
    """Keeps ONLY the fields we need. Every other key in the input is ignored."""
    if not isinstance(cases, (list, tuple)):
        raise ValueError("cases must be a list")
    items, seen = [], set()
    for c in cases:
        if not isinstance(c, dict) or "id" not in c:
            raise ValueError("every case must be a dict with an id")
        cid = str(c["id"])
        if cid in seen:
            raise ValueError("duplicate case id: " + cid)
        seen.add(cid)
        category = c.get("category")
        items.append({
            "id": cid,
            "category": category if isinstance(category, str) else "",
            "filed": _utc(c.get("created_at")),
            "text": _text_of(c),
        })
    return items


def _vectors(items, embedder):
    with_text = [i for i in items if i["text"]]
    if not with_text:
        return {}
    embed = embedder or default_embedder
    vectors = embed([i["text"] for i in with_text])
    if len(vectors) != len(with_text):
        raise ValueError("embedder must return one vector per text")
    return {i["id"]: [float(x) for x in v] for i, v in zip(with_text, vectors)}


def _sim(a, b):
    """Cosine similarity, rounded to 4 decimals (the same number is shown and compared)."""
    if len(a) != len(b):
        raise ValueError("vectors must have the same length")
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    return round(max(-1.0, min(1.0, dot / (na * nb))), 4)


def _groups(pairs):
    parent = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for p in pairs:
        for k in (p["case_a"], p["case_b"]):
            parent.setdefault(k, k)
        ra, rb = find(p["case_a"]), find(p["case_b"])
        if ra != rb:
            parent[ra] = rb
    groups = {}
    for k in parent:
        groups.setdefault(find(k), []).append(k)
    out = [sorted(g) for g in groups.values()]
    out.sort(key=lambda g: (-len(g), g))
    return out


def _find(items, case_id):
    for i in items:
        if i["id"] == str(case_id):
            return i
    raise ValueError("case not found: " + str(case_id))


def find_similar_cases(cases, embedder=None, threshold=None):
    """All pairs of cases whose text similarity is at or above the threshold,
    plus groups (cases joined through similar pairs). Always carries the notice."""
    t = _check_threshold(threshold)
    items = _prepare(cases)
    vecs = _vectors(items, embedder)
    pairs = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]
            if a["id"] in vecs and b["id"] in vecs:
                s = _sim(vecs[a["id"]], vecs[b["id"]])
                if s >= t:
                    if a["id"] > b["id"]:
                        a, b = b, a
                    pairs.append({"case_a": a["id"], "case_b": b["id"],
                                  "category_a": a["category"], "category_b": b["category"],
                                  "similarity": s})
    pairs.sort(key=lambda p: (-p["similarity"], p["case_a"], p["case_b"]))
    groups = _groups(pairs)
    if groups:
        message = (str(len(groups)) + " group(s) of cases with similar wording found. "
                   "Please ask a human reviewer to read them.")
    else:
        message = "No cases with similar wording were found at this threshold."
    return {"pairs": pairs, "groups": groups, "threshold": t,
            "cases_checked": len(items), "message": message, "notice": cfg.PATTERN_NOTICE}


def similar_to(case_id, cases, embedder=None, threshold=None):
    """Cases whose text is similar to ONE case (best match first). Always carries the notice."""
    t = _check_threshold(threshold)
    items = _prepare(cases)
    target = _find(items, case_id)
    vecs = _vectors(items, embedder) if target["text"] else {}
    matches = []
    if target["id"] in vecs:
        for o in items:
            if o["id"] != target["id"] and o["id"] in vecs:
                s = _sim(vecs[target["id"]], vecs[o["id"]])
                if s >= t:
                    matches.append({"case_id": o["id"], "category": o["category"],
                                    "filed_on": o["filed"].date().isoformat(),
                                    "similarity": s})
    matches.sort(key=lambda m: (-m["similarity"], m["case_id"]))
    if not target["text"]:
        message = "This case has no text, so no similar cases can be looked for."
    elif matches:
        message = (str(len(matches)) + " case(s) with similar wording found. "
                   "Please ask a human reviewer to read them.")
    else:
        message = "No cases with similar wording were found at this threshold."
    return {"case_id": target["id"], "matches": matches, "threshold": t,
            "message": message, "notice": cfg.PATTERN_NOTICE}


def recurrence_count(case_id, cases, embedder=None, threshold=None):
    """How many OTHER cases, filed strictly EARLIER, have similar text.
    This whole number is the 'recurrence_count' input of the Phase 5 risk score."""
    t = _check_threshold(threshold)
    items = _prepare(cases)
    target = _find(items, case_id)
    if not target["text"]:
        return 0
    vecs = _vectors(items, embedder)
    count = 0
    for o in items:
        if o["id"] != target["id"] and o["id"] in vecs and o["filed"] < target["filed"]:
            if _sim(vecs[target["id"]], vecs[o["id"]]) >= t:
                count += 1
    return count


def filed_at_of(case_id, cases):
    """The time a case was filed (UTC), used by the retaliation check."""
    return _find(_prepare(cases), case_id)["filed"]