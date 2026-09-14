"""The attachment selector: what is due, what is done, and what cannot be done."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def attachment(vault: Path, thread: str, filename: str, *, summary: str = "",
               with_note: bool = True) -> Path:
    folder = vault / "Work" / "Threads" / thread / "files" / f"{thread[:10]} {filename}"
    folder.mkdir(parents=True)
    (folder / filename).write_bytes(b"data")
    if with_note:
        (folder / f"{folder.name}.md").write_text(
            f'---\ntype: "File"\noriginal_filename: "{filename}"\n---\n\n'
            f"## Summary\n\n{summary}\n\n## Personal Notes\n", encoding="utf-8")
    return folder


def test_an_unsummarized_file_is_due_and_a_summarized_one_is_not(tmp_path):
    import select_files as s
    attachment(tmp_path, "2026-06-01 A", "a.pdf")
    attachment(tmp_path, "2026-06-02 B", "b.pdf", summary="Already read.")
    result = s.select(tmp_path)
    assert result["due"] == 1
    assert result["summarized"] == 1
    assert result["selected"][0]["original_filename"] == "a.pdf"


def test_a_folder_without_a_note_is_counted_not_selected(tmp_path):
    """There is nowhere to write its summary, and every other pass walks notes,
    so without this count these files are simply invisible."""
    import select_files as s
    attachment(tmp_path, "2026-06-01 A", "orphan.pdf", with_note=False)
    result = s.select(tmp_path)
    assert result["orphans_without_note"] == 1
    assert result["due"] == 0


def test_oldest_first_and_the_limit_holds(tmp_path):
    import select_files as s
    for day in ("03", "01", "02"):
        attachment(tmp_path, f"2026-06-{day} T{day}", f"f{day}.pdf")
    result = s.select(tmp_path, limit=2)
    assert [f["thread"] for f in result["selected"]] == ["2026-06-01 T01", "2026-06-02 T02"]
    assert result["due"] == 3
    newest = s.select(tmp_path, limit=1, newest_first=True)
    assert newest["selected"][0]["thread"] == "2026-06-03 T03"


def test_the_output_is_json_serializable(tmp_path):
    import select_files as s
    attachment(tmp_path, "2026-06-01 A", "a.pdf")
    json.dumps(s.select(tmp_path))
