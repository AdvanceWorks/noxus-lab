"""LLM-classifier primitives shared by every `noxuslab init` repo.

A classification process is the same shape everywhere: pick exactly one
label from a fixed set, score the model's confidence with the
first-token logprob, and route low-confidence picks to human review.
This module owns that shape so individual processes only carry their
labels and prompt — no infrastructure code.

Public surface:

- `TokenScore`           — one label + its log-probability
- `ClassificationResult` — final per-item record (label, confidence, needs_review)
- `build_client()`       — `openai.AzureOpenAI` from env vars
- `classify()`           — one chat-completion call, returns `TokenScore`
- `decide()`             — apply the threshold, return `ClassificationResult`

`openai` is imported lazily so the rest of the CLI does not pay for it.
"""

from __future__ import annotations

import math
import os
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
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


@dataclass(frozen=True)
class ClassificationResult:
    """The output every process emits per item.

    - `label`: the chosen label from the process's label set.
    - `confidence`: probability in [0, 1], computed from the model's logprob.
    - `needs_review`: True when `confidence < threshold` or the label is
      one of `review_labels`. When True, the downstream workflow should
      escalate to a human reviewer instead of acting on the label.
    - `threshold`: the threshold that was applied (for auditability).
    """

    label: str
    confidence: float
    needs_review: bool
    threshold: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_client() -> AzureOpenAI:
    """Construct an `AzureOpenAI` client from environment variables.

    Required env vars:

    - `AZURE_OPENAI_API_KEY`
    - `AZURE_OPENAI_ENDPOINT`
    - `AZURE_OPENAI_API_VERSION` (default: `2024-08-01-preview`)
    """
    from openai import AzureOpenAI

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


def decide(
    score: TokenScore,
    *,
    threshold: float,
    review_labels: tuple[str, ...] = ("unknown", "other"),
) -> ClassificationResult:
    """Apply the threshold to a `TokenScore` and produce the final result.

    Labels in `review_labels` always trigger review, regardless of how
    confident the model is.
    """
    confidence = score.probability
    needs_review = confidence < threshold or score.token in review_labels
    return ClassificationResult(
        label=score.token,
        confidence=confidence,
        needs_review=needs_review,
        threshold=threshold,
    )


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
