"""Attachments past Windows' 260-character MAX_PATH -- the real shape, not a toy.

256 real attachments were lost to this: capture made the folder, then failed to
write the file inside it. These fixtures are built so the ORIGINAL file's path
genuinely exceeds 260 characters; a test that stayed under the limit would pass
against the broken code.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vault_manager as vm


def deep_attachment(tmp_path: Path) -> tuple[Path, Path]:
    thread = ("2026-06-10 Commercials - MoE Digital Transformation Program - "
              "Business Processes Re-engineering and Operating Model Design")
    slug = ("2026-06-10 1b006e42-E - Core42 Commercial Proposal to MOE for "
            "Business Process Re-engineering v1.0")
    folder = tmp_path / "Work" / "Threads" / thread / "files" / slug
    note = folder / f"{slug}.md"
    original = folder / ("E - Core42 Commercial Proposal to MOE for Business Process "
                         "Re-engineering and Operating Model v1.0 final.txt")
    assert len(str(original)) > 260, f"fixture is only {len(str(original))} chars -- proves nothing"
    os.makedirs(vm.long_path(folder), exist_ok=True)
    Path(vm.long_path(note)).write_text(
        f'---\ntype: "File"\noriginal_filename: "{original.name}"\n---\n\n'
        "## Summary\n\n\n## Personal Notes\n", encoding="utf-8")
    Path(vm.long_path(original)).write_text("Scope and pricing for the MoE programme.",
                                            encoding="utf-8")
    return note, original


def test_the_selector_finds_a_file_past_max_path(tmp_path):
    """A plain iterdir/is_file silently returns nothing past the limit, which
    would report an attachment that exists as an orphan."""
    import select_files as s
    note, _ = deep_attachment(tmp_path)
    result = s.select(tmp_path)
    assert result["orphans_without_note"] == 0
    assert result["due"] == 1
    assert result["selected"][0]["file_present"] is True
    assert result["selected"][0]["file_note"] == str(note)


def test_the_reader_opens_a_file_past_max_path(tmp_path):
    """Otherwise it says "not in the vault" -- and the summary repeats a
    falsehood about a file that is sitting right there."""
    import read_file as r
    note, _ = deep_attachment(tmp_path)
    out = r.read_file(note)
    assert "Scope and pricing for the MoE programme." in out
    assert "not in the vault" not in out
