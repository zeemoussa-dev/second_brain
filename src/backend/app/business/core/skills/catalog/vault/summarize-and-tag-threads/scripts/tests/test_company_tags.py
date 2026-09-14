"""Enrichment reads and saves; the Tagging pipeline tags.

Two pipelines (operator, 2026-09-11: "Enrich is different from Tagging, 2
Pipelines now"). These pin the boundary -- the enrichment applier writes no
company tag -- and the Tagging content step that tags from the saved
extraction: by name, by alias, Affiliates included, never an Opportunity, and
idempotently.
"""
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


def test_enrichment_writes_no_company_tag(vault):
    """The boundary itself: Enrichment reads and saves; Tagging tags."""
    import apply_thread_extract as a
    vault_path, note = vault
    result = a.apply_extract(vault_path, extraction(["ADCB", "G42"]))
    assert vm.read_note(note)[0]["tags"] == ["kind/thread"]
    assert "company_tags_added" not in result
    assert Path(result["extraction_saved_to"]).is_file(), "the read is saved for Tagging"


def test_an_unknown_name_is_still_filed_for_review(vault):
    import apply_thread_extract as a
    vault_path, _ = vault
    result = a.apply_extract(vault_path, extraction(["Nowhere Holdings"]))
    assert result.get("unknown_companies") == ["Nowhere Holdings"]


def test_tagging_tags_from_the_saved_read_by_name_alias_and_affiliate(vault):
    import apply_thread_extract as a
    import retag_threads_from_extracts as r
    vault_path, note = vault
    a.apply_extract(vault_path, extraction(["ADCB", "Khazna", "G42", "Nowhere Holdings"]))

    result = r.run(vault_path)

    tags = vm.read_note(note)[0]["tags"]
    assert "customer/abu-dhabi-commercial-bank" in tags, "resolved by its alias"
    assert "partner/khazna-data-centres" in tags, "an Affiliate resolves too"
    assert "partner/g42" in tags
    assert "kind/thread" in tags, "existing tags survive"
    assert result["tags_added"] == 3 and result["names_still_unresolved"] == 1


def test_an_opportunity_is_never_tagged_as_a_company(vault):
    import apply_thread_extract as a
    import retag_threads_from_extracts as r
    vault_path, note = vault
    a.apply_extract(vault_path, extraction(["Pilot Deal"]))
    r.run(vault_path)
    assert not any("pilot-deal" in t for t in vm.read_note(note)[0]["tags"])


def test_tagging_is_idempotent(vault):
    import apply_thread_extract as a
    import retag_threads_from_extracts as r
    vault_path, note = vault
    a.persist(extraction(["ADCB"]), "conv-1")
    first, second = r.run(vault_path), r.run(vault_path)
    assert first["tags_added"] == 1 and second["tags_added"] == 0


def test_a_dry_run_changes_nothing(vault):
    import apply_thread_extract as a
    import retag_threads_from_extracts as r
    vault_path, note = vault
    a.persist(extraction(["ADCB"]), "conv-1")
    assert r.run(vault_path, dry_run=True)["tags_added"] == 1
    assert vm.read_note(note)[0]["tags"] == ["kind/thread"]
