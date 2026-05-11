"""Label set for workspace `__workspace__`.

One module so the workflow files, the classifier and the tests all
import from a single source of truth. Add or rename a label here and
nowhere else.
"""

from __future__ import annotations

from typing import Final

#: Ordered tuple of allowed labels. Order matters for prompt rendering.
#: Each label starts with a unique first token so the first-token logprob
#: is a clean confidence signal.
LABELS: Final[tuple[str, ...]] = (
    "example_a",
    "example_b",
    "other",
)

#: Labels that always trigger human review, even at high model confidence.
REVIEW_LABELS: Final[tuple[str, ...]] = ("other",)


SYSTEM_PROMPT: Final[str] = (
    "You are a triage assistant. Classify the input below into "
    "exactly ONE of these labels:\n\n"
    "  example_a  - replace this with the real label and its meaning\n"
    "  example_b  - replace this too\n"
    "  other      - anything that does not clearly fit the above\n\n"
    "Reply with the single label, lowercase, no punctuation, no explanation."
)
