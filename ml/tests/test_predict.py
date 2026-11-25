import os

import pytest

import predict
from common import LABELS

TEXT = "He keeps sending me romantic messages late at night although I told him I am not interested."


@pytest.fixture(scope="module")
def normal():
    assert os.path.exists(predict.MODEL_FILE), "Run train_evaluate.py first"
    return predict.suggest_categories(TEXT)


def test_returns_exactly_three_categories(normal):
    assert len(normal["suggestions"]) == 3


def test_categories_are_real_and_different(normal):
    names = [s["category"] for s in normal["suggestions"]]
    assert len(set(names)) == 3
    assert all(n in LABELS for n in names)


def test_scores_between_0_and_1_and_sorted(normal):
    scores = [s["score"] for s in normal["suggestions"]]
    assert all(0.0 <= s <= 1.0 for s in scores)
    assert scores == sorted(scores, reverse=True)
    assert [s["rank"] for s in normal["suggestions"]] == [1, 2, 3]


def test_top3_scores_do_not_add_up_to_more_than_1(normal):
    assert sum(s["score"] for s in normal["suggestions"]) <= 1.001


def test_notice_says_suggestion_only(normal):
    notice = normal["notice"]
    assert "SUGGESTION ONLY" in notice
    assert "human" in notice.lower()
    assert "not decide" in notice.lower()
    assert "guilty" in notice.lower()


@pytest.mark.parametrize("bad", ["", "   ", "\n\t", None, 123])
def test_empty_or_bad_input_is_handled(bad):
    out = predict.suggest_categories(bad)
    assert out["suggestions"] == []
    assert out["message"] != ""
    assert "SUGGESTION ONLY" in out["notice"]


def test_very_long_text_does_not_crash():
    out = predict.suggest_categories("word " * 5000)
    assert len(out["suggestions"]) == 3
    assert "SUGGESTION ONLY" in out["notice"]


def test_clear_example_has_sexual_harassment_in_top3(normal):
    # sanity check on model quality, not a promise for every text
    names = [s["category"] for s in normal["suggestions"]]
    assert "Sexual harassment" in names