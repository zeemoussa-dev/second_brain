"""Tracing a lost attachment folder back to the message it came from.

The network half is verified live; this pins the half that decides WHAT gets
re-fetched -- a wrong match would re-fetch the wrong message's attachments into
a Thread they never belonged to.
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def thread_with(tmp_path: Path, message_ids: list[str]) -> Path:
    thread = tmp_path / "Work" / "Threads" / "2026-06-10 Deal"
    (thread / "messages").mkdir(parents=True)
    for n, message_id in enumerate(message_ids):
        (thread / "messages" / f"2026-06-10 m{n}.md").write_text(
            f'---\ntype: "RawMessage"\nconversation_id: "conv-1"\n'
            f'message_id: "{message_id}"\nreceived: "2026-06-10 09:39:13.000000+00:00"\n---\n',
            encoding="utf-8")
    return thread


def short_hash(message_id: str) -> str:
    return hashlib.sha256(message_id.encode("utf-8")).hexdigest()[:8]


def test_an_empty_folder_is_traced_to_its_message(tmp_path):
    import recover_lost_attachments as r
    thread = thread_with(tmp_path, ["MSG-A", "MSG-B"])
    (thread / "files" / f"2026-06-10 {short_hash('MSG-B')}-proposal.pdf").mkdir(parents=True)

    traced = r.plan(tmp_path)

    assert traced["empty_folders"] == 1
    assert [m["message_id"] for m in traced["messages"]] == ["MSG-B"]
    assert traced["messages"][0]["conversation_id"] == "conv-1"


def test_two_lost_attachments_of_one_message_are_one_refetch(tmp_path):
    import recover_lost_attachments as r
    thread = thread_with(tmp_path, ["MSG-A"])
    for name in ("a.pdf", "b.xlsx"):
        (thread / "files" / f"2026-06-10 {short_hash('MSG-A')}-{name}").mkdir(parents=True)

    traced = r.plan(tmp_path)

    assert len(traced["messages"]) == 1
    assert len(traced["messages"][0]["lost_folders"]) == 2


def test_a_folder_matching_no_message_is_reported_not_guessed(tmp_path):
    import recover_lost_attachments as r
    thread = thread_with(tmp_path, ["MSG-A"])
    (thread / "files" / "2026-06-10 deadbeef-orphan.pdf").mkdir(parents=True)

    traced = r.plan(tmp_path)

    assert traced["messages"] == []
    assert traced["unmapped"] == ["2026-06-10 Deal/files/2026-06-10 deadbeef-orphan.pdf"]


def test_a_captured_attachment_is_not_a_candidate(tmp_path):
    import recover_lost_attachments as r
    thread = thread_with(tmp_path, ["MSG-A"])
    folder = thread / "files" / f"2026-06-10 {short_hash('MSG-A')}-fine.pdf"
    folder.mkdir(parents=True)
    (folder / f"{folder.name}.md").write_text('---\ntype: "File"\n---\n', encoding="utf-8")

    assert r.plan(tmp_path)["empty_folders"] == 0
