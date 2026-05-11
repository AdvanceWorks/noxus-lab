"""Offline tests for `shared/classification.py`."""

import math

import pytest

from shared.azure_openai import TokenScore
from shared.classification import decide


def _score(label: str, prob: float) -> TokenScore:
    return TokenScore(token=label, logprob=math.log(prob))


def test_high_confidence_label_is_accepted() -> None:
    result = decide(_score("billing", 0.97), threshold=0.85)
    assert result.label == "billing"
    assert result.needs_review is False
    assert pytest.approx(result.confidence, rel=1e-3) == 0.97


def test_low_confidence_label_is_flagged_for_review() -> None:
    result = decide(_score("sales", 0.62), threshold=0.85)
    assert result.label == "sales"
    assert result.needs_review is True


def test_unknown_label_always_triggers_review_even_if_confident() -> None:
    result = decide(_score("unknown", 0.99), threshold=0.85)
    assert result.needs_review is True


def test_other_label_always_triggers_review() -> None:
    result = decide(_score("other", 0.99), threshold=0.85)
    assert result.needs_review is True


def test_threshold_boundary_is_inclusive_above() -> None:
    result = decide(_score("general", 0.85), threshold=0.85)
    assert result.needs_review is False


def test_serialisation_round_trip() -> None:
    result = decide(_score("technical", 0.91), threshold=0.85)
    payload = result.to_dict()
    assert payload == {
        "label": "technical",
        "confidence": pytest.approx(0.91, rel=1e-3),
        "needs_review": False,
        "threshold": 0.85,
    }
