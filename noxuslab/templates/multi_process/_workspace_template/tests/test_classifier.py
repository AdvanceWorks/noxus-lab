"""Offline tests for `__workspace__.classifier`.

Uses the `fake_azure_client` fixture from the top-level `conftest.py`
(itself backed by `noxuslab.testing.make_fake_azure_client`) so we
never hit the live Azure OpenAI deployment in CI. The live path is
exercised separately, behind the `live` pytest marker.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from __workspace__.classifier import classify_text
from __workspace__.labels import LABELS, REVIEW_LABELS

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "test_fixtures"


@pytest.mark.parametrize("label", [label for label in LABELS if label not in REVIEW_LABELS])
def test_each_actionable_label_round_trips(label: str, fake_azure_client) -> None:
    result = classify_text(
        "anything",
        client=fake_azure_client(label, 0.97),
        threshold=0.85,
    )
    assert result.label == label
    assert result.needs_review is False


@pytest.mark.parametrize("review_label", REVIEW_LABELS)
def test_review_labels_always_flag_review_even_at_high_confidence(
    review_label: str, fake_azure_client
) -> None:
    result = classify_text(
        "??",
        client=fake_azure_client(review_label, 0.99),
        threshold=0.85,
    )
    assert result.label == review_label
    assert result.needs_review is True


def test_low_confidence_flags_review_even_for_actionable_label(fake_azure_client) -> None:
    actionable = next(label for label in LABELS if label not in REVIEW_LABELS)
    result = classify_text(
        "ambiguous",
        client=fake_azure_client(actionable, 0.40),
        threshold=0.85,
    )
    assert result.label == actionable
    assert result.needs_review is True


def test_threshold_is_per_call_tunable(fake_azure_client) -> None:
    actionable = next(label for label in LABELS if label not in REVIEW_LABELS)
    loose = classify_text("anything", client=fake_azure_client(actionable, 0.90), threshold=0.85)
    strict = classify_text("anything", client=fake_azure_client(actionable, 0.90), threshold=0.95)
    assert loose.needs_review is False
    assert strict.needs_review is True


def test_test_fixtures_cover_every_actionable_label() -> None:
    """Every actionable label has at least one fixture file on disk."""
    found = {p.stem for p in FIXTURES_DIR.glob("*.txt")}
    expected = set(LABELS) - set(REVIEW_LABELS)
    missing = expected - found
    assert not missing, f"missing fixtures: {sorted(missing)}"
