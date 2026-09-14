"""Answering a question about the portfolio from the vault, not from memory.

The mistakes worth a test here are the quiet ones: a count that silently
includes an affiliate as if it were its own relationship, a search that
answers "Mubadala?" with one company when the vault holds three, and a brief
built for the wrong company -- which reads exactly like a correct one.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def hub(vault: Path, root: str, name: str, *, parent: str | None = None,
        aliases=(), sector: str = "", domain: str = "", enriched: str = "",
        actions=(), summary: str = "") -> Path:
    base = vault / "Work" / root
    folder = (base / parent / "Affiliates" / name) if parent else (base / name)
    folder.mkdir(parents=True, exist_ok=True)
    alias_line = ("aliases: [" + ", ".join(f'"{a}"' for a in aliases) + "]\n") if aliases else ""
    note = folder / f"{name}.md"
    note.write_text(
        f'---\ntype: "{"Customer" if root == "Customers" else "Partner"}"\nname: "{name}"\n'
        f'affiliate_of: "{parent or ""}"\nsector: "{sector}"\ndomain: "{domain}"\n'
        f'enriched: "{enriched}"\n{alias_line}---\n\n'
        f"## Summary\n\n> [!abstract] {summary}\n\n## Personal Notes\n\nmine\n\n"
        "## Actions\n\n" + "".join(f"{a}\n" for a in actions) + "\n## Related\n",
        encoding="utf-8")
    return note


def history(hub_md: Path, *entries: str) -> None:
    hub_md.parent.joinpath(f"{hub_md.stem}-history.md").write_text(
        f'---\ntype: "History"\nname: "{hub_md.stem} History"\n---\n\n'
        f"# {hub_md.stem}\n\n" + "".join(f"- {e}\n" for e in entries), encoding="utf-8")


def captures(hub_md: Path, notes: str, *entries: str) -> None:
    hub_md.parent.joinpath(f"{hub_md.stem}-captures.md").write_text(
        f'---\ntype: "Captures"\nname: "{hub_md.stem} Captures"\n---\n\n'
        f"# {hub_md.stem}\n\n## Notes\n\n{notes}\n\n## Captured\n\n"
        + "".join(f"- {e}\n" for e in entries), encoding="utf-8")


def person(folder: Path, email: str, name: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    folder.joinpath(f"{email}.md").write_text(
        f'---\ntype: "Person"\nname: "{name}"\nemail: "{email}"\nrole: "CEO"\n---\n\n## Notes\n',
        encoding="utf-8")


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(tmp_path / "config"))
    taqa = hub(tmp_path, "Customers", "TAQA", sector="Energy", domain="taqa.com",
               enriched="2026-09-11", summary="Abu Dhabi's state utility.",
               actions=["- [ ] Send revised pricing", "- [x] Share the DR report"])
    history(taqa, "2026-09-11: Pipeline review", "2026-08-24: Briefing prepared")
    captures(taqa, "my own note about them", "2026-08-18: Renewal may reuse DCT learnings")
    person(taqa.parent / "People", "abid@taqa.com", "Abid Hussain")
    distribution = hub(tmp_path, "Customers", "TAQA Distribution", parent="TAQA",
                       sector="Energy", enriched="2026-09-11")
    history(distribution, "2026-09-08: Proceeding to go-live")
    hub(tmp_path, "Customers", "Mubadala Health", sector="Healthcare")
    hub(tmp_path, "Partners", "Cisco", aliases=["Cisco Systems"], sector="Technology",
        domain="cisco.com")
    hub(tmp_path, "Partners", "Never Engaged Co", sector="Technology")
    (tmp_path / "Work" / "People").mkdir(parents=True, exist_ok=True)
    person(tmp_path / "Work" / "People", "someone@elsewhere.com", "Someone Else")
    return tmp_path


# ── counting ─────────────────────────────────────────────────────────────

def test_an_affiliate_is_never_counted_as_its_own_relationship(vault):
    """TAQA Distribution is a real hub, but "how many customers" does not mean
    "how many hub notes" -- counting it as one would inflate the portfolio."""
    import company_counts as c
    answer, _, _ = c.tally(vault, None)
    assert answer["customer"]["companies"] == 2, "TAQA and Mubadala Health"
    assert answer["customer"]["affiliates"] == 1, "TAQA Distribution"


def test_classified_and_actually_engaged_are_different_numbers(vault):
    import company_counts as c
    answer, _, _ = c.tally(vault, "partner")
    assert answer["partner"]["companies"] == 2
    assert answer["partner"]["engaged"] == 0, "neither partner has a History entry"
    assert answer["totals"]["engaged"] == 0


def test_the_same_sector_written_two_ways_is_one_line_in_the_breakdown(vault):
    """The sector field is free text and hubs disagree about capitals. Two
    entries differing only in a capital letter is noise, not a breakdown."""
    import company_counts as c
    hub(vault, "Partners", "Another Tech Co", sector="technology")
    _, sectors, _ = c.tally(vault, "partner")
    assert sectors["partner"]["Technology"] == 3
    assert "technology" not in sectors["partner"]


def test_the_denominator_for_engaged_and_enriched_is_every_hub(vault):
    import company_counts as c
    answer, _, _ = c.tally(vault, "customer")
    counts = answer["customer"]
    assert counts["hubs"] == counts["companies"] + counts["affiliates"] == 3
    assert counts["enriched"] == 2, "TAQA and its affiliate, not Mubadala Health"


def test_counting_one_kind_leaves_the_other_out(vault):
    import company_counts as c
    answer, sectors, names = c.tally(vault, "customer")
    assert "partner" not in answer
    assert sectors["customer"]["Energy"] == 2
    assert "Cisco" not in names["customer"]


# ── finding ──────────────────────────────────────────────────────────────

def test_a_name_two_companies_share_comes_back_as_both(vault):
    """"Mubadala" is a real company and so is "Mubadala Health". Answering
    with one of them is the mistake; naming both is the answer."""
    import find_company as f
    answer = f.find(vault, "TAQA", None)
    assert answer["status"] == "one" and answer["matches"][0]["name"] == "TAQA"
    partial = f.find(vault, "taqa", None)
    assert partial["matches"][0]["name"] == "TAQA"


def test_an_exact_hit_still_names_the_companies_it_did_not_return(vault):
    """"Mubadala" resolves to Mubadala and stops there -- which would hide
    Mubadala Health from the person who asked. Name the neighbours."""
    import find_company as f
    answer = f.find(vault, "TAQA", None)
    assert answer["matches"][0]["name"] == "TAQA"
    assert answer["others_with_this_in_their_name"] == ["TAQA Distribution"]


def test_a_fragment_finds_every_company_containing_it(vault):
    import find_company as f
    answer = f.find(vault, "mubadala", None)
    assert [m["name"] for m in answer["matches"]] == ["Mubadala Health"]
    fragment = f.find(vault, "distribution", None)
    assert fragment["matches"][0]["matched_on"] == "part of the name"


def test_an_alias_and_a_domain_both_find_the_company(vault):
    import find_company as f
    assert f.find(vault, "Cisco Systems", None)["matches"][0]["name"] == "Cisco"
    assert f.find(vault, "cisco.com", None)["matches"][0]["matched_on"] == "domain"


def test_a_company_we_do_not_have_is_reported_as_none(vault):
    import find_company as f
    answer = f.find(vault, "Acme Widgets", None)
    assert answer["status"] == "none" and answer["matches"] == []


def test_a_result_says_when_we_last_engaged(vault):
    import find_company as f
    match = f.find(vault, "TAQA", None)["matches"][0]
    assert (match["last_engagement"], match["engagements"]) == ("2026-09-11", 2)
    assert match["affiliates"] == ["TAQA Distribution"]


# ── briefing ─────────────────────────────────────────────────────────────

def test_the_brief_gathers_each_part_from_the_note_that_owns_it(vault):
    import company_brief as b
    answer = b.brief(vault, "TAQA", 10, 10)
    assert answer["recent_history"][0] == {"date": "2026-09-11", "what": "Pipeline review"}
    assert answer["captured_facts"][0]["fact"] == "Renewal may reuse DCT learnings"
    assert answer["open_actions"] == ["Send revised pricing"], "a done action is not owed"
    assert answer["people"][0]["name"] == "Abid Hussain"
    assert answer["summary"] == "Abu Dhabi's state utility."


def test_the_brief_never_reports_the_operators_own_notes(vault):
    """`## Notes` is the operator's handwriting. Reporting it back as a vault
    fact would launder his own thinking into something the system 'knows'."""
    import company_brief as b
    answer = b.brief(vault, "TAQA", 10, 10)
    assert all("my own note" not in fact["fact"] for fact in answer["captured_facts"])


def test_a_brief_for_a_parent_never_shows_its_affiliates_engagements(vault):
    import company_brief as b
    answer = b.brief(vault, "TAQA", 10, 10)
    assert all("go-live" not in event["what"] for event in answer["recent_history"])
    assert b.brief(vault, "TAQA Distribution", 10, 10)["parent"] == "TAQA"


def test_a_company_that_does_not_resolve_gets_no_brief(vault):
    import company_brief as b
    answer = b.brief(vault, "Acme Widgets", 10, 10)
    assert answer["status"] == "none" and answer["candidates"] == []


def test_the_brief_says_how_much_it_left_out(vault):
    import company_brief as b
    answer = b.brief(vault, "TAQA", 1, 10)
    assert len(answer["recent_history"]) == 1 and answer["total_engagements"] == 2
