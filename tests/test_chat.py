"""Tests for `noxuslab.chat` (offline, mocked)."""

from unittest.mock import MagicMock, patch

from noxuslab.chat import _create_conversation, _make_client, _stream_reply, one_shot


def test_make_client_raises_without_key(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("NOXUS_API_KEY", raising=False)
    monkeypatch.delenv("NOXUSLAB_SECRETS_CMD", raising=False)
    import pytest

    from noxuslab.errors import AuthMissing

    with pytest.raises(AuthMissing):
        _make_client()


@patch("noxuslab.chat._make_client")
def test_create_conversation_with_agent(mock_client):
    client = MagicMock()
    mock_client.return_value = client
    client.conversations.create.return_value = MagicMock()
    result = _create_conversation(client, agent_id="abc-123", model=None)
    client.conversations.create.assert_called_once_with(name="noxuslab-chat", agent_id="abc-123")
    assert result is not None


@patch("noxuslab.chat._make_client")
def test_create_conversation_without_agent(mock_client):
    client = MagicMock()
    mock_client.return_value = client
    client.conversations.create.return_value = MagicMock()
    _create_conversation(client, agent_id=None, model="test-model")
    call_kwargs = client.conversations.create.call_args[1]
    assert call_kwargs["name"] == "noxuslab-chat"
    assert "settings" in call_kwargs


def test_stream_reply_collects_tokens(capsys):
    """iter_messages yields events; _stream_reply concatenates them."""
    event1 = MagicMock(type="text", content="Hello ")
    event2 = MagicMock(type="text", content="world!")
    event_end = MagicMock(type="conversation_end", content=None)
    conv = MagicMock()
    conv.iter_messages.return_value = iter([event1, event2, event_end])
    result = _stream_reply(conv)
    assert result == "Hello world!"
    captured = capsys.readouterr()
    assert "Hello " in captured.out
    assert "world!" in captured.out


@patch("noxuslab.chat.load_dotenv")
@patch("noxuslab.chat._make_client")
@patch("noxuslab.chat._create_conversation")
@patch("noxuslab.chat._send_blocking")
def test_one_shot(mock_send, mock_create_conv, mock_client, mock_dotenv):
    mock_send.return_value = "answer"
    rc = one_shot("hello?", agent_id=None, model=None)
    assert rc == 0
    mock_send.assert_called_once()


@patch("noxuslab.chat.load_dotenv")
@patch("noxuslab.chat._make_client")
@patch("noxuslab.chat._create_conversation")
@patch("noxuslab.chat._send_blocking")
@patch("builtins.input", side_effect=["hi", "/exit"])
def test_start_chat_basic(mock_input, mock_send, mock_create_conv, mock_client, mock_dotenv):
    from noxuslab.chat import start_chat

    mock_send.return_value = "response"
    rc = start_chat(agent_id=None, model=None)
    assert rc == 0
    mock_send.assert_called_once()


@patch("noxuslab.chat.load_dotenv")
@patch("noxuslab.chat._make_client")
@patch("noxuslab.chat._create_conversation")
@patch("builtins.input", side_effect=EOFError)
def test_start_chat_eof(mock_input, mock_create_conv, mock_client, mock_dotenv):
    from noxuslab.chat import start_chat

    rc = start_chat(agent_id=None, model=None)
    assert rc == 0
