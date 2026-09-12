"""Filing what the CBO said, where a mistake is expensive.

A capture is the operator's own statement of fact. Filed against the wrong
company it is worse than no capture at all, and the two companies most likely
to be confused are a parent and its own affiliate. These pin that, the
provenance that keeps a stated fact separate from a derived one, and the rule
that nothing here ever writes in the operator's own sections.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vault_manager as vm  # noqa: E402


def hub(vault: Path, root: str, name: str, *, parent: str | None = None, aliases=()) -> Path:
    base = vault / "Work" / root
    folder = (base / parent / "Affiliates" / name) if parent else (base / name)
    folder.mkdir(parents=True, exist_ok=True)
    alias_line = ("aliases: [" + ", ".join(f'"{a}"' for a in aliases) + "]\n") if aliases else ""
    note = folder / f"{name}.md"
    note.write_text(
        f'---\ntype: "{"Customer" if root == "Customers" else "Partner"}"\nname: "{name}"\n'
        f'affiliate_of: "{parent or ""}"\n{alias_line}---\n\n'
        "## Summary\n\n## Personal Notes\n\nmy own thinking\n\n## Actions\n\n## Related\n",
        encoding="utf-8")
    return note


def person(folder: Path, email: str, name: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{email}.md"
    path.write_text(f'---\ntype: "Person"\nname: "{name}"\nemail: "{email}"\n'
                    f'role: "CEO"\ntags: ["kind/person"]\n---\n\n## Notes\n', encoding="utf-8")
    return path


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(tmp_path / "config"))
    hub(tmp_path, "Customers", "TAQA")
    hub(tmp_path, "Customers", "TAQA Distribution", parent="TAQA")
    hub(tmp_path, "Partners", "Cisco")
    person(tmp_path / "Work" / "Customers" / "TAQA" / "Affiliates" / "TAQA Distribution" / "People",
           "irfan.siddiqui@taqadistribution.com", "Irfan Siddiqui")
    person(tmp_path / "Work" / "Customers" / "TAQA" / "Affiliates" / "TAQA Distribution" / "People",
           "irfan.khan@taqadistribution.com", "Irfan Khan")
    (tmp_path / "Work" / "People").mkdir(parents=True, exist_ok=True)
    return tmp_path


def capture(**overrides) -> dict:
    base = {"schema_version": 1, "said_at": "2026-09-12", "company": "TAQA Distribution",
            "people": [], "history_line": "Met the CEO; positive; agreed Q1 phasing",
            "important_info": [], "actions": []}
    base.update(overrides)
    return base


def entries(path: Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("- 2")]


# ── resolving ────────────────────────────────────────────────────────────

def test_a_parent_never_resolves_to_its_affiliate(vault):
    import resolve_capture as r
    answer = r.resolve(vault, "TAQA", [])
    assert answer["company"]["status"] == "one"
    assert answer["company"]["matches"][0]["name"] == "TAQA"
    assert answer["company"]["matches"][0]["affiliates"] == ["TAQA Distribution"]


def test_an_unknown_company_is_reported_not_guessed(vault):
    import resolve_capture as r
    answer = r.resolve(vault, "TAQA Water", [])
    assert answer["company"]["status"] == "none"
    assert "TAQA" in answer["company"]["did_you_mean"]


def test_two_people_sharing_a_name_come_back_ambiguous(vault):
    import resolve_capture as r
    answer = r.resolve(vault, "TAQA Distribution", ["Irfan"])
    assert answer["people"][0]["status"] == "ambiguous"
    assert len(answer["people"][0]["matches"]) == 2


def test_an_email_resolves_to_exactly_one_person(vault):
    import resolve_capture as r
    answer = r.resolve(vault, "TAQA Distribution", ["irfan.siddiqui@taqadistribution.com"])
    assert answer["people"][0]["status"] == "one"
    assert answer["people"][0]["matches"][0]["name"] == "Irfan Siddiqui"


def test_a_name_matches_whole_words_not_any_substring(vault):
    """Searching "Mir" returned Emirates and Emirates Skywards -- a substring
    match inside E-mir-ates. Filing against the wrong person is the cost."""
    import resolve_capture as r
    person(vault / "Work" / "People", "do-not-reply@emirates.email", "Emirates")
    person(vault / "Work" / "Customers" / "TAQA" / "Affiliates" / "TAQA Distribution" / "People",
           "dawarali.mir@taqadistribution.com", "Dawar Ali Mir")
    answer = r.resolve(vault, "TAQA Distribution", ["Mir"])
    assert answer["people"][0]["status"] == "one"
    assert answer["people"][0]["matches"][0]["name"] == "Dawar Ali Mir"


def test_a_person_at_an_affiliate_is_found_when_the_parent_is_named(vault):
    """The CBO says "I met Mir at TAQA" while Mir is filed under TAQA
    Distribution. Reporting nobody would be useless; the useful answer names
    the affiliate so the agent can confirm which company this belongs to."""
    import resolve_capture as r
    person(vault / "Work" / "Customers" / "TAQA" / "Affiliates" / "TAQA Distribution" / "People",
           "dawarali.mir@taqadistribution.com", "Dawar Ali Mir")
    answer = r.resolve(vault, "TAQA", ["Mir"])
    assert answer["company"]["matches"][0]["name"] == "TAQA"
    found = answer["people"][0]
    assert found["status"] == "one"
    assert found["matches"][0]["company"] == "TAQA Distribution"
    assert "TAQA Distribution" in found["note"]


# ── applying ─────────────────────────────────────────────────────────────

def test_the_event_lands_in_the_company_history_with_its_source(vault):
    import apply_capture as a
    result = a.apply_capture(vault, capture(people=["irfan.siddiqui@taqadistribution.com"]))
    history = Path(result["hub"]).parent / "TAQA Distribution-history.md"
    assert entries(history) == [
        "- 2026-09-12: Met the CEO; positive; agreed Q1 phasing "
        "(with [[irfan.siddiqui@taqadistribution.com]]) -- CBO capture"]
    assert result["people_linked"] == 1


def test_durable_facts_and_commitments_land_in_their_own_places(vault):
    import apply_capture as a
    result = a.apply_capture(vault, capture(
        important_info=[{"text": "RFP expected next week"}],
        actions=[{"text": "Send revised pricing", "owner": "Sherif", "due": "Friday"}]))
    folder = Path(result["hub"]).parent
    captured = (folder / "TAQA Distribution-captures.md").read_text(encoding="utf-8")
    assert "- 2026-09-12: RFP expected next week -- CBO capture" in captured
    hub_note = (folder / "TAQA Distribution.md").read_text(encoding="utf-8")
    assert "- [ ] Send revised pricing (Sherif — Friday)" in hub_note


def test_the_operators_own_sections_are_never_touched(vault):
    import apply_capture as a
    result = a.apply_capture(vault, capture(important_info=[{"text": "A durable fact"}]))
    folder = Path(result["hub"]).parent
    hub_note = (folder / "TAQA Distribution.md").read_text(encoding="utf-8")
    assert "my own thinking" in hub_note, "Personal Notes must survive untouched"
    captured = (folder / "TAQA Distribution-captures.md").read_text(encoding="utf-8")
    before_captured = captured.split("## Captured")[0]
    assert "A durable fact" not in before_captured, "nothing may land above ## Captured"


def test_applying_the_same_capture_twice_writes_once(vault):
    import apply_capture as a
    payload = capture(important_info=[{"text": "RFP expected next week"}],
                      actions=[{"text": "Send revised pricing"}])
    first = a.apply_capture(vault, payload)
    second = a.apply_capture(vault, payload)
    assert (first["history_written"], first["captures_written"], first["actions_written"]) == (True, 1, 1)
    assert (second["history_written"], second["captures_written"], second["actions_written"]) == (False, 0, 0)
    history = Path(first["hub"]).parent / "TAQA Distribution-history.md"
    assert len(entries(history)) == 1


def test_a_company_that_does_not_resolve_is_refused_with_its_candidates(vault):
    import apply_capture as a
    with pytest.raises(SystemExit) as refused:
        a.apply_capture(vault, capture(company="TAQA Water"))
    assert "did not resolve" in str(refused.value)


def test_a_dry_run_writes_nothing(vault):
    import apply_capture as a
    result = a.apply_capture(vault, capture(important_info=[{"text": "x"}]), dry_run=True)
    assert result["history_written"] and result["captures_written"] == 1
    assert not (Path(result["hub"]).parent / "TAQA Distribution-history.md").exists()


def test_a_wrong_schema_version_is_refused(vault):
    import apply_capture as a
    with pytest.raises(SystemExit, match="schema_version"):
        a.apply_capture(vault, capture(schema_version=2))


def test_a_person_with_no_note_is_reported_never_created(vault):
    import apply_capture as a
    result = a.apply_capture(vault, capture(people=["Someone Unknown"]))
    assert result["people_not_in_vault"] == ["Someone Unknown"]
    assert result["people_linked"] == 0
