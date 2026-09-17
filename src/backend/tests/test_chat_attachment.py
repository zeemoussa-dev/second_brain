"""Chat attachments: the Chat paperclip's `POST /agents/{id}/chat/attachment`
had no backend route since the 2026-08-20 redesign, so attaching a file broke
Chat. The file is now saved into the install and handed to the agent."""
import pytest
from fastapi.testclient import TestClient

import app.main as main_app
from app.api import agents_router
from app.business.hermes import chat_sessions
from app.business.hermes.client import HermesUnavailableError
from app.business.logic import chat_attachment
from app.config import settings

client = TestClient(main_app.app, raise_server_exceptions=False)


@pytest.fixture()
def data_path(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path)
    return tmp_path


@pytest.fixture()
def primary(monkeypatch):
    """Primary exists, and every turn sent to it is recorded instead of reaching Hermes."""
    sent = []

    class Profiles:
        def find_by_id(self, agent_id):
            return object() if agent_id == "default" else None

    class Client:
        profiles = Profiles()

    async def send_and_await_reply(agent_id, message):
        sent.append((agent_id, message))
        return "Filed it."

    monkeypatch.setattr(agents_router, "get_client", lambda: Client())
    monkeypatch.setattr(chat_sessions, "send_and_await_reply", send_and_await_reply)
    return sent


def attach(name, content, message="What is this?", agent_id="default"):
    return client.post(
        f"/agents/{agent_id}/chat/attachment",
        data={"message": message},
        files={"file": (name, content, "application/octet-stream")},
    )


@pytest.mark.parametrize("given, expected", [
    ("report.pdf", "report.pdf"),
    ("C:\\Users\\someone\\Desktop\\plan.docx", "plan.docx"),
    ("../../outside.txt", "outside.txt"),
    ('bad:name?.txt', "badname.txt"),
])
def test_a_filename_becomes_one_safe_path_segment(given, expected):
    assert chat_attachment.safe_filename(given) == expected


def test_a_long_filename_is_shortened_but_keeps_its_extension():
    name = chat_attachment.safe_filename("x" * 400 + ".xlsx")

    assert len(name) == 150 and name.endswith(".xlsx")


def test_a_file_is_saved_and_handed_to_the_agent_with_its_path(data_path, primary):
    response = attach("notes.txt", b"hello")

    assert response.status_code == 200
    assert response.json() == {"reply": "Filed it.", "attachment_status": "sent_to_agent", "vault_path": None}
    [saved] = list((data_path / "data" / "chat-uploads").rglob("notes.txt"))
    assert saved.read_bytes() == b"hello"
    [(agent_id, message)] = primary
    assert agent_id == "default"
    assert message.startswith("What is this?")
    assert str(saved) in message


def test_two_files_with_the_same_name_do_not_overwrite_each_other(data_path, primary):
    attach("same.txt", b"first")
    attach("same.txt", b"second")

    contents = sorted(p.read_bytes() for p in (data_path / "data" / "chat-uploads").rglob("same.txt"))
    assert contents == [b"first", b"second"]


def test_an_empty_file_is_rejected_without_reaching_the_agent(data_path, primary):
    body = attach("empty.txt", b"").json()

    assert body["attachment_status"] == "rejected"
    assert "empty" in body["reply"]
    assert primary == []


def test_a_file_over_the_limit_is_rejected_without_reaching_the_agent(data_path, primary, monkeypatch):
    monkeypatch.setattr(chat_attachment, "MAX_ATTACHMENT_BYTES", 4)

    body = attach("big.bin", b"12345").json()

    assert body["attachment_status"] == "rejected"
    assert primary == []
    assert not (data_path / "data" / "chat-uploads").exists()


def test_an_unknown_agent_is_a_404(data_path, primary):
    assert attach("notes.txt", b"hello", agent_id="nobody").status_code == 404


def test_hermes_being_down_is_a_502_not_a_fabricated_reply(data_path, primary, monkeypatch):
    async def unavailable(agent_id, message):
        raise HermesUnavailableError("gateway is not running")

    monkeypatch.setattr(chat_sessions, "send_and_await_reply", unavailable)

    assert attach("notes.txt", b"hello").status_code == 502
