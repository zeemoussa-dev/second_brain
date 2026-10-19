"""The scoped read as a shipped, catalogued Action reached through the call
gate (REQ-SB-95-US-05-T05; AC-06).

The agent's door onto the scoped entity read is the same door as onto
everything else: `POST /actions/{action_id}/call`. Nothing here re-implements
validation, dispatch, refusal or the ledger -- all four are `REQ-SB-95-US-03`'s
and are driven unchanged through the real `app.main.app` with `TestClient`
(which is `httpx.ASGITransport(app=app)` behind a sync wrapper), so these tests
also prove the new route is really REGISTERED rather than merely importable.

**The route table is NOT patched here, unlike the sibling Action test files.**
They invent a route and therefore have to; this Action names a real one
(`GET /vault-search/entity-read`), so leaving the live table alone makes
"`REQ-SB-95-US-02-T02` resolves the implementation against the running app's
own route table" a real observation instead of a stubbed one -- and makes
step 5's rename genuinely break it.

**Nothing here may reach a real write.** Patched, and nothing else:

- the Action store, in memory, so no test touches this install's real
  `<DATA_PATH>/data/Actions/`;
- the Action-call ledger's own root, onto `tmp_path`, so the REAL writer runs
  and is asserted against real files in a directory pytest throws away;
- `settings.vault_path` and `settings.second_brain_data_path`, onto `tmp_path`,
  so the vault walked and the plugins loaded are this file's own;
- `shipped_starters._SHIPPED_STARTERS_DIR` -- see below.

**Why the shipped definition is read from a directory this file writes.** The
starter's own `Action.json` is held back pending `ESC-080`: a second folder
under `app/business/core/actions/starters/` makes three `[REQ-SB-95-US-03-AC-05]`
tests in `tests/test_action_runner_skill.py` fail, because they enumerate the
shipped-starter set exhaustively (`== ["report-unmet-request"]`), and that file
belongs to a `Done` task and is outside this task's `## Files to Modify`.
`THE_SHIPPED_ACTION_JSON` below is the exact text destined for
`starters/read-entity-updates/Action.json`, and it is seeded here through the
real `ActionManager.seed_shipped_starters()` -- so the mechanism, the bytes and
every gate behaviour over them are all verified; only the bytes' resting place
in the repository waits on the authorisation.

The entity vocabulary is synthetic throughout (`glyph`), for the reason the
code under test has none: the framework names no plugin and enumerates no kind
(`ADR-022`, `ADR-035`, `ADR-037`).
"""
import json
import os
import textwrap
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main_app
from app import plugin_api
from app.api import vault_search_router
from app.business.core.actions import shipped_starters
from app.business.core.actions.action_manager import ActionManager
from app.business.core.plugins import plugin_manager as plugin_manager_module
from app.business.core.plugins.plugin_manager import PluginManager
from app.business.core.vault import vault_manager as vault_manager_module
from app.business.core.vault.vault_manager import VaultManager
from app.business.logic import action_invocation, scoped_entity_read
from app.config import settings
from app.obsidian.notes import long_path

client = TestClient(main_app.app)

THE_STARTER = "read-entity-updates"
THE_ROUTE = ("GET", "/vault-search/entity-read")

THE_CALLER = "an-agent"
ANOTHER_AGENT = "another-agent"

# The exact bytes destined for
# `app/business/core/actions/starters/read-entity-updates/Action.json`
# (`ESC-080`). Kept as one literal rather than assembled from a dict so that
# what this file verifies and what ships are the same text, character for
# character, when the authorisation lands.
THE_SHIPPED_ACTION_JSON = """{
  "description": "Read what this install actually knows about ONE named thing -- that thing's own synthesis first, then the evidence tagged to it, newest first. Call this INSTEAD of searching whenever the question names something in particular: the name is resolved against the namespaces registered on this install, and the answer is read from that name's own scope alone, so nothing outside it is returned and no whole-vault search is run. If the name resolves to nothing, or to more than one registered entry, the answer says exactly that -- report it back rather than falling back to a search or answering about something else.",
  "inputs": [
    {
      "name": "name",
      "type": "string",
      "required": true,
      "description": "The name, alias or email domain the operator used, in their own words -- not a tag, not a search phrase, and not your guess at which one they meant."
    },
    {
      "name": "evidence_limit",
      "type": "integer",
      "required": false,
      "description": "Optional: how many evidence notes to return (20 by default). The answer always reports the true total beside the list and says when the list was cut, so ask again for more rather than treating a capped list as everything there is."
    }
  ],
  "allowed_callers": ["*"],
  "needs_confirmation": false,
  "implementation": {
    "http": {
      "method": "GET",
      "path": "/vault-search/entity-read"
    }
  }
}
"""

