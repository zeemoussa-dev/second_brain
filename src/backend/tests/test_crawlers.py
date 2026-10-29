"""What a crawler is, read and labelled (`REQ-SB-102`; operator,
2026-10-24: "I need to see what's inside, a quick visual of the steps,
a friendly name, a tag, and when they run and the next run").

The measurement these tests exist to protect, taken on the operator's
own install before any of this was designed:

    12 cron jobs
     6 run a SCRIPT and carry no prompt at all
     5 carry a one-sentence prompt
     1 spells its work out as numbered steps

So "show the steps" would have shown nothing for eleven of twelve, and
"show the prompt" nothing for six. `definition_of` is what keeps the
screen honest about which shape each job actually has.
"""
import pytest

from app.business.hermes import crawlers


def test_numbered_steps_are_read_in_the_order_written() -> None:
    """[REQ-SB-102] The one job that does spell its work out."""
    prompt = (
        "Follow its three-step loop and nothing else:\n\n"
        "1. Ask which Threads are due:\n"
        "   python select_threads.py --limit 25\n"
        "   Take the batch exactly as returned.\n\n"
        "2. For each Thread in the batch, read it\n\n"
        "3. Write the summary back\n"
    )

    steps = crawlers.steps_in(prompt)

    assert [step["number"] for step in steps] == ["1", "2", "3"]
    assert steps[0]["says"] == "Ask which Threads are due:"
    assert steps[2]["says"] == "Write the summary back"


def test_a_prompt_with_no_numbered_steps_yields_none_rather_than_guessing() -> None:
    """[REQ-SB-102] Eleven of twelve jobs land here. Returning `[]` is
    what lets the view say what the job IS instead of drawing an empty
    chain, which would read as "this job has no steps"."""
    assert crawlers.steps_in(
        "Rebuild the vault structural index for agent lookups",
    ) == []
    assert crawlers.steps_in("") == []


def test_numbers_are_taken_as_written_and_never_renumbered() -> None:
    """[REQ-SB-102] A prompt that jumps from 2 to 4 is shown as it is:
    renumbering here would hide an edit someone made badly, which is
    exactly the thing a reader is looking for."""
    steps = crawlers.steps_in("1. first\n2. second\n4. fourth\n")

    assert [step["number"] for step in steps] == ["1", "2", "4"]


def test_a_script_job_says_what_it_runs_even_with_no_prompt() -> None:
    """[REQ-SB-102] Six jobs on the operator's install are this shape,
    and before this they showed nothing at all -- which is what "I need
    to see what's inside" was about. `script` is not in the Hermes
    client's dataclass, so it is read from Hermes' own jobs.json."""
    definition = crawlers.definition_of(
        {"prompt": "", "skill": ""}, {"script": "index_adnoc.py", "no_agent": True},
    )

    assert definition["kind"] == "script"
    assert definition["runs"] == "index_adnoc.py"


def test_a_script_beats_a_prompt_when_a_job_has_both() -> None:
    """[REQ-SB-102] `no_agent` jobs run the script; a prompt sitting
    beside it is not what happens, and showing it as the definition
    would describe work that never runs."""
    definition = crawlers.definition_of(
        {"prompt": "1. this does not run\n", "skill": ""},
        {"script": "personal_sync_runner.py"},
    )

    assert definition["kind"] == "script"
    assert definition["runs"] == "personal_sync_runner.py"


def test_the_plural_skills_fill_in_where_the_singular_one_is_empty() -> None:
    """[REQ-SB-102] The client exposes `skill` (singular) and it is
    empty on jobs that declare `skills` in the file. Reading only the
    singular left real jobs looking like they ran nothing."""
    definition = crawlers.definition_of(
        {"prompt": "do the thing", "skill": ""}, {"skills": ["new-company-discovery"]},
    )

    assert definition["runs"] == "new-company-discovery"
    assert definition["skills"] == ["new-company-discovery"]


def test_a_job_with_nothing_readable_says_so_rather_than_looking_empty() -> None:
    """[REQ-SB-102] A job that runs every hour while this app can see
    no definition is a gap in what we read, not an empty job, and the
    view needs to be able to say which."""
    definition = crawlers.definition_of({"prompt": "", "skill": ""}, {})

    assert definition["kind"] == "unknown"
    assert definition["steps"] == []


# ---------------------------------------------------------------- labels


@pytest.fixture
def annotations(tmp_path, monkeypatch):
    store = tmp_path / "crawler-annotations.json"
    monkeypatch.setattr(
        "app.data_access.crawler_annotations.crawler_annotations_path", lambda: store,
    )
    return store


def test_a_name_and_tags_are_stored_against_the_job_id(annotations) -> None:
    """[REQ-SB-102] Keyed by id, not by Hermes' name: a name can be
    edited in Hermes and an id cannot, so keying on the name would
    orphan the label the first time somebody renamed a job there."""
    saved = crawlers.set_annotation("dd61ce1c8065", "ADNOC index", ["indexes"])

    assert saved == {"friendly_name": "ADNOC index", "tags": ["indexes"]}
    from app.data_access import crawler_annotations as data
    assert data.read_all() == {"dd61ce1c8065": {"friendly_name": "ADNOC index", "tags": ["indexes"]}}


def test_tags_are_trimmed_and_de_duplicated_in_the_order_given(annotations) -> None:
    """[REQ-SB-102] No tag vocabulary is invented -- the operator's
    grouping is theirs -- but the same tag twice is noise."""
    saved = crawlers.set_annotation("a-job", "", [" indexes ", "indexes", "nightly", ""])

    assert saved["tags"] == ["indexes", "nightly"]


def test_clearing_both_removes_the_row_rather_than_storing_an_empty_one(annotations) -> None:
    """[REQ-SB-102] The file stays a list of what was actually
    labelled, so a job with no label leaves no trace to puzzle over."""
    crawlers.set_annotation("a-job", "Something", ["indexes"])

    crawlers.set_annotation("a-job", "  ", [])

    from app.data_access import crawler_annotations as data
    assert data.read_all() == {}


def test_one_crawlers_label_never_disturbs_anothers(annotations) -> None:
    """[REQ-SB-102] Labels are written as a whole file, so this is the
    property that keeps that safe."""
    crawlers.set_annotation("first", "First", ["indexes"])
    crawlers.set_annotation("second", "Second", ["nightly"])

    crawlers.set_annotation("first", "First renamed", ["indexes"])

    from app.data_access import crawler_annotations as data
    everything = data.read_all()
    assert everything["first"]["friendly_name"] == "First renamed"
    assert everything["second"] == {"friendly_name": "Second", "tags": ["nightly"]}


def test_an_absent_annotations_file_is_a_normal_install(annotations) -> None:
    """[REQ-SB-102] Nothing labelled yet is the starting state of every
    install, and must not read as an error -- every crawler still shows
    under Hermes' own name."""
    from app.data_access import crawler_annotations as data

    assert not annotations.exists()
    assert data.read_all() == {}
