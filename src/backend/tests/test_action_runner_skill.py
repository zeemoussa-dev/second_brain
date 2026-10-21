"""The shipped runner Skill, the honest refusal end to end, and the
recorded unmet request (REQ-SB-95-US-03-T05, `ADR-033`).

The runner is **payload** -- `catalog/actions/call-action/scripts/
call_action.py`, stdlib-only, deployed into a Hermes profile and never
imported by the app (`ADR-019`). So it is loaded here BY PATH, the way
`test_plugin_host.py` already loads a bundled script, and driven through
its real `main()` with real command lines.

**It is pointed at the real app through a loopback-shaped transport.**
`urllib.request.urlopen` is replaced by one that takes the very
`Request` object the runner built, asserts it is the POST the catalogue
block tells agents to make, and hands it to `TestClient` -- which is
`httpx.ASGITransport(app=app)`, in process. So the gate, the dispatch
and the ledger are the real ones, no socket is opened, and nothing here
can reach the operator's backend on :8001 even if it is running. A
refusal arrives as a real `urllib.error.HTTPError`, body and all,
exactly as it would over a wire.

**What is isolated, and nothing else:**

- the Action store, in memory, so no test touches
  `<DATA_PATH>/data/Actions/`;
- the Action-call ledger's own root, onto `tmp_path`, so the REAL
  writer runs and the recorded row is asserted against a real file;
- the three resolution sources, because what is deployed, routed and
  registered on this machine is instance state;
- `HERMES_PROFILE_ID`, deleted, so a machine that happens to set it
  cannot make the "it refuses to guess its own id" test pass for the
  wrong reason.

**The one subprocess in this file is deliberate and is the point.** A
`skill` Action is AUTHORISED by the app and performed by the runner
(`ADR-019`), so the grant test builds a throwaway Hermes profile under
`tmp_path`, copies the shipped runner into it in the flat shape a deploy
really writes, and lets it run a one-line Skill that lives in the same
throwaway tree. Nothing it runs is the operator's.
"""
import importlib.util
import io
import json
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main_app
from app.business.core.actions import shipped_starters
from app.business.core.actions.action import UI_FEATURE_KEYS
from app.business.core.actions.action_manager import ActionManager
from app.data_access import action_calls as action_calls_data

client = TestClient(main_app.app)

RUNNER_SOURCE = (
    Path(main_app.__file__).resolve().parent
    / "business" / "core" / "skills" / "catalog" / "actions" / "call-action"
    / "scripts" / "call_action.py"
)

THE_CALLER = "cbo-agent"
A_DEPLOYED_SKILL = "capture-the-thread"
A_REAL_FEATURE_KEY = "/settings/actions"
THE_BASE_URL = "http://127.0.0.1:8001"

THE_UNMET_REQUEST_STARTER = "report-unmet-request"


def load_runner(path: Path, module_name: str):
    """The payload script as a module, loaded from wherever it really
    sits -- which matters, because the runner reads its own deployed
    path to learn which profile it is running as."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def runner(monkeypatch):
    monkeypatch.delenv("HERMES_PROFILE_ID", raising=False)
    return load_runner(RUNNER_SOURCE, "call_action_under_test")


@pytest.fixture
def loopback(monkeypatch) -> list[dict]:
    """`urllib.request.urlopen`, replaced by the app itself. Returns the
    list of requests the runner really made, so "it posted the call the
    catalogue block documents" is checked rather than assumed."""
    made: list[dict] = []

    class _Response:
        def __init__(self, status: int, content: bytes):
            self.status = status
            self._content = content

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self) -> bytes:
            return self._content

    def fake_urlopen(request, timeout=None):
        body = json.loads(request.data.decode("utf-8"))
        made.append({
            "url": request.full_url,
            "method": request.get_method(),
            "body": body,
            "content_type": request.get_header("Content-type"),
        })
        assert request.full_url.startswith(THE_BASE_URL + "/actions/")
        assert request.get_method() == "POST"
        path = request.full_url[len(THE_BASE_URL):]
        response = client.post(path, json=body)
        if response.status_code >= 400:
            raise urllib.error.HTTPError(
                request.full_url, response.status_code, "", {}, io.BytesIO(response.content),
            )
        return _Response(response.status_code, response.content)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    return made