# -- the entity, its scope and the vault ----------------------------------------------

GLYPH = "glyph"
THE_TAG = "glyph/lumen-cartography"
ANOTHER_ENTITYS_TAG = "glyph/tessellate-works"

THE_NAME = "Lumen Cartography"
AN_ALIAS = "LC"
THE_HUB = "Work/Hubs/Lumen Cartography.md"

# Carries a separator, punctuation and a non-ASCII letter on purpose: anything
# that split, trimmed, cased or mapped `kind` on its way through the route
# would change a byte.
AN_OPAQUE_KIND = "Counterparty :: 42/x -- nee"

A_MEETING_NEWEST = "2026-10-13 06:00:00.000000+00:00"
A_THREAD_SECOND = "2026-10-11T09:30:00+00:00"
A_MEETING_THIRD = "2026-10-09T17:11:47+00:00"
A_THREAD_OLDEST = "2026-10-07 08:00:00.000000+00:00"

THE_ENTITYS_EVIDENCE = [
    ("Work/Threads/a-oldest/a-oldest.md", "Thread", {"last_message_at": A_THREAD_OLDEST}),
    ("Work/Meetings/b-third/b-third.md", "Meeting", {"start": A_MEETING_THIRD}),
    ("Work/Threads/c-second/c-second.md", "Thread", {"last_message_at": A_THREAD_SECOND}),
    ("Work/Meetings/d-newest/d-newest.md", "Meeting", {"start": A_MEETING_NEWEST}),
]
NEWEST_FIRST = ["d-newest", "c-second", "b-third", "a-oldest"]

THE_ENTRY = {
    "slug": "lumen-cartography",
    "name": THE_NAME,
    "aliases": [AN_ALIAS],
    "domains": ["lumen.example.invalid"],
    "hub": THE_HUB,
    "kind": AN_OPAQUE_KIND,
}
A_SECOND_ENTRY_CLAIMING_THE_SAME_NAME = {
    "slug": "tessellate-works",
    "name": "Tessellate Works",
    "aliases": [THE_NAME],
    "domains": [],
    "hub": "Work/Hubs/Tessellate Works.md",
    "kind": "Something Else",
}


def registry_backend(namespace: str) -> str:
    """A plugin whose entries come from a file it rereads every time it is
    asked -- the shape `tests/test_tag_resolution.py` already registers a real
    namespace with."""
    return f'''
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENTRIES = HERE / "entries.json"


def register(api):
    def entries():
        return json.loads(ENTRIES.read_text(encoding="utf-8"))

    api.register_tag_namespace("{namespace}", entries)
'''


def raising_backend(namespace: str, message: str) -> str:
    return f'''
def register(api):
    def entries():
        raise RuntimeError("{message}")

    api.register_tag_namespace("{namespace}", entries)
'''


def install(data_path: Path, plugin_id: str, backend: str) -> Path:
    folder = data_path / "plugins" / plugin_id
    (folder / "backend").mkdir(parents=True)
    (folder / "plugin.json").write_text(json.dumps({
        "id": plugin_id, "name": plugin_id.title(), "version": "0.1.0",
        "framework_api": plugin_api.FRAMEWORK_API, "requires": [],
    }), encoding="utf-8")
    (folder / "backend" / "__init__.py").write_text(textwrap.dedent(backend), encoding="utf-8")

    record_path = data_path / "plugins" / "installed.json"
    record = json.loads(record_path.read_text(encoding="utf-8")) if record_path.is_file() else {"plugins": []}
    record["plugins"].append({"id": plugin_id, "version": "0.1.0"})
    record_path.write_text(json.dumps(record), encoding="utf-8")
    return folder


