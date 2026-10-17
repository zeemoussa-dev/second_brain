"""Capture must write an attachment whose path passes Windows' 260-char MAX_PATH.

It did not: the folder (just under the limit) was created, then writing the
file inside it failed, leaving 256 real attachments as empty folders with no
file and no note -- and no error anyone saw (2026-09-11). The fixture's file
path genuinely exceeds 260 characters, or the test would pass against the bug.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vault_manager as vm
import vault_lib


def test_an_attachment_past_max_path_is_written_file_and_note(tmp_path):
    thread_dir = tmp_path / "Work" / "Threads" / (
        "2026-06-10 Commercials - MoE Digital Transformation Program - "
        "Business Processes Re-engineering and Operating Model Design")
    os.makedirs(vm.long_path(thread_dir), exist_ok=True)
    name = ("E - Core42 Commercial Proposal to MOE for Business Process "
            "Re-engineering and Operating Model v1.0 final.pdf")

    result = vault_lib.write_file_companion(
        tmp_path, subfolder=thread_dir, file_slug="2026-06-10 1b006e42-" + name,
        original_filename=name, content=b"%PDF-1.4 proposal", summary="",
        source_thread="[[thread]]")

    assert len(result["file_path"]) > 260, "fixture must genuinely exceed MAX_PATH"
    assert os.path.isfile(vm.long_path(result["file_path"])), "the attachment itself was lost"
    assert os.path.isfile(vm.long_path(result["companion_path"])), "its note was lost"
    with open(vm.long_path(result["file_path"]), "rb") as handle:
        assert handle.read() == b"%PDF-1.4 proposal"
