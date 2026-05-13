"""Test helpers for repos scaffolded with `noxuslab init --multi-process`.

Two helpers live here, both shared by every repo scaffolded from the
multi-process template:

- ``make_fake_azure_client(label, probability)`` — a ``SimpleNamespace``
  shaped like ``openai.AzureOpenAI`` that always replies with one
  fixed (label, logprob) pair. Used by classifier tests so they never
  hit the live deployment.

- ``exec_code_node(template, inputs)`` — exec a ``CodeExecutionV3Node``
  template string (the same string the Noxus platform runs) into an
  isolated namespace and call its ``main(inputs)`` function. Used by
  every test that exercises an in-platform Python code node without
  pushing a workflow.

Both helpers are picked up by tests via a one-line pytest fixture in
the top-level ``conftest.py``::

    from noxuslab.testing import make_fake_azure_client
    import pytest

    @pytest.fixture
    def fake_azure_client():
        return make_fake_azure_client

so no test ever needs to mock ``openai`` itself or hit the live
deployment, and no test ever needs to re-implement the exec dance for
code nodes.
"""

from __future__ import annotations

import math
from types import SimpleNamespace
from typing import Any


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


def exec_code_node(template: str, inputs: dict[str, Any]) -> dict[str, Any]:
    """Execute a ``CodeExecutionV3Node`` template string offline.

    The platform's contract for a code node is: the template defines a
    top-level ``main(inputs: dict) -> dict`` function; the platform
    calls ``main(inputs)`` with the wired input variables and writes the
    returned dict to the node's output variables. This helper does
    exactly that, in-process, with no network or SDK involvement:

    >>> CODE = "def main(inputs):\\n    return {'hi': inputs['name']}"
    >>> exec_code_node(CODE, {"name": "world"})
    {'hi': 'world'}

    Use it in unit tests so the same string that the platform runs is
    what the test exercises. If you change the code-node template, the
    test fails before the next push hits the platform.

    The exec namespace is fresh per call, so two calls cannot leak
    state through module-level mutables. Imports inside the template
    are real imports against the test environment's interpreter —
    install any third-party packages the node uses (``openai``,
    ``httpx``, etc.) as dev dependencies.

    Raises:
        KeyError: if the template does not define ``main``.
    """
    ns: dict[str, Any] = {}
    exec(template, ns)  # noqa: S102 — exec is the entire point
    try:
        main = ns["main"]
    except KeyError as exc:
        raise KeyError("code-node template defines no top-level `main(inputs)` function") from exc
    return main(inputs)