def register_namespace(data_path: Path, namespace: str, entries: list[dict],
                       plugin_id: str | None = None) -> str:
    plugin_id = plugin_id or f"{namespace}-owner"
    install(data_path, plugin_id, registry_backend(namespace))
    (data_path / "plugins" / plugin_id / "backend" / "entries.json").write_text(
        json.dumps(entries), encoding="utf-8",
    )
    PluginManager().load_all()
    return plugin_id


def write_note(vault_root: Path, relative: str, note_type: str, tags: list[str],
               fields: dict | None = None, body: str = "body") -> Path:
    """Every write goes through `long_path`: pytest's own tmp root plus a real
    subject line is already past Windows' 260 characters, where a plain
    `open()` raises and `os.path.isfile()` answers False without raising."""
    path = Path(vault_root) / relative
    os.makedirs(long_path(path.parent), exist_ok=True)
    lines = ["---", f'type: "{note_type}"', "tags: [" + ", ".join(f'"{tag}"' for tag in tags) + "]"]
    for key, value in (fields or {}).items():
        lines.append(f'{key}: "{value}"')
    lines.append("---")
    with open(long_path(path), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n\n" + body + "\n")
    return path


# -- fixtures -------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def data_path(tmp_path, monkeypatch) -> Path:
    """This file's own App Database Folder. `tests/conftest.py` sandboxes the
    Hermes install and nothing else, so without this the plugin loader would
    read the operator's real installed plugins."""
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path / "data")
    (tmp_path / "data").mkdir()
    return tmp_path / "data"


@pytest.fixture(autouse=True)
def nothing_loaded_here_outlives_this_test(monkeypatch):
    monkeypatch.setattr(plugin_manager_module, "_plugin_tag_namespaces",
                        dict(plugin_manager_module._plugin_tag_namespaces))
    monkeypatch.setattr(plugin_manager_module, "_load_report", list(plugin_manager_module._load_report))
    monkeypatch.setattr(vault_manager_module, "_vault_index", dict(vault_manager_module._vault_index))
    monkeypatch.setattr(vault_manager_module, "_vault_entries", list(vault_manager_module._vault_entries))
    monkeypatch.setattr(vault_manager_module, "_vault_tag_index", dict(vault_manager_module._vault_tag_index))


@pytest.fixture
def vault(tmp_path, monkeypatch):
    """The entity's hub and evidence, plus a second entity, so a read that
    widened past the tag would show in every test here and not only in the one
    that looks for it."""
    root = tmp_path / "vault"
    monkeypatch.setattr(settings, "vault_path", root)

    def build(notes=THE_ENTITYS_EVIDENCE, with_hub: bool = True):
        if with_hub:
            write_note(root, THE_HUB, "Glyph", [THE_TAG],
                       body="## Synthesis\n\nwhat is actually going on with this entity")
        for relative, note_type, fields in notes:
            write_note(root, relative, note_type, [THE_TAG], fields)
        write_note(root, "Work/Hubs/Tessellate Works.md", "Glyph", [ANOTHER_ENTITYS_TAG],
                   body="another entity's synthesis")
        write_note(root, "Work/Threads/z-other/z-other.md", "Thread", [ANOTHER_ENTITYS_TAG],
                   {"last_message_at": A_MEETING_NEWEST})
        VaultManager().rebuild_index()
        return root

    return build


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
    """The ledger's root, moved onto `tmp_path` -- the real writer, the real
    JSON, a throwaway directory. Patched at the root rather than at
    `write_call_json` so the file naming and the mkdir are exercised too: "the
    refusal is in the ledger" has to mean a file, not a recorded intention."""
    root = tmp_path / "ActionCalls"
    monkeypatch.setattr("app.data_access.action_calls._action_calls_root", lambda: root)
    return root


@pytest.fixture
def shipped(tmp_path, monkeypatch) -> Path:
    """The shipped starter, as the real mechanism reads it -- see this file's
    docstring for why the directory is this test's own rather than the
    repository's."""
    starters = tmp_path / "starters"
    (starters / THE_STARTER).mkdir(parents=True)
    (starters / THE_STARTER / "Action.json").write_text(THE_SHIPPED_ACTION_JSON, encoding="utf-8")
    monkeypatch.setattr(shipped_starters, "_SHIPPED_STARTERS_DIR", starters)
    return starters


