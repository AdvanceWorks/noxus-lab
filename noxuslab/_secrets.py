"""Secret resolution: env var, .env, or external command.

The CLI never hardcodes a secret manager. Operators choose how to
provide `NOXUS_API_KEY` — most flexibly via `NOXUSLAB_SECRETS_CMD`,
which lets you plug in AWS Secrets Manager, Azure Key Vault, Vault,
1Password, or anything that prints the secret to stdout.

Resolution order (first hit wins):
1. `NOXUS_API_KEY` already in the environment.
2. `.env` file in the current directory (loaded by python-dotenv).
3. `NOXUSLAB_SECRETS_CMD` shell command — its stdout becomes the key.

In production, prefer (3): inject `NOXUSLAB_SECRETS_CMD` at deploy time
and never write the key to disk.
"""

import os
import shlex
import subprocess  # noqa: S404 — boundary, command is operator-controlled

from dotenv import load_dotenv

from noxuslab.errors import AuthMissing


def resolve_api_key() -> str:
    """Return `NOXUS_API_KEY` from env, .env, or the configured command.

    Raises `AuthMissing` if no source produces a non-empty value.
    """
    key = os.environ.get("NOXUS_API_KEY")
    if key:
        return key

    load_dotenv()
    key = os.environ.get("NOXUS_API_KEY")
    if key:
        return key

    cmd = os.environ.get("NOXUSLAB_SECRETS_CMD")
    if cmd:
        try:
            # shlex.split + shell=False prevents shell injection.
            out = subprocess.run(  # noqa: S603 — operator-controlled
                shlex.split(cmd),
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise AuthMissing(f"NOXUSLAB_SECRETS_CMD failed: {e}") from e
        key = out.stdout.strip()
        if key:
            os.environ["NOXUS_API_KEY"] = key
            return key

    raise AuthMissing(
        "NOXUS_API_KEY not set. Provide it via env, .env, "
        "or NOXUSLAB_SECRETS_CMD (e.g. 'aws secretsmanager get-secret-value ...')."
    )
