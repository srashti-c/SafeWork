import importlib
import inspect
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.services import pattern
from app.services import pattern_config as cfg

T0 = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)

# Fake "text -> numbers" table, so tests need no model and no download.
# x1/x2 are identical (similarity 1.0), near vs x1 = 0.8, far vs x1 = 0.0.
# p-q and q-r are about 0.7071, p-r is 0 (used for the chain test).
TABLE = {
    "x1": [1.0, 0.0], "x2": [1.0, 0.0], "near": [0.8, 0.6], "far": [0.0, 1.0],
    "zero": [0.0, 0.0], "priya-text": [1.0, 0.0],
    "p": [1.0, 0.0], "q": [0.7071, 0.7071], "r": [0.0, 1.0],
}


def make_embedder():
    def emb(texts):
        emb.calls.append(list(texts))
        return [TABLE[t] for t in texts]
    emb.calls = []
    return emb


def case(cid, text, days=0, category="Other", **extra):
    c = {"id": cid, "title": "", "description": text, "category": category,
         "created_at": T0 + timedelta(days=days)}
    c.update(extra)
    return c


def find(cases, threshold=0.9, emb=None):
    return pattern.find_similar_cases(cases, emb or make_embedder(), threshold)


# ---------- rules ----------
def test_identical_text_is_flagged():
    r = find([case("a", "x1"), case("b", "x2")])
    assert len(r["pairs"]) == 1
    assert r["pairs"][0]["similarity"] == 1.0
    assert r["groups"] == [["a", "b"]]


def test_different_text_is_not_flagged():
    r = find([case("a", "x1"), case("b", "far")])
    assert r["pairs"] == [] and r["groups"] == []


def test_threshold_is_inclusive():
    cs = [case("a", "x1"), case("b", "near")]      # similarity is 0.8
    assert len(find(cs, 0.8)["pairs"]) == 1
    assert find(cs, 0.8001)["pairs"] == []


def test_three_similar_cases_make_one_group():
    r = find([case("a", "x1"), case("b", "x2"), case("c", "near")], 0.8)
    assert r["groups"] == [["a", "b", "c"]]


def test_group_joins_a_chain():
    r = find([case("a", "p"), case("b", "q"), case("c", "r")], 0.7)
    assert len(r["pairs"]) == 2
    assert r["groups"] == [["a", "b", "c"]]


def test_default_threshold_comes_from_config(monkeypatch):
    cs = [case("a", "x1"), case("b", "near")]
    monkeypatch.setattr(cfg, "SIMILARITY_THRESHOLD", 0.5)
    assert len(pattern.find_similar_cases(cs, make_embedder())["pairs"]) == 1
    monkeypatch.setattr(cfg, "SIMILARITY_THRESHOLD", 0.95)
    assert pattern.find_similar_cases(cs, make_embedder())["pairs"] == []


def test_category_does_not_matter_only_text():
    r = find([case("a", "x1", category="Verbal harassment"),
              case("b", "x2", category="Sexual harassment")])
    assert len(r["pairs"]) == 1
    assert r["pairs"][0]["category_a"] == "Verbal harassment"


def test_order_of_input_does_not_change_result():
    cs = [case("a", "x1"), case("b", "x2"), case("c", "near"), case("d", "far")]
    assert find(cs, 0.8)["pairs"] == find(list(reversed(cs)), 0.8)["pairs"]


@pytest.mark.parametrize("bad", [-0.1, 1.5, "0.5", True, float("nan"), [0.5]])
def test_bad_threshold_raises(bad):
    with pytest.raises(ValueError):
        pattern.find_similar_cases([], make_embedder(), bad)


def test_threshold_0_and_1_are_allowed():
    pattern.find_similar_cases([], make_embedder(), 0)
    pattern.find_similar_cases([], make_embedder(), 1)


# ---------- edge cases ----------
def test_empty_list_gives_nothing_and_does_not_call_embedder():
    emb = make_embedder()
    r = find([], emb=emb)
    assert r["pairs"] == [] and r["cases_checked"] == 0
    assert emb.calls == []


def test_blank_and_non_text_are_skipped():
    emb = make_embedder()
    cs = [case("a", "   "), case("b", None), case("c", 5), case("d", "x1"), case("e", "x2")]
    r = find(cs, emb=emb)
    assert emb.calls == [["x1", "x2"]]
    assert r["groups"] == [["d", "e"]]


def test_zero_vector_does_not_crash():
    r = find([case("a", "zero"), case("b", "x1")], 0)
    assert r["pairs"][0]["similarity"] == 0.0


def test_title_and_description_are_both_used():
    emb = make_embedder()
    c = case("a", "x1")
    c["title"] = "far"
    TABLE["far. x1"] = [0.0, 1.0]
    try:
        find([c, case("b", "x2")], emb=emb)
    finally:
        del TABLE["far. x1"]
    assert emb.calls[0][0] == "far. x1"