@pytest.fixture
def resolvable(monkeypatch):
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.deployed_skill_ids",
        lambda: {A_DEPLOYED_SKILL},
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.app_route_table",
        lambda: {("POST", "/__test_action_target_any_inputs")},
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.UI_FEATURE_KEYS",
        (A_REAL_FEATURE_KEY,),
    )


@pytest.fixture
def stored_actions(monkeypatch) -> dict:
    """The whole Action store, in memory, keyed by action id."""
    written: dict = {}

    def read(action_id: str) -> dict:
        if action_id not in written:
            raise FileNotFoundError(action_id)
        return written[action_id]

    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.write_action_json",
        lambda action_id, data: written.update({action_id: data}),
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.read_action_json", read,
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.list_action_ids",
        lambda: sorted(written),
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.delete_action_definition",
        lambda action_id: written.pop(action_id, None),
    )
    return written


@pytest.fixture
def ledger(tmp_path, monkeypatch) -> Path:
    """The ledger's root, moved onto tmp_path -- the real writer, the
    real JSON, a throwaway directory."""
    root = tmp_path / "ActionCalls"
    monkeypatch.setattr("app.data_access.action_calls._action_calls_root", lambda: root)
    return root


def ledger_records(root: Path) -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(root.glob("*.json"))]


def the_one_record(root: Path) -> dict:
    records = ledger_records(root)
    assert len(records) == 1, records
    return records[0]


def drive(runner, capsys, *arguments) -> tuple[int, str]:
    """Run the runner exactly as an agent's `terminal` call would -- its
    real `main()`, over a real command line -- and return (exit code,
    everything it said)."""
    original_argv = list(sys.argv)
    sys.argv = ["call_action.py", *arguments]
    try:
        code = runner.main()
    finally:
        sys.argv = original_argv
    captured = capsys.readouterr()
    return code, (captured.out + captured.err).strip()


A_SKILL_ACTION = {
    "id": "capture-this-thread",
    "description": "File a mail thread into the vault",
    "inputs": [
        {"name": "thread_id", "type": "string", "required": True, "description": "the thread"},
    ],
    "allowed_callers": [THE_CALLER],
    "needs_confirmation": False,
    "implementation": {"skill": {"skill_id": A_DEPLOYED_SKILL}},
}

A_CONFIRMED_ACTION = {
    "id": "archive-the-mailbox",
    "description": "Archive everything",
    "inputs": [],
    "allowed_callers": ["*"],
    "needs_confirmation": True,
    "implementation": {"ui": {"feature_key": A_REAL_FEATURE_KEY}},
}

AN_ACTION_WITH_A_REQUIRED_INPUT = {
    "id": "file-the-note",
    "description": "File a note",
    "inputs": [
        {"name": "folder", "type": "string", "required": True, "description": "where it goes"},
        {"name": "urgent", "type": "boolean", "required": False, "description": ""},
    ],
    "allowed_callers": ["*"],
    "needs_confirmation": False,
    "implementation": {"ui": {"feature_key": A_REAL_FEATURE_KEY}},
}


