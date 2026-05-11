"""Thin wrapper around the Azure OpenAI Python client.

Why this exists:

- One place to read Azure credentials from the environment.
- One place to build a chat-completion request that returns both the
  text answer and the per-token logprobs we use for confidence scoring.
- One place that knows how to fail loudly when the deployment is
  misconfigured (wrong region, wrong API version, missing role).

Stays tiny on purpose. Specialised prompting lives in each process.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Any

from openai import AzureOpenAI


@dataclass(frozen=True)
class TokenScore:
    """A single classification choice with the model's probability for it.

    `logprob` is the natural-log probability the model assigned to the
    chosen token (or first token of the chosen label, for multi-token
    labels). `probability` exposes it as a [0, 1] number for thresholds.
    """

    token: str
    logprob: float

    @property
    def probability(self) -> float:
        return math.exp(self.logprob)


def build_client() -> AzureOpenAI:
    """Construct an `AzureOpenAI` client from environment variables.

    Required env vars:

    - `AZURE_OPENAI_API_KEY`
    - `AZURE_OPENAI_ENDPOINT`
    - `AZURE_OPENAI_API_VERSION` (default: `2024-08-01-preview`)
    """
    return AzureOpenAI(
        api_key=_required("AZURE_OPENAI_API_KEY"),
        azure_endpoint=_required("AZURE_OPENAI_ENDPOINT"),
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
    )


def classify(
    client: AzureOpenAI,
    *,
    deployment: str,
    system_prompt: str,
    user_content: str | list[dict[str, Any]],
    allowed_labels: list[str],
) -> TokenScore:
    """Ask the model to pick exactly one label; return it with its logprob.

    `user_content` is either a plain string (text-only message body) or a
    list of OpenAI content parts (text + images for multimodal classification).

    The model is instructed to reply with a single label from
    `allowed_labels`. The first token of the response is what we score,
    so labels should be chosen so each starts with a unique token.
    """
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},  # type: ignore[arg-type]
        ],
        temperature=0,
        max_tokens=8,
        logprobs=True,
        top_logprobs=5,
    )
    choice = response.choices[0]
    text = (choice.message.content or "").strip()
    label = _match_label(text, allowed_labels)

    logprob = 0.0
    if choice.logprobs and choice.logprobs.content:
        logprob = choice.logprobs.content[0].logprob
    return TokenScore(token=label, logprob=logprob)


def _match_label(reply: str, allowed: list[str]) -> str:
    """Map the model's free-form reply to one of the allowed labels.

    Falls back to the literal reply if no match is found, which the
    caller's threshold logic will then catch as an unknown label.
    """
    lower = reply.lower().strip().strip(".,;:'\"")
    for label in allowed:
        if lower == label.lower() or lower.startswith(label.lower()):
            return label
    return reply.strip() or "unknown"


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"{name} is not set. Copy .env.example to .env and fill in your "
            f"Azure OpenAI credentials, or export {name} in your shell."
        )
    return value