@pytest.fixture
def dispatched(monkeypatch) -> list[dict]:
    """A spy AROUND the real dispatch seam, not instead of it: a refusal test
    needs to count entries (zero), and an accepted call needs the real
    dispatch to really perform the route."""
    entries: list[dict] = []
    real_seam = action_invocation.dispatch_validated_action_call

    def spy(action, caller_agent_id, validated_inputs):
        entries.append({
            "action_id": action.id,
            "caller_agent_id": caller_agent_id,
            "inputs": dict(validated_inputs),
        })
        return real_seam(action, caller_agent_id, validated_inputs)

    monkeypatch.setattr(
        "app.business.logic.action_invocation.dispatch_validated_action_call", spy,
    )
    return entries


@pytest.fixture
def scoped_reads(monkeypatch) -> list[dict]:
    """A spy AROUND the scoped read itself. A refused call must not merely
    answer "refused" -- the read must never have run, which is only checkable
    by watching the function the route calls."""
    asked: list[dict] = []
    real_read = scoped_entity_read.read_entity_named

    def spy(name, evidence_limit=scoped_entity_read.DEFAULT_EVIDENCE_LIMIT):
        asked.append({"name": name, "evidence_limit": evidence_limit})
        return real_read(name, evidence_limit=evidence_limit)

    monkeypatch.setattr(scoped_entity_read, "read_entity_named", spy)
    return asked


# -- helpers --------------------------------------------------------------------------


def seed() -> dict:
    return ActionManager().seed_shipped_starters()


def call(action_id: str = THE_STARTER, caller: str = THE_CALLER, **inputs):
    return client.post(
        f"/actions/{action_id}/call",
        json={"caller_agent_id": caller, "inputs": inputs},
    )


def accepted_verdict(response) -> dict:
    assert response.status_code == 200, response.text
    verdict = response.json()
    assert verdict["accepted"] is True, verdict
    return verdict


def refusal_of(response) -> dict:
    """Every gate refusal is a 409 whose `detail` IS the verdict."""
    assert response.status_code == 409, response.text
    return response.json()["detail"]


def ledger_records(root: Path) -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(root.glob("*.json"))]


def the_one_record(root: Path) -> dict:
    records = ledger_records(root)
    assert len(records) == 1, records
    return records[0]


def the_entity_read_route():
    """The real route object behind `GET /vault-search/entity-read`, read off
    the router rather than reconstructed."""
    for route in vault_search_router.router.routes:
        if getattr(route, "path", None) == THE_ROUTE[1]:
            return route
    raise AssertionError(f"{THE_ROUTE[1]} is not on vault_search_router")


# -- 1. the shipped Action, called through the gate, answers with the scoped read -----


def test_the_shipped_action_called_through_the_gate_answers_with_the_scoped_read(
    vault, shipped, stored_actions, ledger, dispatched, scoped_reads,
) -> None:
    """[REQ-SB-95-US-05-AC-06] The whole point of the story's sixth scenario:
    an agent reaches the scoped read the same way it reaches anything else.
    The framework's own starter is seeded, called over
    `POST /actions/{id}/call` with a resolvable name, and what comes back is
    the scoped read's OWN result -- hub synthesis first, then the tagged
    evidence newest first -- with a ledger record for the call."""
    vault()
    register_namespace(data_path_of(shipped), GLYPH, [THE_ENTRY])
    assert seed()["seeded"] == [THE_STARTER]

    verdict = accepted_verdict(call(name=THE_NAME))

    assert verdict["outcome"] == "performed"
    assert [entry["inputs"] for entry in dispatched] == [{"name": THE_NAME}]
    assert [asked["name"] for asked in scoped_reads] == [THE_NAME]

    result = verdict["result"]
    assert result["performed"] is True
    assert result["resolution_outcome"] == "resolved"
    assert result["tag"] == THE_TAG
    assert result["kind"] == AN_OPAQUE_KIND, "`kind` is carried through, never interpreted"
    assert result["hub_status"] == scoped_entity_read.HUB_FOUND
    assert result["synthesis"]["role"] == scoped_entity_read.SYNTHESIS
    assert result["synthesis"]["stem"] == THE_NAME
    assert "what is actually going on" in result["synthesis"]["body"]
    assert [note["stem"] for note in result["evidence"]] == NEWEST_FIRST
    assert {note["role"] for note in result["evidence"]} == {scoped_entity_read.EVIDENCE}
    assert all(THE_TAG in note["tags"] for note in result["evidence"])
    assert result["evidence_total"] == 4
    # The body's own key order is the required reading order, so a caller that
    # reads it top to bottom gets synthesis before evidence.
    assert list(result).index("synthesis") < list(result).index("evidence")

    record = the_one_record(ledger)
    assert record["call_id"] == verdict["call_id"]
    assert record["action_id"] == THE_STARTER
    assert record["caller_agent_id"] == THE_CALLER
    assert record["outcome"] == "performed"
    assert record["inputs"] == {"name": THE_NAME}
    assert record["result"]["synthesis"]["stem"] == THE_NAME


