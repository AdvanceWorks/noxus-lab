"""Test helpers for repos scaffolded with `noxuslab init --multi-process`.

The single helper here is `make_fake_azure_client(label, probability)`,
which returns a `SimpleNamespace` shaped like `openai.AzureOpenAI` and
always replies with one fixed label + logprob. Every classifier test in
a scaffolded repo uses it through a one-line pytest fixture in the
top-level `conftest.py`:

    from noxuslab.testing import make_fake_azure_client
    import pytest

    @pytest.fixture
    def fake_azure_client():
        return make_fake_azure_client

so no test ever needs to mock `openai` itself or hit the live deployment.
"""

from __future__ import annotations

import math
from types import SimpleNamespace


def make_fake_azure_client(label: str, probability: float) -> SimpleNamespace:
    """Return an object shaped like `openai.AzureOpenAI` that always replies `label`.

    The reply carries one logprob (the natural log of `probability`)
    on the first token, which is what `noxuslab.classify.classify`
    reads to compute confidence.
    """
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=label),
                logprobs=SimpleNamespace(content=[SimpleNamespace(logprob=math.log(probability))]),
            )
        ]
    )
    return SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_kwargs: response))
    )
