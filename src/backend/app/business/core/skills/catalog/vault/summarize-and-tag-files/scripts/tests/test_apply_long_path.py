"""Applying a review to an attachment whose note path passes MAX_PATH.

The first scheduled File Enrichment run read and summarized 10 attachments and
could write only 6: the 4 with note paths past Windows' 260-character limit
failed at apply. The reader and the selector had been made long-path-safe; the
applier -- and whatever it calls -- had not. This runs the whole apply against a
fixture that genuinely exceeds the limit, with the real shipped templates.
"""
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vault_manager as vm

_MASTERS = Path(__file__).resolve().parents[6] / "templates" / "masters"
# The real layout: the Thread note sits under MAX_PATH (~220 characters on the
# operator's vault) while the attachment note two levels below it does not.
# pytest's temporary root is ~95 characters deep, so the Thread name is kept
# short enough that only the attachment crosses the limit.
_THREAD = "2026-06-08 Core42 Holding Board Pre-Read"
_SLUG = "2026-06-08 04efaede-Core42 Holding RSC Ltd_Board-Meeting_Jun2026 - Final Version"


@pytest.fixture()
def deep(tmp_path, monkeypatch):
    config = tmp_path / "config"
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(config))
    for template_id in ("file", "thread"):
        target = config / "data" / "Templates" / template_id
        target.mkdir(parents=True)
        shutil.copy(_MASTERS / template_id / "Template.json", target / "Template.json")

    thread_dir = tmp_path / "Work" / "Threads" / _THREAD
    thread_dir.mkdir(parents=True)
    thread_note = thread_dir / f"{_THREAD}.md"
    thread_note.write_text(
        f'---\ntype: "Thread"\nid: "conv-1"\ntags: ["kind/thread"]\n---\n\n'
        f"## Summary\n\n\n## Personal Notes\n\n\n## Actions\n\n\n## Conversation\n\n\n"
        f"## Related\n\n\n## Files\n\n- [[{_SLUG}]]\n", encoding="utf-8")

    folder = thread_dir / "files" / _SLUG
    note = folder / f"{_SLUG}.md"
    assert len(str(note)) > 260, f"fixture is only {len(str(note))} chars -- proves nothing"
    Path(vm.long_path(folder)).mkdir(parents=True)
    Path(vm.long_path(note)).write_text(
        '---\ntype: "File"\noriginal_filename: "Board-Meeting_Jun2026.pdf"\n'
        f'source_thread: "[[{_THREAD}]]"\ntags: ["kind/attachment", "type/pdf"]\n---\n\n'
        "## Summary\n\n\n## Personal Notes\n", encoding="utf-8")
    Path(vm.long_path(folder / "Board-Meeting_Jun2026.pdf")).write_bytes(b"%PDF-1.4")
    return tmp_path, note, thread_note


def review(note: Path) -> dict:
    return {"file_path": str(note), "summary": "Board pre-read for the June meeting.",
            "short_summary": "June board pre-read", "companies": []}


def test_a_review_is_applied_to_a_note_past_max_path(deep):
    import apply_file_review as a
    vault_path, note, thread_note = deep

    result = a.apply_file_review(vault_path, review(note))

    assert not result.get("skipped")
    assert "Board pre-read for the June meeting." in vm.get_section_content(note, "Summary")
    assert f"- [[{_SLUG}]] -- June board pre-read" in vm.get_section_content(thread_note, "Files")


def test_the_skip_guard_holds_past_max_path(deep):
    """The guard is what stops a re-picked file from being overwritten. A
    plain is_file() past the limit is False, which silently disables it."""
    import apply_file_review as a
    vault_path, note, _ = deep
    a.apply_file_review(vault_path, review(note))

    second = a.apply_file_review(vault_path, {**review(note), "summary": "Overwritten."})

    assert second.get("skipped") is True
    assert "Overwritten." not in vm.get_section_content(note, "Summary")