def test_an_alias_reaches_the_same_entity_through_the_same_call(
    vault, shipped, stored_actions, ledger, scoped_reads,
) -> None:
    """[REQ-SB-95-US-05-AC-06] The Action takes the operator's own words, so
    the resolver's alias handling has to survive the trip through the gate and
    the query string rather than being a property of a direct function call."""
    vault()
    register_namespace(data_path_of(shipped), GLYPH, [THE_ENTRY])
    seed()

    result = accepted_verdict(call(name=AN_ALIAS))["result"]

    assert result["name_as_asked"] == AN_ALIAS
    assert result["tag"] == THE_TAG
    assert result["synthesis"]["stem"] == THE_NAME


# -- 2. a missing required input: refused by the gate, and the read never runs --------


def test_a_call_without_the_required_name_is_refused_and_the_read_never_runs(
    vault, shipped, stored_actions, ledger, dispatched, scoped_reads,
) -> None:
    """[REQ-SB-95-US-05-AC-06] Ask rather than guess. The gate names the
    missing input, nothing is dispatched, and the scoped read -- spied on
    around the real function -- was never entered, so no vault was read on a
    call that never passed validation."""
    vault()
    register_namespace(data_path_of(shipped), GLYPH, [THE_ENTRY])
    seed()

    refused = refusal_of(call())

    assert refused["accepted"] is False
    assert refused["outcome"] == "refused:missing_required_input"
    assert "'name'" in refused["refusal"]
    assert dispatched == []
    assert scoped_reads == []

    record = the_one_record(ledger)
    assert record["outcome"] == "refused:missing_required_input"
    assert record["inputs"] == {}


# -- 3. an unknown action id: the same refusal path as any other ----------------------


def test_an_unknown_action_id_is_refused_exactly_as_for_any_other_action(
    vault, shipped, stored_actions, ledger, dispatched, scoped_reads,
) -> None:
    """[REQ-SB-95-US-05-AC-06] A near-miss on this Action's own id is not a
    special case: it is refused by the same gate, with the same
    `refused:unknown_action` outcome and the same ledger row an invented id
    anywhere else in the catalogue gets."""
    vault()
    register_namespace(data_path_of(shipped), GLYPH, [THE_ENTRY])
    seed()

    refused = refusal_of(call(action_id="read-entity-update", name=THE_NAME))

    assert refused["outcome"] == "refused:unknown_action"
    assert "read-entity-update" in refused["refusal"]
    assert dispatched == []
    assert scoped_reads == []
    assert the_one_record(ledger)["action_id"] == "read-entity-update"


# -- 4. a caller outside allowed_callers: refused, and the refusal is in the ledger ---