@pytest.mark.parametrize("bad", [
    "not a list",
    [{"description": "x1", "created_at": T0}],
    ["a string"],
    [case("a", "x1"), case("a", "x2")],
    [{"id": "a", "description": "x1"}],
    [{"id": "a", "description": "x1", "created_at": "2026-01-01"}],
])
def test_bad_cases_raise(bad):
    with pytest.raises(ValueError):
        find(bad)


def test_embedder_with_wrong_length_raises():
    with pytest.raises(ValueError):
        pattern.find_similar_cases([case("a", "x1"), case("b", "x2")], lambda t: [[1.0, 0.0]], 0.9)


def test_uuid_ids_are_accepted_and_returned_as_text():
    u1, u2 = uuid.uuid4(), uuid.uuid4()
    r = find([case(u1, "x1"), case(u2, "x2")])
    assert {r["pairs"][0]["case_a"], r["pairs"][0]["case_b"]} == {str(u1), str(u2)}
    json.dumps(r)


# ---------- notices ----------
def test_notice_in_every_output():
    cs = [case("a", "x1"), case("b", "x2")]
    outs = [find([]), find(cs), pattern.similar_to("a", cs, make_embedder(), 0.9)]
    for o in outs:
        n = o["notice"].lower()
        assert o["notice"] == cfg.PATTERN_NOTICE
        assert "human reviewer" in n
        assert "similar" in n
        assert "does not name, accuse or identify anyone" in n
        assert "does not mean" in n


# ---------- privacy ----------
def test_extra_fields_and_text_never_appear_in_output():
    cs = [case("a", "priya-text", pseudonym="Reporter-abc123", user_id=987654,
               email="priya@example.com", identity="Priya Sharma"),
          case("b", "x1", pseudonym="Reporter-zzz999")]
    for out in (find(cs), pattern.similar_to("a", cs, make_embedder(), 0.9)):
        text = json.dumps(out)
        for secret in ["Reporter-abc123", "Reporter-zzz999", "priya@example.com",
                       "Priya Sharma", "priya-text", "987654"]:
            assert secret not in text


def test_output_keys_are_fixed():
    cs = [case("a", "x1"), case("b", "x2")]
    r = find(cs)
    assert set(r) == {"pairs", "groups", "threshold", "cases_checked", "message", "notice"}
    assert set(r["pairs"][0]) == {"case_a", "case_b", "category_a", "category_b", "similarity"}
    s = pattern.similar_to("a", cs, make_embedder(), 0.9)
    assert set(s) == {"case_id", "matches", "threshold", "message", "notice"}
    assert set(s["matches"][0]) == {"case_id", "category", "filed_on", "similarity"}


@pytest.mark.parametrize("name", ["pattern", "retaliation", "risk_inputs"])
def test_code_never_mentions_identity_fields(name):
    """Weak guard: it only checks the source text for identity words."""
    src = inspect.getsource(importlib.import_module("app.services." + name)).lower()
    for word in ["pseudonym", "user_id", "complaint_identit", "uploaded_by"]:
        assert word not in src


# ---------- similar_to ----------
def test_similar_to_lists_best_first_and_not_itself():
    cs = [case("a", "x1"), case("b", "x2", category="Verbal harassment"),
          case("c", "near"), case("d", "far")]
    r = pattern.similar_to("a", cs, make_embedder(), 0.7)
    assert [m["case_id"] for m in r["matches"]] == ["b", "c"]
    assert r["matches"][0]["category"] == "Verbal harassment"
    assert r["matches"][0]["filed_on"] == "2026-01-01"


def test_similar_to_unknown_case_raises():
    with pytest.raises(ValueError):
        pattern.similar_to("nope", [case("a", "x1")], make_embedder(), 0.9)


def test_similar_to_case_without_text():
    emb = make_embedder()
    r = pattern.similar_to("a", [case("a", ""), case("b", "x1")], emb, 0.9)
    assert r["matches"] == [] and emb.calls == []
    assert "no text" in r["message"].lower()


# ---------- recurrence_count ----------
def test_recurrence_counts_only_earlier_similar_cases():
    cs = [case("old1", "x1", days=-10),
          case("old2", "x2", days=-5, category="Verbal harassment"),
          case("oldfar", "far", days=-3),
          case("target", "x1", days=0),
          case("later", "x2", days=4),
          case("same", "x2", days=0)]          # same time: not "earlier"
    n = pattern.recurrence_count("target", cs, make_embedder(), 0.9)
    assert n == 2 and type(n) is int


def test_recurrence_zero_when_alone_or_no_text():
    assert pattern.recurrence_count("a", [case("a", "x1")], make_embedder(), 0.9) == 0
    assert pattern.recurrence_count("a", [case("a", ""), case("b", "x1", days=-1)],
                                    make_embedder(), 0.9) == 0


def test_recurrence_handles_times_without_zone():
    old = case("old", "x1")
    old["created_at"] = datetime(2025, 12, 31, 9, 0)        # no time zone
    assert pattern.recurrence_count("t", [old, case("t", "x2")], make_embedder(), 0.9) == 1


def test_filed_at_of():
    assert pattern.filed_at_of("a", [case("a", "x1", days=2)]) == T0 + timedelta(days=2)