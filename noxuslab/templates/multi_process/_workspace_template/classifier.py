"""Pure-Python classifier for workspace `__workspace__`.

Wraps `noxuslab.classify.classify` with this workspace's labels and
prompt, plus the threshold decision from `noxuslab.classify.decide`.
No SDK, no platform code; just `text in, ClassificationResult out`,
so the rest of the pipeline stays unit-testable.

The Noxus workflows under `workflows/` are the production entry
points; they call into this module after extracting the input.

Usage from the command line (one-shot, hits Azure):

    python -m __workspace__.classifier test_fixtures/example_a.txt
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from __workspace__.labels import LABELS, REVIEW_LABELS, SYSTEM_PROMPT
from noxuslab.classify import (
    ClassificationResult,
    build_client,
    classify,
    decide,
)

if TYPE_CHECKING:
    from openai import AzureOpenAI

DEFAULT_THRESHOLD = 0.85


def classify_text(
    text: str,
    *,
    client: AzureOpenAI | None = None,
    deployment: str = "gpt-4o",
    threshold: float = DEFAULT_THRESHOLD,
) -> ClassificationResult:
    """Classify one input and apply the confidence threshold.

    `client` is injected for tests; production callers pass `None` and
    let `build_client()` read Azure credentials from the environment.
    """
    azure = client or build_client()
    score = classify(
        azure,
        deployment=deployment,
        system_prompt=SYSTEM_PROMPT,
        user_content=text,
        allowed_labels=list(LABELS),
    )
    return decide(score, threshold=threshold, review_labels=REVIEW_LABELS)


def _cli() -> int:
    if len(sys.argv) != 2:
        sys.exit("usage: python -m __workspace__.classifier <path/to/input.txt>")
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    result = classify_text(text)
    print(result.to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