def test_a_caller_outside_allowed_callers_is_refused_and_the_ledger_records_it(
    vault, shipped, stored_actions, ledger, dispatched, scoped_reads,
) -> None:
    """[REQ-SB-95-US-05-AC-06] The starter ships `["*"]` -- every agent may ask
    what is known about a name -- so this narrows the operator's own stored
    copy to one agent, the way the Actions screen does, and calls as somebody
    else. The refusal names the caller and the Action, nothing is dispatched,
    the read never runs, and the ledger row carries both the caller and the
    reason. The same call by the permitted agent is the control."""
    vault()
    register_namespace(data_path_of(shipped), GLYPH, [THE_ENTRY])
    seed()
    assert stored_actions[THE_STARTER]["allowed_callers"] == ["*"]
    assert client.put(f"/actions/{THE_STARTER}",
                      json={"allowed_callers": [THE_CALLER]}).status_code == 200

    refused = refusal_of(call(caller=ANOTHER_AGENT, name=THE_NAME))

    assert refused["outcome"] == "refused:caller_not_permitted"
    assert ANOTHER_AGENT in refused["refusal"]
    assert THE_STARTER in refused["refusal"]
    assert dispatched == []
    assert scoped_reads == []

    record = the_one_record(ledger)
    assert record["call_id"] == refused["call_id"]
    assert record["caller_agent_id"] == ANOTHER_AGENT
    assert record["outcome"] == "refused:caller_not_permitted"
    assert ANOTHER_AGENT in record["refusal"]

    # The control: the same Action, the same inputs, the permitted caller.
    assert accepted_verdict(call(name=THE_NAME))["outcome"] == "performed"


# -- 5. the implementation stops resolving: refused, never half-performed -------------


def test_renaming_the_target_route_makes_the_action_stop_resolving_and_refuses_the_call(
    vault, shipped, stored_actions, ledger, dispatched, scoped_reads, monkeypatch,
) -> None:
    """[REQ-SB-95-US-05-AC-06] The route is renamed in process -- on the real
    route object, so this app's own route table reports the new name, which is
    the same reader `ActionManager` resolves against. The catalogue then says
    the Action is broken, naming the path it can no longer find, and a call is
    refused rather than half-performed: nothing dispatched, no read, and a
    ledger row saying why."""
    vault()
    register_namespace(data_path_of(shipped), GLYPH, [THE_ENTRY])
    seed()
    assert [entry for entry in ActionManager().resolution_report()
            if entry["action_id"] == THE_STARTER][0]["status"] == "resolves"

    monkeypatch.setattr(the_entity_read_route(), "path", "/vault-search/entity-read-renamed")

    broken = [entry for entry in ActionManager().resolution_report()
              if entry["action_id"] == THE_STARTER][0]
    assert broken["status"] == "broken"
    assert THE_ROUTE[1] in broken["reason"]

    refused = refusal_of(call(name=THE_NAME))

    assert refused["outcome"] == "refused:implementation_does_not_resolve"
    assert THE_ROUTE[1] in refused["refusal"]
    assert dispatched == []
    assert scoped_reads == []
    assert the_one_record(ledger)["outcome"] == "refused:implementation_does_not_resolve"


# -- the shipped definition itself ----------------------------------------------------


def test_the_shipped_implementation_resolves_against_this_apps_real_route_table(
    shipped, stored_actions,
) -> None:
    """[REQ-SB-95-US-05-AC-06] `REQ-SB-95-US-02-T02` resolves an `http`
    implementation against the running app's own route table at save time. The
    table is deliberately NOT patched in this file, so the starter being
    saveable is evidence the route is really mounted -- and a neighbouring path
    that is not mounted is refused by the same rule, which is what stops this
    passing for a table that accepted anything."""
    definition = shipped_starters.read_shipped_starter_json(THE_STARTER)
    assert definition["implementation"] == {"http": {"method": THE_ROUTE[0], "path": THE_ROUTE[1]}}

    manager = ActionManager()
    saved = manager.create(THE_STARTER, description=definition["description"],
                           inputs=definition["inputs"],
                           allowed_callers=definition["allowed_callers"],
                           implementation=definition["implementation"])
    assert saved.implementation.path == THE_ROUTE[1]

    with pytest.raises(Exception) as refused:
        manager.create("names-a-route-that-is-not-mounted",
                       implementation={"http": {"method": "GET", "path": "/vault-search/entity"}})
    assert "/vault-search/entity" in str(refused.value)


