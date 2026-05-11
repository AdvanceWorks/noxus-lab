"""Classification result types and threshold logic shared by all processes.

A process defines its own label set + system prompt. Everything below
(scoring, threshold decision, output schema) is identical across
processes, so it lives here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from shared.azure_openai import TokenScore


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
