"""Offline tests for `processes.support_routing.classifier`.

We never hit Azure here. The Azure OpenAI client is replaced with a
fake that returns the label and logprob we want to exercise.
"""

from __future__ import annotations

import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from processes.support_routing.classifier import classify_email
from processes.support_routing.labels import LABELS

SAMPLES = Path(__file__).resolve().parents[1] / "sample_data"


def _fake_azure(label: str, probability: float):
    """Build a stand-in for `openai.AzureOpenAI` that returns one fixed reply."""
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=label),
                logprobs=SimpleNamespace(content=[SimpleNamespace(logprob=math.log(probability))]),
            )
        ]
    )
    return SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_kw: response))
    )


@pytest.mark.parametrize("label", [label for label in LABELS if label != "other"])
def test_each_known_label_round_trips(label: str) -> None:
    result = classify_email(
        "anything",
        client=_fake_azure(label, 0.97),  # type: ignore[arg-type]
        threshold=0.85,
    )
    assert result.label == label
    assert result.needs_review is False


def test_other_label_always_flags_review() -> None:
    result = classify_email(
        "??",
        client=_fake_azure("other", 0.99),  # type: ignore[arg-type]
        threshold=0.85,
    )
    assert result.needs_review is True


def test_low_confidence_flags_review() -> None:
    result = classify_email(
        "ambiguous",
        client=_fake_azure("billing", 0.40),  # type: ignore[arg-type]
        threshold=0.85,
    )
    assert result.label == "billing"
    assert result.needs_review is True


def test_threshold_can_be_tightened_per_call() -> None:
    result = classify_email(
        "anything",
        client=_fake_azure("technical", 0.90),  # type: ignore[arg-type]
        threshold=0.95,
    )
    assert result.needs_review is True


def test_sample_data_files_exist_for_every_actionable_label() -> None:
    """Every label except `other` ships with at least one sample email."""
    found = {p.stem for p in SAMPLES.glob("*.txt")}
    expected = set(LABELS) - {"other"}
    missing = expected - found
    assert not missing, f"missing sample emails: {sorted(missing)}"
