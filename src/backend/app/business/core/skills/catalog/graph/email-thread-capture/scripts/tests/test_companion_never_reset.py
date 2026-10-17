"""Capturing the same attachment twice must not undo work done on it since.

File Enrichment writes an attachment note's Summary; the operator writes its
Personal Notes. Capture meets the same attachment again whenever a backfill
overlaps or a lost file is re-fetched -- and rewrote the note from scratch
with an empty Summary.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vault_lib


def capture(tmp_path: Path) -> dict:
    thread_dir = tmp_path / "Work" / "Threads" / "2026-06-10 Deal"
    thread_dir.mkdir(parents=True, exist_ok=True)
    return vault_lib.write_file_companion(
        tmp_path, subfolder=thread_dir, file_slug="2026-06-10 abcd1234-proposal.pdf",
        original_filename="proposal.pdf", content=b"%PDF-1.4 v1", summary="",
        source_thread="[[2026-06-10 Deal]]")


def test_a_second_capture_leaves_an_enriched_note_alone(tmp_path):
    first = capture(tmp_path)
    note = Path(first["companion_path"])
    note.write_text(note.read_text(encoding="utf-8").replace(
        "## Summary\n\n", "## Summary\n\nCore42 proposal, v1, scope and price.\n"),
        encoding="utf-8")

    second = capture(tmp_path)

    assert second["companion_path"] == first["companion_path"]
    assert second.get("already_captured") is True
    assert "Core42 proposal, v1, scope and price." in note.read_text(encoding="utf-8")


def test_the_first_capture_still_writes_file_and_note(tmp_path):
    result = capture(tmp_path)
    assert Path(result["file_path"]).read_bytes() == b"%PDF-1.4 v1"
    assert "## Summary" in Path(result["companion_path"]).read_text(encoding="utf-8")
    assert "already_captured" not in result