def test_the_shipped_definition_is_a_real_definition_this_catalogue_can_hold(
    shipped, stored_actions,
) -> None:
    """[REQ-SB-95-US-05-AC-06] A shipped file that will not parse is a build
    defect that would only show up on a fresh install's first boot. Seeded
    through the real mechanism and read back through the catalogue's own
    parser, with its typed inputs and its one required one asserted."""
    assert seed() == {"seeded": [THE_STARTER], "kept": []}
    assert ActionManager().seed_shipped_starters() == {"seeded": [], "kept": [THE_STARTER]}, (
        "a starter is never overwritten -- the operator's own edit outranks the shipped copy"
    )

    action = ActionManager().get_by_id(THE_STARTER)

    assert action.implementation.kind == "http"
    assert (action.implementation.method, action.implementation.path) == THE_ROUTE
    assert [declared.name for declared in action.inputs] == ["name", "evidence_limit"]
    assert [declared.name for declared in action.inputs if declared.required] == ["name"]
    assert [declared.type for declared in action.inputs] == ["string", "integer"]
    assert action.allowed_callers == ["*"]
    assert action.needs_confirmation is False, "a read changes nothing, so it asks nobody"


def test_the_shipped_definition_names_no_business_vocabulary_and_no_plugin() -> None:
    """[REQ-SB-95-US-05-AC-06] The Action's description is the one artefact an
    agent actually reads, and `ADR-022`'s test -- a second brain built for
    someone who tracks nothing but books gets the same framework -- would be
    undone by one example word in it. `kind` is opaque everywhere else in this
    story; leaking a vocabulary here would teach it anyway."""
    definition = json.loads(THE_SHIPPED_ACTION_JSON)
    everything_an_agent_reads = json.dumps(definition).casefold()

    for a_vocabulary_the_framework_must_not_know in (
        "customer", "partner", "opportunity", "plugin", "entities", "hermes", "obsidian",
    ):
        assert a_vocabulary_the_framework_must_not_know not in everything_an_agent_reads, (
            f"the shipped Action names {a_vocabulary_the_framework_must_not_know!r}"
        )


# -- the three non-answers, surfaced rather than flattened ----------------------------


def test_a_name_that_did_not_resolve_and_an_entity_with_no_evidence_are_different_answers(
    vault, shipped, stored_actions, ledger, scoped_reads,
) -> None:
    """[REQ-SB-95-US-05-AC-06] The one collapse that would undo the story: both
    of these could be served as an empty list. They are not. "Nothing knows
    that name" comes back `performed: false` with the name repeated as asked
    and no read performed; "that entity exists and nothing has been written
    about it" comes back `performed: true`, saying so by tag."""
    vault(notes=[], with_hub=False)
    register_namespace(data_path_of(shipped), GLYPH, [{**THE_ENTRY, "hub": None}])
    seed()

    did_not_resolve = accepted_verdict(call(name="Nobody Registered This"))["result"]
    assert did_not_resolve["performed"] is False
    assert did_not_resolve["resolution_outcome"] == "did_not_resolve"
    assert did_not_resolve["name_as_asked"] == "Nobody Registered This"
    assert "Nobody Registered This" in did_not_resolve["message"]
    assert did_not_resolve["tag"] is None
    assert did_not_resolve["evidence"] == []
    assert did_not_resolve["found_anything"] is False

    nothing_written_about_it = accepted_verdict(call(name=THE_NAME))["result"]
    assert nothing_written_about_it["performed"] is True
    assert nothing_written_about_it["resolution_outcome"] == "resolved"
    assert nothing_written_about_it["tag"] == THE_TAG
    assert nothing_written_about_it["evidence"] == []
    assert nothing_written_about_it["evidence_total"] == 0
    assert nothing_written_about_it["found_anything"] is False
    assert THE_TAG in nothing_written_about_it["message"]

    assert did_not_resolve["performed"] != nothing_written_about_it["performed"], (
        "two different facts must not reach the agent as the same empty list"
    )


