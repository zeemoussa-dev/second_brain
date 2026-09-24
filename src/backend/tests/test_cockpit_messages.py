"""The Inbox Cockpit lists the emails a Thread is made of.

Operator, 2026-09-24: "I can't See Related Emails to the Thread". A captured Thread
keeps one note per real email under its own `messages/` folder, and the Cockpit --
the cockpit FOR that conversation -- showed everything except those."""
import pytest

from app.business.cockpit import messages
from app.business.core.vault.vault_manager import VaultManager

MESSAGE = """---
type: "RawMessage"
sender: "{sender}"
sender_email: "{email}"
subject: "{subject}"
received: "{received}"
---

body
"""


@pytest.fixture()
def thread(tmp_path, monkeypatch):
    """A Thread note with a messages/ folder beside it, as capture writes it."""
    folder = tmp_path / "Work" / "Threads" / "2026-09-17 Data Platform"
    (folder / "messages").mkdir(parents=True)
    note = folder / "2026-09-17 Data Platform.md"
    note.write_text("---\ntype: \"Thread\"\n---\n\n## Summary\n", encoding="utf-8")
    written = [
        ("Tim Burke", "tburke@masdar.ae", "Re: Data Platform", "2026-09-17 20:13:22+00:00"),
        ("Amr Elsayed", "amraze@microsoft.com", "RE: Data Platform", "2026-09-22 13:05:01+00:00"),
    ]
    for sender, email, subject, received in written:
        (folder / "messages" / f"{received[:10]}-{sender}.md").write_text(
            MESSAGE.format(sender=sender, email=email, subject=subject, received=received), encoding="utf-8")
    monkeypatch.setattr(VaultManager, "get_index",
                        lambda self: {"2026-09-17 Data Platform": {"path": str(note), "stem": note.stem}})
    return folder


def test_every_email_in_the_thread_is_listed_newest_first(thread):
    listed = messages.list_messages("2026-09-17 Data Platform")

    assert [m["sender"] for m in listed] == ["Amr Elsayed", "Tim Burke"]
    assert listed[0]["subject"] == "RE: Data Platform"
    assert listed[0]["sender_email"] == "amraze@microsoft.com"
    assert listed[0]["received"].startswith("2026-09-22")
    # Each email is a real note, so the screens can link straight to it.
    assert listed[0]["stem"] == "2026-09-22-Amr Elsayed"


def test_a_note_in_the_folder_that_is_not_a_message_is_left_out(thread):
    (thread / "messages" / "notes.md").write_text("---\ntype: \"Note\"\n---\n\nmine\n", encoding="utf-8")

    assert len(messages.list_messages("2026-09-17 Data Platform")) == 2


def test_a_subject_with_no_messages_folder_lists_nothing(tmp_path, monkeypatch):
    """A Meeting, or a Thread captured before the folder existed -- not an error."""
    note = tmp_path / "meeting.md"
    note.write_text("---\ntype: \"Meeting\"\n---\n", encoding="utf-8")
    monkeypatch.setattr(VaultManager, "get_index",
                        lambda self: {"meeting": {"path": str(note), "stem": "meeting"}})

    assert messages.list_messages("meeting") == []


def test_an_unknown_subject_lists_nothing(monkeypatch):
    monkeypatch.setattr(VaultManager, "get_index", lambda self: {})

    assert messages.list_messages("nope") == []


def test_an_unreadable_message_is_skipped_not_fatal(thread, monkeypatch, caplog):
    (thread / "messages" / "broken.md").write_text("---\ntype: \"RawMessage\"\n", encoding="utf-8")
    from app.vault import vault_manager as vm

    real_read = vm.read_note

    def explode(path):
        if "broken" in str(path):
            raise OSError("unreadable")
        return real_read(path)

    monkeypatch.setattr(messages.vm, "read_note", explode)

    assert len(messages.list_messages("2026-09-17 Data Platform")) == 2
    assert "skipping unreadable message note" in caplog.text
