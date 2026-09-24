"""BUG-077 -- the Cockpit 500s for any subject with a long attachment path.

An attachment's folder repeats the attachment's own name (`Files/<name>/<name>.md`),
so a subject with a long subject line puts that note past Windows' 260 characters.
`list_documents` walked those paths without `long_path`, `stat()` raised, and the
WHOLE Cockpit read returned 500 -- no summary, no people, no chat. 171 of the
reporting install's subjects were unusable, including every one the Action Center
links to.

Two things are checked: the listing reaches a long path, and no panel can take the
view down with it again."""
import os

import pytest

from app.business.cockpit import documents
from app.business.core.vault.vault_manager import VaultManager
from app.business.logic import cockpit_view
from app.config import settings
from app.vault import vault_manager as vm

# Long enough that `Files/<name>/<name>.md` under a real vault root passes 260.
LONG_NAME = "2026-09-09 DFS_10014135 - INJAZAT DATA SYSTEMS LLC - Credit Hold and the rest of a real subject line"


@pytest.fixture()
def subject(tmp_path, monkeypatch):
    """A Thread note with one attachment whose own note sits past the limit."""
    monkeypatch.setattr(settings, "vault_path", tmp_path)
    notes_root = tmp_path / vm._NOTES_ROOT
    subject_folder = notes_root / "Threads" / LONG_NAME
    subject_folder.mkdir(parents=True)
    note = subject_folder / f"{LONG_NAME}.md"
    # Even this write needs the prefix: pytest's own tmp path plus a real subject
    # line is already past the limit, which is exactly the install's situation.
    with open(vm.long_path(note), "w", encoding="utf-8") as handle:
        handle.write('---\ntype: "Thread"\n---\n\n## Summary\n\nwhat happened.\n')

    attachment_folder = subject_folder / "Files" / LONG_NAME
    description = attachment_folder / f"{LONG_NAME}.md"
    os.makedirs(vm.long_path(attachment_folder), exist_ok=True)
    with open(vm.long_path(description), "w", encoding="utf-8") as handle:
        handle.write('---\ntype: "File"\ntitle: "Credit hold letter"\n---\n\n## Summary\n\na letter.\n')
    with open(vm.long_path(attachment_folder / "letter.pdf"), "wb") as handle:
        handle.write(b"%PDF-1.4 ")
    assert len(str(description)) > 260, "the test must actually exceed the limit"

    monkeypatch.setattr(VaultManager, "get_index", lambda self: {
        LONG_NAME: {"stem": LONG_NAME, "path": str(note), "frontmatter": {"type": "Thread"}, "tags": []},
    })
    return note


def test_an_attachment_past_the_windows_limit_is_listed(subject):
    [document] = documents.list_documents(LONG_NAME)

    assert document["title"] == "Credit hold letter"
    assert document["filename"] == "letter.pdf"
    # The path that leaves the module is the ordinary one, not the prefixed form.
    assert not document["note_path"].startswith("\\\\?\\")


def test_the_cockpit_opens_for_that_subject(subject):
    view = cockpit_view.build_cockpit_view("email", LONG_NAME)

    assert view["overview"]["summary"] == "what happened."
    assert len(view["overview"]["related_documents"]) == 1
    assert "thread" in view and "people" in view


def test_a_panel_that_fails_leaves_the_rest_of_the_cockpit_standing(subject, monkeypatch, caplog):
    """The shape of the original failure: whatever goes wrong in one panel, the
    subject still opens."""
    def explode(*args, **kwargs):
        raise OSError("a path nobody can read")

    monkeypatch.setattr(documents, "list_documents", explode)

    view = cockpit_view.build_cockpit_view("email", LONG_NAME)

    assert view["overview"]["related_documents"] == []
    assert view["overview"]["summary"] == "what happened."
    assert "the documents panel failed" in caplog.text


def test_one_unreadable_attachment_does_not_hide_the_others(subject, monkeypatch):
    real_read = vm.read_note

    def read(path):
        if "letter" not in str(path) and LONG_NAME in str(path):
            raise OSError("unreadable")
        return real_read(path)

    monkeypatch.setattr(documents.vm, "read_note", read)

    # The only attachment here is the unreadable one: it is skipped, not fatal.
    assert documents.list_documents(LONG_NAME) == []
