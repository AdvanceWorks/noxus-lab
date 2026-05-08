"""Tests for `noxuslab._secrets` (offline)."""

import pytest

from noxuslab._secrets import resolve_api_key
from noxuslab.errors import AuthMissing


def test_resolve_from_env(monkeypatch):
    monkeypatch.setenv("NOXUS_API_KEY", "from-env")
    monkeypatch.delenv("NOXUSLAB_SECRETS_CMD", raising=False)
    assert resolve_api_key() == "from-env"


def test_resolve_raises_when_unset(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("NOXUS_API_KEY", raising=False)
    monkeypatch.delenv("NOXUSLAB_SECRETS_CMD", raising=False)
    with pytest.raises(AuthMissing):
        resolve_api_key()


def test_resolve_from_command(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("NOXUS_API_KEY", raising=False)
    # Cross-platform: use python -c to print a value.
    import sys

    cmd = f'"{sys.executable}" -c "print(\'from-cmd\')"'
    monkeypatch.setenv("NOXUSLAB_SECRETS_CMD", cmd)
    assert resolve_api_key() == "from-cmd"


def test_resolve_command_failure_raises(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("NOXUS_API_KEY", raising=False)
    monkeypatch.setenv("NOXUSLAB_SECRETS_CMD", "this-binary-does-not-exist-xyz")
    with pytest.raises(AuthMissing):
        resolve_api_key()
