"""Offline tests for `noxuslab.classify` and `noxuslab.testing`."""

from __future__ import annotations

import math

import pytest

from noxuslab.classify import (
    ClassificationResult,
    TokenScore,
    _match_label,
    _required,
    decide,
)
from noxuslab.testing import exec_code_node, make_fake_azure_client


def _score(label: str, prob: float) -> TokenScore:
    return TokenScore(token=label, logprob=math.log(prob))


def test_token_score_probability_round_trips() -> None:
    s = TokenScore(token="vacation", logprob=math.log(0.9))
    assert pytest.approx(s.probability, rel=1e-6) == 0.9


def test_decide_high_confidence_label_is_accepted() -> None:
    result = decide(_score("billing", 0.97), threshold=0.85)
    assert isinstance(result, ClassificationResult)
    assert result.label == "billing"
    assert result.needs_review is False


def test_decide_low_confidence_label_is_flagged_for_review() -> None:
    result = decide(_score("sales", 0.62), threshold=0.85)
    assert result.needs_review is True


def test_decide_review_labels_always_trigger_review_even_if_confident() -> None:
    result = decide(_score("other", 0.99), threshold=0.85)
    assert result.needs_review is True
    custom = decide(_score("escalate", 0.99), threshold=0.85, review_labels=("escalate",))
    assert custom.needs_review is True


def test_decide_threshold_boundary_is_inclusive_above() -> None:
    result = decide(_score("general", 0.85), threshold=0.85)
    assert result.needs_review is False


def test_decide_serialisation_round_trip() -> None:
    payload = decide(_score("technical", 0.91), threshold=0.85).to_dict()
    assert payload["label"] == "technical"
    assert payload["needs_review"] is False
    assert payload["threshold"] == 0.85


def test_match_label_exact_case_insensitive() -> None:
    assert _match_label("Billing", ["billing", "sales"]) == "billing"


def test_match_label_strips_punctuation_and_starts_with() -> None:
    assert _match_label('"billing".', ["billing"]) == "billing"
    assert _match_label("billing because", ["billing"]) == "billing"


def test_match_label_falls_back_to_raw_when_unknown() -> None:
    assert _match_label("zzz", ["billing"]) == "zzz"


def test_required_raises_with_helpful_message(monkeypatch) -> None:
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="AZURE_OPENAI_API_KEY"):
        _required("AZURE_OPENAI_API_KEY")


def test_make_fake_azure_client_returns_label_and_logprob() -> None:
    client = make_fake_azure_client("vacation", 0.9)
    response = client.chat.completions.create()
    assert response.choices[0].message.content == "vacation"
    logprob = response.choices[0].logprobs.content[0].logprob
    assert pytest.approx(math.exp(logprob), rel=1e-6) == 0.9


# ---------------------------------------------------------------------------
# exec_code_node — offline runner for CodeExecutionV3Node templates
# ---------------------------------------------------------------------------


def test_exec_code_node_runs_main_with_inputs() -> None:
    code = "def main(inputs):\n    return {'echo': inputs['x'] + '!'}\n"
    assert exec_code_node(code, {"x": "hi"}) == {"echo": "hi!"}


def test_exec_code_node_supports_imports_and_stdlib() -> None:
    code = (
        "import json\n"
        "def main(inputs):\n"
        "    payload = json.loads(inputs['raw'])\n"
        "    return {'len': str(len(payload))}\n"
    )
    assert exec_code_node(code, {"raw": "[1, 2, 3]"}) == {"len": "3"}


def test_exec_code_node_isolates_namespaces_between_calls() -> None:
    code = (
        "_state = []\n"
        "def main(inputs):\n"
        "    _state.append(inputs['v'])\n"
        "    return {'count': str(len(_state))}\n"
    )
    # Two separate calls => two fresh namespaces => no state leak.
    assert exec_code_node(code, {"v": 1}) == {"count": "1"}
    assert exec_code_node(code, {"v": 2}) == {"count": "1"}


def test_exec_code_node_missing_main_raises_keyerror() -> None:
    with pytest.raises(KeyError, match="main"):
        exec_code_node("x = 1\n", {})
