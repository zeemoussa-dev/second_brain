"""Re-tagging attachments from the companies their summaries wiki-link."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vault_manager as vm


def hub(vault: Path, root: str, name: str, *, aliases=(), note_type=None) -> None:
    folder = vault / "Work" / root / name
    folder.mkdir(parents=True)
    alias_line = ("aliases: [" + ", ".join(f'"{a}"' for a in aliases) + "]\n") if aliases else ""
    kind = note_type or ("Customer" if root == "Customers" else "Partner")
    (folder / f"{name}.md").write_text(f'---\ntype: "{kind}"\nname: "{name}"\n{alias_line}---\n',
                                       encoding="utf-8")


def attachment(vault: Path, summary: str) -> Path:
    folder = vault / "Work" / "Threads" / "2026-06-08 Board" / "files" / "2026-06-08 abcd-deck.pdf"
    folder.mkdir(parents=True)
    (folder / "deck.pdf").write_bytes(b"%PDF")
    note = folder / "2026-06-08 abcd-deck.pdf.md"
    note.write_text('---\ntype: "File"\ntags: ["kind/attachment"]\n---\n\n'
                    f"## Summary\n\n{summary}\n\n## Personal Notes\n", encoding="utf-8")
    return note


def test_a_company_linked_by_its_alias_is_tagged(tmp_path):
    import retag_files_from_summaries as r
    hub(tmp_path, "Customers", "Abu Dhabi Commercial Bank", aliases=["ADCB"])
    note = attachment(tmp_path, "Financing ask of $800m from [[ADCB]] and [[Nobody Ltd]].")

    first = r.run(tmp_path)
    second = r.run(tmp_path)

    tags = vm.read_note(note)[0]["tags"]
    assert "customer/abu-dhabi-commercial-bank" in tags
    assert "kind/attachment" in tags
    assert first["tags_added"] == 1 and second["tags_added"] == 0


def test_a_piped_link_resolves_by_its_target(tmp_path):
    import retag_files_from_summaries as r
    hub(tmp_path, "Partners", "G42")
    note = attachment(tmp_path, "Delivered with [[G42|the group]].")
    r.run(tmp_path)
    assert "partner/g42" in vm.read_note(note)[0]["tags"]


def test_an_opportunity_link_is_not_a_company(tmp_path):
    import retag_files_from_summaries as r
    hub(tmp_path, "Customers", "Pilot Deal", note_type="Opportunity")
    note = attachment(tmp_path, "Pricing for [[Pilot Deal]].")
    r.run(tmp_path)
    assert vm.read_note(note)[0]["tags"] == ["kind/attachment"]


def test_a_dry_run_changes_nothing(tmp_path):
    import retag_files_from_summaries as r
    hub(tmp_path, "Partners", "G42")
    note = attachment(tmp_path, "With [[G42]].")
    assert r.run(tmp_path, dry_run=True)["tags_added"] == 1
    assert vm.read_note(note)[0]["tags"] == ["kind/attachment"]
