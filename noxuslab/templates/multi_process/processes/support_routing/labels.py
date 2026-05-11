"""Label set for the support-routing classifier.

One module so the workflow file, the classifier, the tests and the
sample-data generator all import from a single source of truth. If
you add a label, you only edit this file.
"""

from __future__ import annotations

from typing import Final

#: Ordered tuple of allowed labels. Order matters for prompt rendering.
#: Each label starts with a unique first token so the first-token logprob
#: is a clean confidence signal.
LABELS: Final[tuple[str, ...]] = (
    "billing",
    "technical",
    "sales",
    "general",
    "other",
)

#: Labels that always trigger human review, even at high model confidence.
REVIEW_LABELS: Final[tuple[str, ...]] = ("other",)


SYSTEM_PROMPT: Final[str] = (
    "You are a support triage assistant. Classify the email below into "
    "exactly ONE of these labels:\n\n"
    "  billing    - invoices, charges, refunds, payment problems\n"
    "  technical  - bugs, errors, integration failures, outages\n"
    "  sales      - pricing, demos, contract upgrades, new accounts\n"
    "  general    - how-to questions, documentation, onboarding\n"
    "  other      - anything that does not clearly fit the above\n\n"
    "Reply with the single label, lowercase, no punctuation, no explanation."
)