def test_an_unknown_action_id_reaches_the_operator_as_the_frameworks_own_refusal(
    runner, loopback, resolvable, stored_actions, ledger, capsys,
) -> None:
    """[REQ-SB-95-US-03-AC-03] The agent's door relays what the gate
    said, names the id nobody has, states inability rather than any
    outcome, and leaves a `refused:` row behind -- which is how a
    fabricated capability becomes a discoverable one."""
    code, said = drive(runner, capsys, "send-the-invoice", "--caller", THE_CALLER)

    assert code == 2, said
    assert "REFUSED BY THE APP" in said
    assert "refused:unknown_action" in said
    assert "'send-the-invoice'" in said
    assert "there is no action 'send-the-invoice' in this install's catalogue" in said
    assert "NOTHING WAS PERFORMED" in said
    for an_outcome_that_did_not_happen in ("PERFORMED (call", "AUTHORISED", "RECORDED, NOT"):
        assert an_outcome_that_did_not_happen not in said

    assert loopback[0]["body"] == {
        "caller_agent_id": THE_CALLER, "inputs": {}, "confirmed_call_id": None,
    }
    record = the_one_record(ledger)
    assert record["outcome"] == "refused:unknown_action"
    assert record["action_id"] == "send-the-invoice"


def test_a_missing_required_input_comes_back_as_ask_for_it_by_name(
    runner, loopback, resolvable, stored_actions, ledger, capsys,
) -> None:
    """[REQ-SB-95-US-03-AC-04] The runner asks for the input the app
    named and invents nothing in its place -- neither in what it says
    nor in what was sent."""
    assert client.post("/actions", json=AN_ACTION_WITH_A_REQUIRED_INPUT).status_code == 200

    code, said = drive(
        runner, capsys, "file-the-note", "--caller", THE_CALLER, "--input", "urgent=true",
    )

    assert code == 2, said
    assert "refused:missing_required_input" in said
    assert "'folder'" in said
    assert "ask for it by name" in said
    assert "nothing is guessed or defaulted in its place" in said

    assert loopback[0]["body"]["inputs"] == {"urgent": "true"}
    assert "folder" not in json.dumps(loopback[0]["body"]["inputs"])
    record = the_one_record(ledger)
    assert record["inputs"] == {"urgent": "true"}
    assert "folder" not in record["inputs"]


def test_a_caller_who_may_not_run_it_is_told_so_and_relays_it(
    runner, loopback, resolvable, stored_actions, ledger, capsys,
) -> None:
    """[REQ-SB-95-US-03-AC-03] The second refusal class an agent meets
    in real use. Same single 409, same relayed sentence, same ledger
    row -- the runner does not treat "not for you" differently from
    "does not exist"."""
    assert client.post("/actions", json=A_SKILL_ACTION).status_code == 200

    code, said = drive(
        runner, capsys, "capture-this-thread", "--caller", "someone-else",
        "--input", "thread_id=AAMk-0042",
    )

    assert code == 2, said
    assert "refused:caller_not_permitted" in said
    assert "'someone-else' may not run action 'capture-this-thread'" in said
    assert the_one_record(ledger)["outcome"] == "refused:caller_not_permitted"


def test_an_action_awaiting_confirmation_is_reported_and_the_runner_stops(
    runner, loopback, resolvable, stored_actions, ledger, capsys,
) -> None:
    """[REQ-SB-95-US-03-AC-06] `T04` owns the confirmation; this is the
    runner's half of it. It reports what is waiting, names the call id
    the operator must confirm, performs nothing and makes no second
    attempt of its own."""
    assert client.post("/actions", json=A_CONFIRMED_ACTION).status_code == 200

    code, said = drive(runner, capsys, "archive-the-mailbox", "--caller", THE_CALLER)

    assert code == 2, said
    assert "WAITING FOR THE OPERATOR" in said
    assert "awaiting_confirmation" in said
    assert "needs the operator's confirmation before it runs" in said
    assert "Do not retry" in said

    record = the_one_record(ledger)
    assert record["outcome"] == "awaiting_confirmation"
    assert record["call_id"] in said
    assert len(loopback) == 1, "it stopped rather than re-calling on its own"


