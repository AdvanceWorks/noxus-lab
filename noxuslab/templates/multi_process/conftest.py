"""Top-level pytest fixtures shared by every test in this repo.

The single fixture exposed here is `fake_azure_client` — a factory that
returns an object shaped like `openai.AzureOpenAI` and always replies
with one fixed (label, probability) pair. The real implementation
lives in `noxuslab.testing` so the same helper backs every repo
scaffolded by `noxuslab init --multi-process`.

Per-workspace and per-process tests pick this up automatically because
pytest walks up from the test file looking for `conftest.py`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from noxuslab.testing import make_fake_azure_client


@pytest.fixture
def fake_azure_client() -> Callable[[str, float], Any]:
    """Factory fixture: `fake_azure_client("vacation", 0.95)` -> fake Azure client."""
    return make_fake_azure_client
