"""The log -> history retrofit reaches every note that can own a log child.

The traversal named `Work/Opportunities` as a top-level root. No such folder
exists -- an Opportunity lives under its Customer -- and the loop read only
each root's DIRECT children, so Affiliates were missed too: 21 of this
vault's 58 `-log.md` notes were covered, and the 26 Opportunity ones had no
route to migration at all. These pin all three shapes.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import migrate_hub_children as mhc  # noqa: E402


def note_folder(folder: Path, name: str, *, note_type: str, with_log: bool = True) -> Path:
    """A note folder in the shape the older template produced: a root note
    indexing a `-log` child under `## Log & Captures`, plus a captures note."""
    folder.mkdir(parents=True)
    (folder / f"{name}.md").write_text(
        f'---\ntype: "{note_type}"\nname: "{name}"\n---\n\n'
        "## Summary\n\nPlaceholder.\n\n## Actions\n\n## Related\n\n"
        f"## Log & Captures\n\n- [[{name}-log|Log]]\n- [[{name}-captures|Captures]]\n",
        encoding="utf-8",
    )
    if with_log:
        (folder / f"{name}-log.md").write_text(
            f'---\ntype: "Log"\nname: "{name} Log"\nparent: "[[{name}]]"\n'
            f'tags: ["kind/log"]\n---\n\n# {name} Log\n\n- 2026-09-01: Something happened\n',
            encoding="utf-8",
        )
    (folder / f"{name}-captures.md").write_text(
        f'---\ntype: "Captures"\nname: "{name} Captures"\n---\n\nSome capture.\n',
        encoding="utf-8",
    )
    return folder


@pytest.fixture()
def vault(tmp_path: Path) -> Path:
    customers = tmp_path / "Work" / "Customers"
    note_folder(customers / "Adnoc", "Adnoc", note_type="Customer")
    note_folder(customers / "Adnoc" / "Opportunities" / "Alarm Management",
                "Alarm Management", note_type="Opportunity")
    note_folder(customers / "Adnoc" / "Affiliates" / "Adnoc Gas",
                "Adnoc Gas", note_type="Customer")
    # Real shapes from the live vault: an Opportunity filed under an
    # AFFILIATE rather than the top-level Customer, and an affiliate of an
    # affiliate (Partners/G42/Affiliates/M42/Affiliates/Diaverum).
    note_folder(customers / "Adnoc" / "Affiliates" / "Adnoc Gas" / "Opportunities" / "Gas Platform",
                "Gas Platform", note_type="Opportunity")
    note_folder(tmp_path / "Work" / "Partners" / "Microsoft", "Microsoft", note_type="Partner")
    note_folder(tmp_path / "Work" / "Partners" / "Microsoft" / "Affiliates" / "LinkedIn"
                / "Affiliates" / "Lynda", "Lynda", note_type="Partner")
    # An archived folder must never be migrated.
    note_folder(customers / "_archive" / "Old Customer", "Old Customer", note_type="Customer")
    return tmp_path


def test_every_shape_is_migrated(vault):
    result = mhc.migrate(vault, dry_run=False)

    # hub, affiliate, opportunity, partner -- the affiliate and the
    # opportunity are the two the old traversal could never reach.
    assert result["log_notes_renamed"] == 6
    assert result["hubs_seen"] == 6
    for path in (
        vault / "Work/Customers/Adnoc/Adnoc-history.md",
        vault / "Work/Customers/Adnoc/Opportunities/Alarm Management/Alarm Management-history.md",
        vault / "Work/Customers/Adnoc/Affiliates/Adnoc Gas/Adnoc Gas-history.md",
        vault / "Work/Partners/Microsoft/Microsoft-history.md",
        vault / "Work/Customers/Adnoc/Affiliates/Adnoc Gas/Opportunities/Gas Platform/Gas Platform-history.md",
        vault / "Work/Partners/Microsoft/Affiliates/LinkedIn/Affiliates/Lynda/Lynda-history.md",
    ):
        assert path.is_file(), f"not migrated: {path}"
        assert not path.with_name(path.name.replace("-history", "-log")).exists()


def test_the_renamed_note_becomes_a_history_note(vault):
    mhc.migrate(vault, dry_run=False)

    text = (vault / "Work/Customers/Adnoc/Opportunities/Alarm Management"
            / "Alarm Management-history.md").read_text(encoding="utf-8")
    assert 'type: "History"' in text
    assert 'name: "Alarm Management History"' in text
    assert '"kind/history"' in text
    assert '"kind/log"' not in text
    # The entries themselves are never rewritten by the rename.
    assert "- 2026-09-01: Something happened" in text


def test_the_root_note_points_at_the_history_child(vault):
    mhc.migrate(vault, dry_run=False)

    text = (vault / "Work/Customers/Adnoc/Opportunities/Alarm Management"
            / "Alarm Management.md").read_text(encoding="utf-8")
    assert "## History & Captures" in text
    assert "## Log & Captures" not in text
    assert "[[Alarm Management-history|History]]" in text
    assert "-log|Log]]" not in text


def test_a_second_run_changes_nothing(vault):
    mhc.migrate(vault, dry_run=False)
    before = {p: p.read_bytes() for p in sorted(vault.rglob("*.md"))}

    again = mhc.migrate(vault, dry_run=False)

    assert again["log_notes_renamed"] == 0
    assert again["sections_renamed"] == 0
    assert again["index_links_repointed"] == 0
    assert {p: p.read_bytes() for p in sorted(vault.rglob("*.md"))} == before


def test_a_dry_run_writes_nothing(vault):
    result = mhc.migrate(vault, dry_run=True)

    assert result["status"] == "dry-run"
    assert result["log_notes_renamed"] == 6
    assert (vault / "Work/Customers/Adnoc/Adnoc-log.md").is_file()
    assert not (vault / "Work/Customers/Adnoc/Adnoc-history.md").exists()


def test_an_opportunitys_captures_note_is_left_alone(vault):
    mhc.migrate(vault, dry_run=False)

    opportunity = (vault / "Work/Customers/Adnoc/Opportunities/Alarm Management"
                   / "Alarm Management-captures.md").read_text(encoding="utf-8")
    hub = (vault / "Work/Customers/Adnoc/Adnoc-captures.md").read_text(encoding="utf-8")
    # Structuring a captures note changes how that note is WRITTEN; it is a
    # hub concern and not part of renaming log to history.
    assert "## Captured" not in opportunity
    assert "## Captured" in hub


def test_an_archived_folder_is_never_migrated(vault):
    mhc.migrate(vault, dry_run=False)

    archived = vault / "Work/Customers/_archive/Old Customer"
    assert (archived / "Old Customer-log.md").is_file()
    assert not (archived / "Old Customer-history.md").exists()


def test_a_folder_without_a_root_note_is_skipped(vault):
    stray = vault / "Work" / "Customers" / "Adnoc" / "Files" / "MACC Estimator"
    stray.mkdir(parents=True)
    (stray / "Some Forecast.md").write_text("---\ntype: \"File\"\n---\n", encoding="utf-8")

    result = mhc.migrate(vault, dry_run=False)

    assert result["hubs_seen"] == 6
