"""Thread enrichment tags every company it names that resolves to a hub.

It did not: the extraction applier fed named companies only to the review list,
so a Thread was tagged by participant domain alone -- an internal thread about
five customer accounts carried none of them. And a company named before its
alias existed could never resolve later. Both are pinned here, plus the
backfill that re-applies from the saved extractions without a model.
"""
import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vault_manager as vm

_THREAD_TEMPLATE = (Path(__file__).resolve().parents[6]
                    / "templates" / "masters" / "thread" / "Template.json")


def hub(vault: Path, root: str, name: str, *, aliases=(), kind_type=None, parent=None) -> Path:
    base = vault / "Work" / root
    folder = (base / parent / "Affiliates" / name) if parent else (base / name)
    folder.mkdir(parents=True)
    note_type = kind_type or ("Customer" if root == "Customers" else "Partner")
    alias_line = ("aliases: [" + ", ".join(f'"{a}"' for a in aliases) + "]\n") if aliases else ""
    (folder / f"{name}.md").write_text(
        f'---\ntype: "{note_type}"\nname: "{name}"\n{alias_line}---\n\n## Summary\n',
        encoding="utf-8")
    return folder


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(tmp_path / "config"))
    templates = tmp_path / "config" / "data" / "Templates" / "thread"
    templates.mkdir(parents=True)
    shutil.copy(_THREAD_TEMPLATE, templates / "Template.json")
    (tmp_path / "Work" / "People").mkdir(parents=True)
    hub(tmp_path, "Customers", "Abu Dhabi Commercial Bank", aliases=["ADCB"])
    hub(tmp_path, "Partners", "G42")
    hub(tmp_path, "Partners", "Khazna Data Centres", aliases=["Khazna"], parent="G42")
    # Same own-folder shape as a hub, but an Opportunity -- never a company.
    hub(tmp_path, "Customers", "Pilot Deal", kind_type="Opportunity")
    thread_dir = tmp_path / "Work" / "Threads" / "2026-09-10 Example"
    (thread_dir / "messages").mkdir(parents=True)
    note = thread_dir / "2026-09-10 Example.md"
    note.write_text('---\ntype: "Thread"\nid: "conv-1"\ntags: ["kind/thread"]\n---\n\n'
                    "## Summary\n\n\n## Personal Notes\n\n\n## Actions\n\n\n"
                    "## Conversation\n\n\n## Related\n\n\n## Files\n\n", encoding="utf-8")
    return tmp_path, note


def extraction(companies):
    return {"schema_version": 1, "thread_path": "Work/Threads/2026-09-10 Example/2026-09-10 Example.md",
            "summary": "Discussed the facility.", "companies": companies,
            "people": [], "actions": [], "important_info": []}


def test_named_companies_are_tagged_by_name_and_alias(vault):
    import apply_thread_extract as a
    vault_path, note = vault
    result = a.apply_extract(vault_path, extraction(["ADCB", "Khazna", "G42"]))
    tags = vm.read_note(note)[0]["tags"]
    assert "customer/abu-dhabi-commercial-bank" in tags
    assert "partner/khazna-data-centres" in tags, "an Affiliate resolves too"
    assert "partner/g42" in tags
    assert "kind/thread" in tags, "existing tags survive"
    assert sorted(result["company_tags_added"]) == sorted(
        ["customer/abu-dhabi-commercial-bank", "partner/g42", "partner/khazna-data-centres"])


def test_an_unknown_name_is_still_filed_for_review_not_tagged(vault):
    import apply_thread_extract as a
    vault_path, note = vault
    result = a.apply_extract(vault_path, extraction(["Nowhere Holdings"]))
    assert result.get("unknown_companies") == ["Nowhere Holdings"]
    assert vm.read_note(note)[0]["tags"] == ["kind/thread"]


def test_an_opportunity_is_never_tagged_as_a_company(vault):
    import apply_thread_extract as a
    vault_path, note = vault
    a.apply_extract(vault_path, extraction(["Pilot Deal"]))
    assert not any("pilot-deal" in t for t in vm.read_note(note)[0]["tags"])


def test_the_backfill_reapplies_from_saved_extractions_idempotently(vault):
    """A saved extraction naming a company that had no alias when it was read
    resolves now -- without the model reading the Thread again."""
    import apply_thread_extract as a
    import retag_threads_from_extracts as r
    vault_path, note = vault
    a.persist(extraction(["ADCB"]), "conv-1")        # as saved before tagging existed

    first = r.run(vault_path)
    second = r.run(vault_path)

    assert "customer/abu-dhabi-commercial-bank" in vm.read_note(note)[0]["tags"]
    assert first["threads_tagged"] == 1 and first["tags_added"] == 1
    assert second["tags_added"] == 0, "a second run must add nothing"


def test_a_dry_run_changes_nothing(vault):
    import apply_thread_extract as a
    import retag_threads_from_extracts as r
    vault_path, note = vault
    a.persist(extraction(["ADCB"]), "conv-1")
    result = r.run(vault_path, dry_run=True)
    assert result["tags_added"] == 1
    assert vm.read_note(note)[0]["tags"] == ["kind/thread"]
