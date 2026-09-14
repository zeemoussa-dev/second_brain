"""Names read inside a thread reach the file the operator curates.

The mistakes that matter: offering a name he has already filed under a
different spelling, and adding a row that creates something. His standing rule
is that the default is ignore and nothing is created until he marks it, so
every row this writes has to be inert on its own.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def entities_file(settings: Path, *rows: str) -> Path:
    path = settings / "Entities.md"
    path.write_text("# Entities\n\n## Companies\n\n" + "".join(rows) + "## Partners\n\n",
                    encoding="utf-8")
    return path


def row(name: str, *, aliases: str = "", domain: str = "") -> str:
    return (f"### {name}\n\n\tCompany Name: {name}\n\n\tAliases: {aliases}\n\n"
            f"\tAffiliate of: \n\n\tCreated: Yes\n\n\tIgnore: No\n\n"
            f"\tDomain: {domain}\n\n\tDeleted: No\n\n\n")


def unknowns(data_root: Path, names: dict) -> None:
    """Written where the tagging pass really writes it -- `<data root>/data/`.
    A fixture that puts it beside Settings/ instead passes happily while the
    real run reads an empty file and reports nothing to do."""
    folder = data_root / "data"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "UnknownCompanies.json").write_text(json.dumps(names), encoding="utf-8")


@pytest.fixture()
def setup(tmp_path, monkeypatch):
    data_root = tmp_path / "config"
    settings = data_root / "Settings"
    settings.mkdir(parents=True)
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(data_root))
    return tmp_path, data_root, settings


def test_a_mentioned_name_becomes_a_row_that_creates_nothing(setup):
    """His rule: default is ignore, nothing added until he marks it. A row that
    arrives as Ignore: No would create a hub on the next pass."""
    import find_mentioned_entities as m
    vault, data_root, settings = setup
    path = entities_file(settings, row("TAQA", domain="taqa.com"))
    unknowns(data_root, {"Kyndryl": {"seen": 2, "threads": [{"name": "DD/Kyndryl"}]}})

    result = m.surface(vault, path, min_mentions=1, dry_run=False)

    assert result["added"] == 1
    written = {e["heading"]: e["fields"] for e in m.parse_entities(path.read_text(encoding="utf-8"))}
    assert written["Kyndryl"]["Ignore"] == "Yes"
    assert written["Kyndryl"]["Created"] == "No"
    assert written["Kyndryl"]["Domain"] == "", "a mentioned name has no domain -- that is the marker"


def test_a_name_already_filed_under_another_spelling_is_not_offered_again(setup):
    """"LIMAD" is the operator's own "L'IMAD". Offering it again is asking him
    to make the same decision twice."""
    import find_mentioned_entities as m
    vault, data_root, settings = setup
    path = entities_file(settings, row("L'IMAD", aliases="L'IMAD Group, ADQ"))
    unknowns(data_root, {"LIMAD": {"seen": 3, "threads": []},
                         "ADQ": {"seen": 5, "threads": []},
                         "Mubadala Health LLC": {"seen": 1, "threads": []}})

    result = m.surface(vault, path, min_mentions=1, dry_run=False)

    assert [n for n in result["names"]] == ["Mubadala Health LLC"]
    assert result["already_tracked"] == 2


def test_a_domain_merged_into_aliases_is_not_mistaken_for_a_spelling(setup):
    """Aliases doubles as where a second domain gets merged in. A company
    genuinely named after its domain must still be offered."""
    import find_mentioned_entities as m
    vault, data_root, settings = setup
    path = entities_file(settings, row("Microsoft", aliases="techsupport.microsoft.com"))
    unknowns(data_root, {"Kyndryl": {"seen": 1, "threads": []}})

    assert m.surface(vault, path, min_mentions=1, dry_run=False)["added"] == 1


def test_the_most_mentioned_names_come_first(setup):
    import find_mentioned_entities as m
    vault, data_root, settings = setup
    path = entities_file(settings)
    unknowns(data_root, {"Once": {"seen": 1, "threads": []},
                         "Often": {"seen": 9, "threads": []},
                         "Twice": {"seen": 2, "threads": []}})

    assert m.surface(vault, path, min_mentions=1, dry_run=False)["names"] == \
        ["Often", "Twice", "Once"]


def test_min_mentions_leaves_the_long_tail_out_of_the_file_but_not_the_report(setup):
    """The threshold decides how many rows he hand-curates, never how much he
    is allowed to see -- a name held back is still evidence he may want."""
    import find_mentioned_entities as m
    vault, data_root, settings = setup
    path = entities_file(settings)
    unknowns(data_root, {"Once": {"seen": 1, "threads": []}, "Often": {"seen": 9, "threads": []}})

    result = m.surface(vault, path, min_mentions=2, dry_run=False)

    assert (result["names"], result["held_back"]) == (["Often"], 1)
    assert "Once" not in {e["heading"] for e in m.parse_entities(path.read_text(encoding="utf-8"))}
    report = (settings / "Unclassified-Companies.md").read_text(encoding="utf-8")
    assert "### Once" in report and "Not added -- 1 seen fewer than 2 times" in report


def test_existing_curation_survives_untouched(setup):
    """Entities.md is hand-curated. Appending must not disturb a single field
    of what is already there."""
    import find_mentioned_entities as m
    vault, data_root, settings = setup
    path = entities_file(settings, row("TAQA", aliases="TAQA PJSC", domain="taqa.com"))
    before = m.parse_entities(path.read_text(encoding="utf-8"))
    unknowns(data_root, {"Kyndryl": {"seen": 1, "threads": []}})

    m.surface(vault, path, min_mentions=1, dry_run=False)

    after = m.parse_entities(path.read_text(encoding="utf-8"))
    assert after[:len(before)] == before


def test_a_dry_run_writes_neither_file(setup):
    import find_mentioned_entities as m
    vault, data_root, settings = setup
    path = entities_file(settings)
    original = path.read_text(encoding="utf-8")
    unknowns(data_root, {"Kyndryl": {"seen": 1, "threads": []}})

    result = m.surface(vault, path, min_mentions=1, dry_run=True)

    assert result["added"] == 1
    assert path.read_text(encoding="utf-8") == original
    assert not (settings / "Unclassified-Companies.md").exists()


def test_the_report_carries_the_evidence_a_decision_needs(setup):
    """A bare name cannot be judged. The thread it appeared in can."""
    import find_mentioned_entities as m
    vault, data_root, settings = setup
    path = entities_file(settings)
    unknowns(data_root, {"Kyndryl": {"seen": 2, "threads": [
        {"name": "DD/Kyndryl Modernization"}, {"name": "Kyndryl intro"}]}})

    m.surface(vault, path, min_mentions=1, dry_run=False)

    report = (settings / "Unclassified-Companies.md").read_text(encoding="utf-8")
    assert "### Kyndryl" in report
    assert "DD/Kyndryl Modernization" in report
    assert "Seen 2 times across 2 threads" in report


def test_nothing_to_add_leaves_the_file_byte_identical(setup):
    import find_mentioned_entities as m
    vault, data_root, settings = setup
    path = entities_file(settings, row("TAQA", domain="taqa.com"))
    original = path.read_text(encoding="utf-8")
    unknowns(data_root, {"TAQA": {"seen": 4, "threads": []}})

    result = m.surface(vault, path, min_mentions=1, dry_run=False)

    assert result["added"] == 0
    assert path.read_text(encoding="utf-8") == original, "no spurious diff on a quiet run"


def test_a_missing_unknowns_file_is_not_an_error(setup):
    import find_mentioned_entities as m
    vault, _data_root, settings = setup
    path = entities_file(settings)
    assert m.surface(vault, path, min_mentions=1, dry_run=False)["added"] == 0