def test_a_confirmed_call_is_re_called_with_the_granted_id_and_runs(
    runner, loopback, resolvable, stored_actions, ledger, capsys,
) -> None:
    """[REQ-SB-95-US-03-AC-06] The other half: once the operator has
    confirmed, the agent's re-call names that call id and the Action is
    allowed through, leaving the two rows `T04` joins by
    `granted_by_call_id`."""
    assert client.post("/actions", json=A_CONFIRMED_ACTION).status_code == 200
    drive(runner, capsys, "archive-the-mailbox", "--caller", THE_CALLER)
    waiting = the_one_record(ledger)["call_id"]
    assert client.post(f"/actions/calls/{waiting}/confirm").status_code == 200

    code, said = drive(
        runner, capsys, "archive-the-mailbox", "--caller", THE_CALLER,
        "--confirmed-call-id", waiting,
    )

    assert code == 0, said
    assert "RECORDED, NOT PERFORMED" in said
    assert A_REAL_FEATURE_KEY in said
    spent = [r for r in ledger_records(ledger) if r.get("granted_by_call_id") == waiting]
    assert len(spent) == 1, ledger_records(ledger)


def test_a_skill_grant_is_performed_in_the_runners_own_profile_and_reported_honestly(
    loopback, resolvable, stored_actions, ledger, tmp_path, monkeypatch, capsys,
) -> None:
    """[REQ-SB-95-US-03-AC-02] The app authorises a `skill`
    implementation and never performs it (`ADR-019`); the runner does,
    in the profile it is deployed in, and reports the REAL outcome.

    Everything here lives under `tmp_path` in the exact flat shape
    `HermesSkills.create()` writes -- scripts beside SKILL.md, no
    `scripts/` folder -- so what is proved is the deployed shape, down
    to the runner working out its own agent id from its own path (no
    `--caller` is passed).
    """
    monkeypatch.delenv("HERMES_PROFILE_ID", raising=False)
    profile = tmp_path / "hermes" / "profiles" / THE_CALLER
    deployed_runner = profile / "skills" / "actions" / "call-action" / "call_action.py"
    deployed_runner.parent.mkdir(parents=True)
    shutil.copy(RUNNER_SOURCE, deployed_runner)

    granted = profile / "skills" / "vault" / A_DEPLOYED_SKILL
    granted.mkdir(parents=True)
    (granted / "SKILL.md").write_text(
        "---\nname: capture-the-thread\n---\n\nRun it with "
        'terminal(command="python \\"${HERMES_SKILL_DIR}\\capture.py\\"")\n',
        encoding="utf-8",
    )
    (granted / "capture.py").write_text(
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "handed_over = json.loads(sys.stdin.read() or '{}')\n"
        "Path('it_really_ran.json').write_text(json.dumps({\n"
        "    'stdin': handed_over,\n"
        "    'env': json.loads(os.environ['SECOND_BRAIN_ACTION_INPUTS']),\n"
        "    'call_id': os.environ['SECOND_BRAIN_ACTION_CALL_ID'],\n"
        "}), encoding='utf-8')\n"
        "print('filed thread ' + handed_over['thread_id'])\n",
        encoding="utf-8",
    )

    assert client.post("/actions", json=A_SKILL_ACTION).status_code == 200
    runner = load_runner(deployed_runner, "call_action_deployed")

    code, said = drive(
        runner, capsys, "capture-this-thread", "--input", "thread_id=AAMk-0042",
    )

    assert code == 0, said
    assert "AUTHORISED" in said
    assert "ran in this profile and finished successfully" in said
    assert "filed thread AAMk-0042" in said, "the Skill's own words, not a summary of them"

    # It named itself from its own deployed path, and the app believed
    # it -- which is `ADR-033`'s loopback trust boundary, working.
    assert loopback[0]["body"]["caller_agent_id"] == THE_CALLER

    really_ran = json.loads((granted / "it_really_ran.json").read_text(encoding="utf-8"))
    assert really_ran["stdin"] == {"thread_id": "AAMk-0042"}
    assert really_ran["env"] == {"thread_id": "AAMk-0042"}

    record = the_one_record(ledger)
    assert record["outcome"] == "authorised"
    assert record["grant"]["skill_id"] == A_DEPLOYED_SKILL
    assert really_ran["call_id"] == record["call_id"]


