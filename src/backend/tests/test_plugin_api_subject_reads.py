"""Plugin API v6 -- a plugin can show a subject the way the Cockpit does.

`vault.attachments()` and `vault.read_section()` exist so a plugin showing a
captured Thread (My Day's Emails tab) does not re-derive two vault conventions:
where an attachment lives, and what a note's `Summary` section is. Both have real
traps in them -- an attachment's folder repeats its own long name and passes
Windows' 260-character limit (`BUG-077`).
"""
import os

import pytest

from app import plugin_api
from app.business.core.vault import vault_manager as module
from app.business.core.vault.vault_manager import VaultManager
from app.config import settings
from app.obsidian.notes import long_path

THREAD = "Work/Threads/2026-09-22 Masdar order form/2026-09-22 Masdar order form.md"
THREAD_STEM = "2026-09-22 Masdar order form"
ATTACHMENT = "Work/Threads/2026-09-22 Masdar order form/Files/Order-Form-signed/Order-Form-signed.md"

THREAD_BODY = """## Summary

Masdar returned the [[Order Form]]; legal asked for one clause change.

## Details

Nothing else yet.
"""


def write(path, frontmatter_type, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'---\ntype: "{frontmatter_type}"\n---\n\n{body}', encoding="utf-8")
    return path


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "vault_path", tmp_path)
    thread = write(tmp_path / THREAD, "Thread", THREAD_BODY)
    attachment = write(tmp_path / ATTACHMENT, "File", "## Summary\n\nThe signed order form.\n")
    (attachment.parent / "Order-Form-signed.pdf").write_bytes(b"%PDF-1.4 signed")
    monkeypatch.setattr(module.vault_writer, "list_all_note_paths", lambda: [thread, attachment])
    VaultManager().rebuild_index()
    return tmp_path


def test_a_subjects_attachments_come_back_with_their_real_file(vault):
    [attachment] = plugin_api.VaultApi().attachments(THREAD_STEM)

    assert attachment["filename"] == "Order-Form-signed.pdf"
    assert attachment["title"] == "Order-Form-signed"


def test_a_subject_with_no_files_folder_has_no_attachments(vault):
    assert plugin_api.VaultApi().attachments("Order-Form-signed") == []


def test_an_unknown_subject_is_empty_rather_than_an_error(vault):
    assert plugin_api.VaultApi().attachments("No Such Thread") == []


def test_a_named_section_of_a_note_is_readable(vault):
    """The Summary a Skill wrote, as written -- wikilinks and all, for the host's
    own renderer to turn into links."""
    summary = plugin_api.VaultApi().read_section(vault / THREAD, "Summary")

    assert summary == "Masdar returned the [[Order Form]]; legal asked for one clause change."


def test_a_section_the_note_does_not_have_is_none(vault):
    assert plugin_api.VaultApi().read_section(vault / THREAD, "Decisions") is None


def test_an_unreadable_note_is_none_rather_than_fatal(vault):
    """A panel showing a summary must not take the screen down with it -- the same
    rule the Cockpit's own panels follow."""
    assert plugin_api.VaultApi().read_section(vault / "Work/Threads/Gone.md", "Summary") is None


def test_the_asset_a_long_attachment_path_holds_is_still_found(tmp_path, monkeypatch):
    """An attachment's folder repeats the attachment's own name, so a long subject
    puts the real file past Windows' 260-character limit -- where `is_file()`
    answers False rather than raising, and the file simply 404s (`BUG-077`, on the
    read side of an asset)."""
    monkeypatch.setattr(settings, "vault_path", tmp_path)
    long_name = "2026-09-22 Masdar Core42 order form and credit hold alignment and the rest of a real subject line"
    folder = tmp_path / "Work" / "Threads" / long_name / "Files" / long_name
    note = folder / f"{long_name}.md"
    # Creating them needs the prefix too: pytest's own tmp path plus a real
    # subject line is already past the limit, which is the install's situation.
    os.makedirs(long_path(folder), exist_ok=True)
    with open(long_path(note), "w", encoding="utf-8") as handle:
        handle.write('---\ntype: "File"\n---\n\n## Summary\n\nA long one.\n')
    with open(long_path(folder / "Order-Form-signed.pdf"), "wb") as handle:
        handle.write(b"%PDF-1.4 signed")
    monkeypatch.setattr(module.vault_writer, "list_all_note_paths", lambda: [note])
    manager = VaultManager()
    manager.rebuild_index()

    assert len(str(folder / "Order-Form-signed.pdf")) > 260
    assert manager.resolve_asset_path(long_name, "Order-Form-signed.pdf") is not None
