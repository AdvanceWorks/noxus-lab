"""Network helpers: friendly errors, retry-with-backoff, audit hooks.

The SDK uses httpx internally and does not expose timeouts. We can't
inject one without monkey-patching, so this module focuses on the
boundary: converting low-level errors into typed `NoxusLabError`s the
CLI knows how to print, and retrying transient failures.
"""

import os
import random
import time
from collections.abc import Callable
from typing import TypeVar

from noxuslab.errors import NoxusLabError

T = TypeVar("T")

# Tunable via env so ops teams can tighten limits without a release.
MAX_RETRIES = int(os.environ.get("NOXUSLAB_MAX_RETRIES", "3"))
BASE_DELAY = float(os.environ.get("NOXUSLAB_BASE_DELAY", "0.5"))
MAX_DELAY = float(os.environ.get("NOXUSLAB_MAX_DELAY", "8.0"))


class NetworkError(NoxusLabError):
    """A network call failed after retries."""


class RateLimited(NetworkError):
    """The Noxus backend returned 429."""


def _is_retryable(exc: BaseException) -> bool:
    """True if the exception looks like a transient network failure."""
    name = type(exc).__name__
    if name in {"TimeoutException", "ConnectError", "ReadTimeout", "WriteTimeout", "PoolTimeout"}:
        return True
    # httpx HTTPStatusError carries a response with a status code.
    resp = getattr(exc, "response", None)
    if resp is not None:
        status = getattr(resp, "status_code", None)
        if status in {429, 502, 503, 504}:
            return True
    # SDK's own RequestFailedError wraps anything from httpx.
    msg = str(exc).lower()
    return "timeout" in msg or "temporarily unavailable" in msg


def _delay(attempt: int) -> float:
    """Exponential backoff with jitter. attempt is 0-indexed."""
    raw = min(MAX_DELAY, BASE_DELAY * (2**attempt))
    return raw * (0.5 + random.random() * 0.5)  # noqa: S311 — jitter, not crypto


def call(fn: Callable[[], T], *, what: str = "request") -> T:
    """Run `fn` with retry-on-transient-failure and friendly errors.

    Wraps a no-arg callable so call sites stay terse:

        wf = call(lambda: client.workflows.get(workflow_id=wid), what="get workflow")
    """
    last_exc: BaseException | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            return fn()
        except NoxusLabError:  # noqa: PERF203 — retry loop, not a hot path
            raise  # already typed, don't retry
        except Exception as exc:  # noqa: BLE001 — boundary
            last_exc = exc
            if attempt < MAX_RETRIES and _is_retryable(exc):
                time.sleep(_delay(attempt))
                continue
            resp = getattr(exc, "response", None)
            status = getattr(resp, "status_code", None) if resp is not None else None
            if status == 429:
                raise RateLimited(f"{what}: rate limited by Noxus (429)") from exc
            raise NetworkError(f"{what}: {type(exc).__name__}: {exc}") from exc
    # Unreachable — loop either returns or raises, but mypy/pyright like it.
    raise NetworkError(f"{what}: exhausted retries") from last_exc