def test_a_granted_skill_that_fails_is_reported_as_a_failure(
    loopback, resolvable, stored_actions, ledger, tmp_path, monkeypatch, capsys,
) -> None:
    """[REQ-SB-95-US-03-AC-02] The grant is not the outcome. A Skill
    that really ran and really failed is reported as failed, with its
    own words -- never as the operation having happened."""
    monkeypatch.delenv("HERMES_PROFILE_ID", raising=False)
    profile = tmp_path / "hermes" / "profiles" / THE_CALLER
    deployed_runner = profile / "skills" / "actions" / "call-action" / "call_action.py"
    deployed_runner.parent.mkdir(parents=True)
    shutil.copy(RUNNER_SOURCE, deployed_runner)
    granted = profile / "skills" / "vault" / A_DEPLOYED_SKILL
    granted.mkdir(parents=True)
    (granted / "SKILL.md").write_text("---\nname: capture-the-thread\n---\n", encoding="utf-8")
    (granted / "capture.py").write_text(
        "import sys\nprint('the mailbox refused the connection', file=sys.stderr)\nraise SystemExit(3)\n",
        encoding="utf-8",
    )

    assert client.post("/actions", json=A_SKILL_ACTION).status_code == 200
    runner = load_runner(deployed_runner, "call_action_deployed_failing")

    code, said = drive(runner, capsys, "capture-this-thread", "--input", "thread_id=AAMk-0042")

    assert code == 1, said
    assert "RAN AND FAILED (exit 3)" in said
    assert "the mailbox refused the connection" in said
    assert "successfully" not in said


def test_the_shipped_starter_records_an_unmet_request_and_it_is_retrievable(
    runner, loopback, resolvable, stored_actions, ledger, capsys,
) -> None:
    """[REQ-SB-95-US-03-AC-05] "I cannot do that" as a real, recorded
    answer. The framework's own starter is seeded, called through the
    runner with the operator's own words, and those words are on disk
    in the ledger afterwards -- readable by id, not merely printed
    once. Nothing is performed: an unmet request is a record, and the
    runner says exactly that."""
    seeding = ActionManager().seed_shipped_starters()
    assert THE_UNMET_REQUEST_STARTER in seeding["seeded"], (
        f"membership, not equality: the shipped set grows (`ESC-080`). Seeded {seeding}"
    )

    their_own_words = "book the Tuesday refinery meeting into my calendar"
    code, said = drive(
        runner, capsys, THE_UNMET_REQUEST_STARTER, "--caller", THE_CALLER,
        "--input", f"request={their_own_words}",
        "--input", "why_no_action_matched=no catalogued action touches the calendar",
    )

    assert code == 0, said
    assert "RECORDED, NOT PERFORMED" in said
    assert A_REAL_FEATURE_KEY in said
    assert "claiming it was done would be false" in said

    record = the_one_record(ledger)
    assert record["action_id"] == THE_UNMET_REQUEST_STARTER
    assert record["caller_agent_id"] == THE_CALLER
    assert record["inputs"]["request"] == their_own_words
    assert record["outcome"] == "pointed_at"

    # Retrievable afterwards, through the ledger's own reader rather
    # than the file this test happens to know the name of: a capability
    # gap nobody can look up later was not recorded, only printed.
    assert record["call_id"] in action_calls_data.list_call_ids()
    assert action_calls_data.read_call_json(record["call_id"])["inputs"]["request"] == their_own_words


