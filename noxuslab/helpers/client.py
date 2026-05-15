"""Public factory for a configured `noxus_sdk.Client`.

Downstream repos (`noxus-ctt`, `noxus-xxx`) should use this instead of
calling `Client(api_key=os.environ["NOXUS_API_KEY"])` directly. The
factory mirrors what the `noxuslab` CLI does internally:

- Resolves the API key via `_secrets.resolve_api_key()` — env, `.env`,
  or a pluggable `NOXUSLAB_SECRETS_CMD`.
- Reads `NOXUS_BACKEND_URL` (the Noxus tenant base URL) and passes it
  to the SDK when set. Without it, the SDK falls back to its built-in
  default, which only works against the public Noxus cloud.

This is the single chokepoint where staging and production diverge:
flip `NOXUS_BACKEND_URL` + `NOXUS_API_KEY` (typically via
`noxuslab env use staging` / `prod`) and every script and CI job
talks to the right tenant.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from dotenv import load_dotenv

if TYPE_CHECKING:
    from noxus_sdk.client import Client


def make_client() -> Client:
    """Return a `noxus_sdk.Client` configured from the current environment."""
    from noxus_sdk.client import Client

    from noxuslab._secrets import resolve_api_key

    load_dotenv()
    kwargs: dict = {"api_key": resolve_api_key()}
    url = os.environ.get("NOXUS_BACKEND_URL")
    if url:
        kwargs["base_url"] = url
    return Client(**kwargs)
