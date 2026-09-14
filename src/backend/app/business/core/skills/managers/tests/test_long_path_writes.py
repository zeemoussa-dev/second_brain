"""The engine's writes past Windows' 260-character MAX_PATH.

`read_note` went through `long_path`; `write_note` did not. So an engine write
to any note past the limit failed -- File Enrichment read and summarized four
real long-path attachments and then could not save them, because its first
write (minting the note's `id`) died in `write_note`. Each fixture genuinely
exceeds the limit; one that stayed under it would pass against the bug.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vault_manager as vm


def deep_note(tmp_path: Path) -> Path:
    note = (tmp_path / "Work" / "Threads" / ("2026-06-08 " + "Board Pre-Read " * 5).strip()
            / "files" / ("2026-06-08 04efaede-" + "Board-Meeting_Jun2026 " * 3).strip()
            / "attachment.md")
    assert len(str(note)) > 260, f"fixture is only {len(str(note))} chars -- proves nothing"
    return note


def test_write_note_creates_a_note_past_max_path(tmp_path):
    note = deep_note(tmp_path)
    vm.write_note(note, {"type": "File"}, "\n## Summary\n\n")
    assert os.path.isfile(vm.long_path(note))
    frontmatter, _ = vm.read_note(note)
    assert frontmatter["type"] == "File"


def test_update_rewrites_a_note_past_max_path(tmp_path):
    """The exact call that failed: an applier minting an id on first touch."""
    note = deep_note(tmp_path)
    vm.write_note(note, {"type": "File"}, "\n## Summary\n\nKept.\n")
    vm.update(tmp_path, note, frontmatter={"id": "minted-id"})
    frontmatter, body = vm.read_note(note)
    assert frontmatter["id"] == "minted-id"
    assert "Kept." in body, "the body must survive a frontmatter update"