def test_the_runner_surfaces_an_unreachable_app_rather_than_claiming_success(
    runner, resolvable, stored_actions, ledger, monkeypatch, capsys,
) -> None:
    """[REQ-SB-95-US-03-AC-05] The backend being down is a real,
    expected state -- `ADR-033` says so explicitly -- and the one place
    a silent fallback would be most tempting. It names the URL it could
    not reach, says nothing was performed, exits non-zero, and writes no
    ledger row, because no call was ever made."""
    def refuse_to_connect(request, timeout=None):
        raise urllib.error.URLError("WinError 10061: no connection could be made")

    monkeypatch.setattr(urllib.request, "urlopen", refuse_to_connect)

    code, said = drive(runner, capsys, "file-the-note", "--caller", THE_CALLER, "--input", "folder=X")

    assert code == 1, said
    assert "NOTHING WAS PERFORMED" in said
    assert "could not be reached at http://127.0.0.1:8001" in said
    assert "do not report the action as done" in said
    assert "do not attempt it another way" in said
    for a_claim_it_must_not_make in ("PERFORMED (call", "AUTHORISED", "REFUSED BY THE APP"):
        assert a_claim_it_must_not_make not in said
    assert not ledger.exists() or ledger_records(ledger) == []


def test_the_runner_refuses_to_guess_which_agent_it_is(runner, loopback, capsys) -> None:
    """[REQ-SB-95-US-03-AC-03] The app believes the caller id it is
    given (`ADR-033`), so a guessed one would record a call nobody made.
    Undeployed -- loaded from the repo rather than from a profile -- it
    has no honest answer, and makes no call at all."""
    code, said = drive(runner, capsys, "file-the-note")

    assert code == 1, said
    assert "cannot tell which agent it is running as" in said
    assert loopback == [], "it must not call with a made-up caller id"


def test_seeding_a_starter_twice_never_overwrites_the_operators_own_copy(
    resolvable, stored_actions,
) -> None:
    """[REQ-SB-95-US-03-AC-05] The shipped starter is a starting point,
    not a managed file. Once this install has it, the shipped copy stops
    applying -- the same rule `seed_shipped_masters()` follows, and for
    the same reason: the seed runs on every boot, so overwriting would
    silently revert the operator's edit on every restart."""
    manager = ActionManager()
    first_pass = manager.seed_shipped_starters()
    assert THE_UNMET_REQUEST_STARTER in first_pass["seeded"], (
        f"membership, not equality: the shipped set grows (`ESC-080`). Seeded {first_pass}"
    )
    stored_actions[THE_UNMET_REQUEST_STARTER]["description"] = "my own words for it"

    again = manager.seed_shipped_starters()

    assert again["seeded"] == [], f"a second pass installs nothing at all: {again}"
    assert THE_UNMET_REQUEST_STARTER in again["kept"], (
        f"the operator's own copy is kept, not overwritten: {again}"
    )
    assert stored_actions[THE_UNMET_REQUEST_STARTER]["description"] == "my own words for it"


def test_the_shipped_starter_is_a_real_definition_this_catalogue_can_hold() -> None:
    """[REQ-SB-95-US-03-AC-05] A shipped file that will not parse is a
    build defect, and it would only show up on a fresh install's first
    boot. Checked here against the real shipped bytes, with nothing
    patched."""
    shipped = shipped_starters.list_shipped_starter_ids()
    assert THE_UNMET_REQUEST_STARTER in shipped, (
        f"membership, not equality: the shipped set grows (`ESC-080`). Shipped {shipped}"
    )
    definition = shipped_starters.read_shipped_starter_json(THE_UNMET_REQUEST_STARTER)

    action = ActionManager()._to_action(THE_UNMET_REQUEST_STARTER, definition)

    assert action.allowed_callers == ["*"], "every agent must be able to report a gap"
    assert action.needs_confirmation is False
    assert action.implementation.kind == "ui", "the app performs nothing about an unmet request"
    assert action.implementation.feature_key in UI_FEATURE_KEYS
    assert [i.name for i in action.inputs if i.required] == ["request"]
