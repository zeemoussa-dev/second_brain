"""A Person note another process has open must be skipped, never fatal.

The first live run died on one file capture had open (WinError 32 -- on
Windows a rename fails while any process holds the file) and left every
remaining person unfiled.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from test_people_pipeline import flat, hub, person, vault  # noqa: F401  (fixture)


def test_a_busy_note_is_skipped_and_the_rest_are_filed(vault, monkeypatch):
    import people_pipeline as p
    acme = hub(vault, "partner", "Acme", "acme.com")
    for name in ("amy", "bob", "cat"):
        person(flat(vault), f"{name}@acme.com")
    real_replace = p.os.replace

    def replace(src, dst):
        if "bob@acme.com" in str(src):
            raise PermissionError(32, "being used by another process")
        return real_replace(src, dst)

    monkeypatch.setattr(p.os, "replace", replace)
    result = p.run(vault)

    assert result["busy_skipped"] == 1 and result["busy_sample"] == ["bob@acme.com.md"]
    assert result["moved_into_hubs"] == 2
    assert (acme / "People" / "amy@acme.com.md").is_file()
    assert (acme / "People" / "cat@acme.com.md").is_file()
    assert (flat(vault) / "bob@acme.com.md").is_file(), "the busy one waits for the next run"


def test_an_interrupted_merge_does_not_log_the_same_change_twice(vault, monkeypatch):
    """Logging succeeded, deleting the duplicate did not: the retry must not
    append the same History entry again."""
    import people_pipeline as p
    acme = hub(vault, "partner", "Acme", "acme.com")
    filed = person(acme / "People", "jane@acme.com", "**Partner:** [[Acme]]", role="Director")
    person(flat(vault), "jane@acme.com", role="VP")
    real_remove = p.os.remove
    monkeypatch.setattr(p.os, "remove",
                        lambda path: (_ for _ in ()).throw(PermissionError(32, "busy")))
    first = p.run(vault)
    assert first["busy_skipped"] == 1

    monkeypatch.setattr(p.os, "remove", real_remove)
    p.run(vault)

    history = filed.read_text(encoding="utf-8").split("## History", 1)[1]
    assert history.count('"Director" → "VP"') == 1
    assert not (flat(vault) / "jane@acme.com.md").exists()