def test_an_ambiguous_name_names_both_candidates_rather_than_picking_one(
    vault, shipped, stored_actions, ledger,
) -> None:
    """[REQ-SB-95-US-05-AC-06] `T03`'s second non-answer, carried out through
    the route unflattened: two registered entries claim the one name, so the
    answer is `ambiguous` with both named and no tag at all -- never one of
    them silently."""
    vault()
    register_namespace(data_path_of(shipped), GLYPH,
                       [THE_ENTRY, A_SECOND_ENTRY_CLAIMING_THE_SAME_NAME])
    seed()

    result = accepted_verdict(call(name=THE_NAME))["result"]

    assert result["performed"] is False
    assert result["resolution_outcome"] == "ambiguous"
    assert result["tag"] is None
    assert result["synthesis"] is None
    assert result["evidence"] == []
    candidates = {candidate["tag"] for candidate in result["resolution"]["candidates"]}
    assert candidates == {THE_TAG, ANOTHER_ENTITYS_TAG}


def test_a_namespace_that_could_not_answer_makes_the_answer_incomplete_not_final(
    vault, shipped, stored_actions, ledger, data_path,
) -> None:
    """[REQ-SB-95-US-05-AC-06] `T03`'s third shape, which an agent must be able
    to tell from a confident "nothing knows that name": one registered
    namespace raises when asked, so the non-answer travels with
    `every_namespace_answered: false` and the failing namespace named."""
    vault()
    register_namespace(data_path, GLYPH, [THE_ENTRY])
    install(data_path, "ward-owner", raising_backend("ward", "its registry file is gone"))
    PluginManager().load_all()
    seed()

    result = accepted_verdict(call(name="Nobody Registered This"))["result"]

    assert result["resolution_outcome"] == "did_not_resolve"
    assert result["every_namespace_answered"] is False
    could_not_answer = result["resolution"]["namespaces_that_could_not_answer"]
    assert [entry["namespace"] for entry in could_not_answer] == ["ward"]
    assert "its registry file is gone" in could_not_answer[0]["failure"]


# -- the cap and the undated rule survive the trip through the gate -------------------


def test_the_optional_limit_caps_the_list_and_the_true_total_is_reported_beside_it(
    vault, shipped, stored_actions, ledger, scoped_reads,
) -> None:
    """[REQ-SB-95-US-05-AC-06] The Action's one optional input really reaches
    the route (it travels as a query parameter, which only a real dispatch
    proves), and a capped list is never passed off as the whole of what is
    known: the true total and the fact that it was cut both come back."""
    vault()
    register_namespace(data_path_of(shipped), GLYPH, [THE_ENTRY])
    seed()

    result = accepted_verdict(call(name=THE_NAME, evidence_limit=2))["result"]

    assert [asked["evidence_limit"] for asked in scoped_reads] == [2]
    assert [note["stem"] for note in result["evidence"]] == NEWEST_FIRST[:2]
    assert result["evidence_returned"] == 2
    assert result["evidence_total"] == 4
    assert result["evidence_truncated"] is True


def test_an_undated_note_sorts_last_and_says_why_rather_than_passing_as_newest(
    vault, shipped, stored_actions, ledger,
) -> None:
    """[REQ-SB-95-US-05-AC-06] `T04`'s documented fallback reaches the agent
    intact: the undated note is last, carries the sentence saying which field
    was missing, and the rule itself travels with the answer so a reader does
    not have to infer it."""
    vault(notes=[*THE_ENTITYS_EVIDENCE,
                 ("Work/Threads/u-no-stamp/u-no-stamp.md", "Thread", {})])
    register_namespace(data_path_of(shipped), GLYPH, [THE_ENTRY])
    seed()

    result = accepted_verdict(call(name=THE_NAME))["result"]

    assert [note["stem"] for note in result["evidence"]] == [*NEWEST_FIRST, "u-no-stamp"]
    undated = result["evidence"][-1]
    assert undated["recency"] == scoped_entity_read.UNDATED
    assert "last_message_at" in undated["undated_because"]
    assert result["undated_evidence_rule"] == scoped_entity_read.UNDATED_EVIDENCE_RULE


def data_path_of(shipped: Path) -> Path:
    """The App Database Folder beside the starters directory this test wrote --
    both live under the same `tmp_path`, so a test that already has one can
    reach the other without taking a second fixture."""
    return shipped.parent / "data"
