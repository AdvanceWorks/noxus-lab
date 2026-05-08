"""Offline tests for `noxuslab agents` (codegen + push round-trip)."""

from __future__ import annotations

from pathlib import Path

import pytest

from noxuslab.agent_codegen import agent_to_python
from noxuslab.cli import _load_agent_file
from noxuslab.errors import BadFile


def _make_agent():
    """Build a real `Agent` instance via the SDK pydantic models, no network."""
    from noxus_sdk.resources.assistants import Agent
    from noxus_sdk.resources.conversations import (
        ConversationSettings,
        WebResearchTool,
    )

    settings = ConversationSettings(
        model=["gemini-2.5-flash"],
        temperature=0.7,
        max_tokens=4096,
        tools=[WebResearchTool()],
        persona="helpful assistant",
        tone=None,
        extra_instructions=None,
    )
    return Agent.model_construct(
        client=None,  # type: ignore[arg-type]
        id="11111111-1111-1111-1111-111111111111",
        name="my agent",
        definition=settings,
        draft_definition=None,
    )


def test_agent_to_python_contains_provenance_and_settings():
    code = agent_to_python(_make_agent(), source_id="11111111-1111-1111-1111-111111111111")
    assert "noxuslab agents pull" in code
    assert "from 11111111" in code
    assert "agent_name = 'my agent'" in code
    assert "agent_id = '11111111-1111-1111-1111-111111111111'" in code
    assert "ConversationSettings.model_validate" in code
    assert '"web_research"' in code  # tool serialised


def test_agent_to_python_round_trip_loads(tmp_path: Path, monkeypatch):
    """Generated file must execute and yield matching name/settings/id."""
    monkeypatch.setenv("NOXUS_API_KEY", "test")
    agent = _make_agent()
    code = agent_to_python(agent, source_id=agent.id)
    f = tmp_path / "agent.py"
    f.write_text(code, encoding="utf-8")
    name, settings, agent_id = _load_agent_file(f)
    assert name == "my agent"
    assert agent_id == agent.id
    # Settings must be a ConversationSettings with the same shape.
    from noxus_sdk.resources.conversations import ConversationSettings

    assert isinstance(settings, ConversationSettings)
    assert settings.model == ["gemini-2.5-flash"]
    assert len(settings.tools) == 1
    assert settings.tools[0].type == "web_research"


def test_load_agent_file_rejects_missing_path(tmp_path: Path):
    with pytest.raises(BadFile, match="not found"):
        _load_agent_file(tmp_path / "nope.py")


def test_load_agent_file_rejects_missing_name(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("NOXUS_API_KEY", "test")
    f = tmp_path / "bad.py"
    f.write_text("agent_settings = object()\n", encoding="utf-8")
    with pytest.raises(BadFile, match="agent_name"):
        _load_agent_file(f)


def test_load_agent_file_rejects_missing_settings(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("NOXUS_API_KEY", "test")
    f = tmp_path / "bad.py"
    f.write_text("agent_name = 'x'\n", encoding="utf-8")
    with pytest.raises(BadFile, match="agent_settings"):
        _load_agent_file(f)


def test_agents_pull_writes_to_default_path(tmp_path: Path, monkeypatch):
    """`cmd_agents_pull` writes under `agents/NN_<slug>.py` by default."""
    import argparse

    from noxuslab import cli

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "_client", lambda: object())
    monkeypatch.setattr(cli, "load_dotenv", lambda *a, **k: None)

    agent = _make_agent()
    monkeypatch.setattr(
        cli,
        "net_call",
        lambda fn, what: agent,  # noqa: ARG005
    )

    args = argparse.Namespace(agent_id=agent.id, out=None, force=False)
    rc = cli.cmd_agents_pull(args)
    assert rc == 0
    files = list((tmp_path / "agents").glob("*.py"))
    assert len(files) == 1
    assert files[0].name == "01_my_agent.py"
    assert "agent_name = 'my agent'" in files[0].read_text(encoding="utf-8")


def test_agents_delete_requires_yes():
    import argparse

    from noxuslab import cli

    args = argparse.Namespace(agent_id="11111111-1111-1111-1111-111111111111", yes=False)
    with pytest.raises(BadFile, match="--yes"):
        cli.cmd_agents_delete(args)
