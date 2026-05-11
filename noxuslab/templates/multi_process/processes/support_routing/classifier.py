"""Pure-Python classifier for inbound support emails.

Wraps `shared.azure_openai.classify` with this process's labels and
prompt, plus the threshold decision from `shared.classification`. No
Outlook, no SharePoint, no SDK; just `text in, ClassificationResult
out`, so the rest of the platform stays unit-testable.

The Noxus workflow under `workflows/classify_email.py` is the
production entry point: it calls into this module after extracting the
email body and any attachment text.

Usage from the command line (one-shot, hits Azure):

    python -m processes.support_routing.classifier sample_data/billing.txt
"""

from __future__ import annotations

import sys
from pathlib import Path

from openai import AzureOpenAI

from processes.support_routing.labels import LABELS, REVIEW_LABELS, SYSTEM_PROMPT
from shared.azure_openai import build_client, classify
from shared.classification import ClassificationResult, decide

DEFAULT_THRESHOLD = 0.85


def classify_email(
    text: str,
    *,
    client: AzureOpenAI | None = None,
    deployment: str = "gpt-4o",
    threshold: float = DEFAULT_THRESHOLD,
) -> ClassificationResult:
    """Classify one support email and apply the confidence threshold.

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
        sys.exit("usage: python -m processes.support_routing.classifier <path/to/email.txt>")
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    result = classify_email(text)
    print(result.to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
