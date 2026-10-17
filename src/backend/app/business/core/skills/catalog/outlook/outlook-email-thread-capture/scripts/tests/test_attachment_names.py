"""Attachment names that real mail actually carries.

37 attachments stayed lost even after the MAX_PATH fix, for two reasons found in
the real failures: attached emails are named after their subject, which carries
`:` and `|`; and a slug cut at 80 characters could end on a space, which the
literal long-path form keeps while the plain API had silently dropped it.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vault_manager as vm
import vault_lib


def test_an_attached_email_named_after_its_subject_is_written(tmp_path):
    thread_dir = tmp_path / "Work" / "Threads" / "2026-06-17 To Send"
    thread_dir.mkdir(parents=True)
    raw = "To Send | Fw: Alignment & Immediate Next Steps - Nvidia & Core42"

    result = vault_lib.write_file_companion(
        tmp_path, subfolder=thread_dir, file_slug="2026-06-17 b70cafd8-" + raw,
        original_filename=raw, content=b"MIME-Version: 1.0", summary="")

    on_disk = Path(result["file_path"]).name
    assert os.path.isfile(vm.long_path(result["file_path"])), "the attachment was lost"
    assert ":" not in on_disk and "|" not in on_disk
    frontmatter, _ = vm.read_note(Path(result["companion_path"]))
    assert frontmatter["original_filename"] == raw, "the real name must survive in the note"


def test_a_slug_cut_on_a_space_does_not_end_in_one():
    # The 80th character of this real attachment's slug is a space.
    text = ("2026-06-10 8020be1d-FW- Invitation to visit Supermicro Headquarter - "
            "Ms. Maiyas Al Hammadi")
    assert text[:80].endswith(" "), "fixture must actually cut on a space"
    slug = vault_lib._slugify(text)
    assert not slug.endswith((" ", "."))
    assert len(slug) <= 80


def test_a_very_long_name_is_capped_and_keeps_its_extension():
    name = "RE- [WARNING - MESSAGE ENCRYPTED]" * 12 + ".pdf"
    disk = vault_lib._disk_name(name)
    assert len(disk) <= 180
    assert disk.endswith(".pdf")


def test_an_ordinary_name_is_unchanged():
    """Attachments already on disk must still be found by a re-capture."""
    assert vault_lib._disk_name("2027 capacity needs.pptx") == "2027 capacity needs.pptx"
