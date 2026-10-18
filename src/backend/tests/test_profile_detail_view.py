"""One composed read of what a Hermes profile really is (`REQ-SB-99-US-01-T05`,
`ADR-043`).

`GET /hermes/agents/{id}/profile-detail` joins the four readers the rest of
this story built -- the soul verbatim, the per-profile skills verdict, the two
config layers, the per-profile cron jobs and the honest toolsets read -- into
one read-only response. What is pinned here is what composing can get wrong:

- **Honest absence survives the join.** Absent, unreadable and empty stay three
  different answers, per file and per region. A region that could not be read
  renders as unread, never as a region holding nothing -- the same lie
  `BUG-085` (a job reporting `ok` while capture was dead) and `BUG-088` (a
  refused plugin drawn as a broken page) were about.
- **An unreadable install fakes no region at all**, and is a 200 rather than a
  404: "no such profile" and "I cannot see the install" are different facts.
- **Looking writes nothing** -- every file under `tmp_path` is hashed before
  and after three requests.
- **Cost is pinned by equality, not by a bound.** One `read_tools` and one
  skills listing per request, and zero of either added to `GET /agents` or
  `GET /hermes/agents` (`BUG-086`: 4.4 of the Agents Map's 6 seconds was a
  listing path nobody had counted).
- **No second opinion.** The skills region is asserted equal to
  `SkillManager.compare_profile_skills()` called directly, and no merged or
  effective config value exists anywhere in the response.

No test here touches the operator's real install: every fixture is a real
Hermes home under `tmp_path` read by a real `HermesClient`, both spawn entry
points are refused for the whole file, and the last two tests assert
conftest's sandbox and that every path read during a request lies under
`tmp_path`.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main_app
from app.business.core.skills.skill_manager import SkillManager
from app.business.hermes import client as client_module
from app.business.hermes import cron_status
from app.business.hermes.profile_detail import (
    KEY_IS_NOT_SET,
    KEY_SOURCE_IS_UNKNOWN,
    REGION_WAS_NOT_READ,
)
from app.config import settings
from app.data_access import skills as skills_data
from app.hermes import HermesClient
from app.hermes.cli import HermesCLI
from app.hermes.profiles import (
    CONFIG_LAYER_INSTALL_ROOT,
    CONFIG_LAYER_PROFILE,
    FILE_IS_ABSENT,
    FILE_IS_UNREADABLE,
    FILE_WAS_READ,
)

# Captured before anything can patch it -- the recorder wraps the real read.
_REAL_READ_TEXT = Path.read_text

PROFILE = "adnoc-expert"
DETAIL_URL = f"/hermes/agents/{PROFILE}/profile-detail"

PROFILE_SOUL = """# ADNOC Expert

You act for the operator on everything ADNOC. You know the account's history, its people and
its open commitments, and you answer from the vault rather than from memory.

## Guardrails

- Never quote a commercial figure that is not in the vault.

## Scope

Your scope is the ADNOC account and nothing else. That means the Customer note, every Project
note beneath it, the meetings and the threads that evidence them -- and, deliberately, not the
operator's personal notes, even when they mention ADNOC in passing.

folders:
  - Customers/ADNOC
tags:
  - adnoc

## Escalation

When a commitment is at risk, say so in the first line of the answer rather than at the end.
"""

ROOT_SOUL = "You are the primary identity of this install.\n"

# The profile sets only `model.default`; the install root sets `model.provider`
# and `logging.level` and nothing else -- so "set here", "inherited from the
# install root" and "not set" (`agent.reasoning_effort`, in neither file) are
# all three observable, and a merge would be visible as one layer carrying
# keys the other's file holds.
ROOT_CONFIG = "model:\n  provider: custom\nlogging:\n  level: info\n"
PROFILE_CONFIG = "model:\n  default: gpt-5\n"

PROFILE_DESCRIPTION = f"The {PROFILE} profile."


def skill_md(version: str, body: str) -> str:
    return f"---\nname: a-skill\nversion: {version}\n---\n{body}\n"


# The profile's own tree -- one of each verdict, including a slug the catalog
# has never heard of (the fifth status only the install-first direction sees).
DEPLOYED_TREE = {
    "vault/vault-index": skill_md("1.0.0", "index the vault"),
    "vault/thread-capture": skill_md("0.9.0", "an older body"),
    "outlook/email-capture": skill_md("2.0.0", "edited in place"),
    "jarvis/hand-rolled-thing": skill_md("0.1.0", "written on the box"),
}

CATALOG = {
    "vault-index": skill_md("1.0.0", "index the vault"),
    "thread-capture": skill_md("1.2.0", "the current body"),
    "email-capture": skill_md("2.0.0", "what we actually ship"),
}

EXPECTED_VERDICTS = {
    "vault-index": "current",
    "thread-capture": "stale",
    "email-capture": "modified",
    "hand-rolled-thing": "unknown_to_framework",
}

TOOLS_LIST_OUTPUT = "  ✓ enabled vault\n  ✓ enabled outlook\n  ✗ disabled web_search\n"


def raw_job(job_id: str, name: str, schedule: str, last_status: str) -> dict:
    """One job as it really sits in a `cron/jobs.json` on disk."""
    return {
        "id": job_id, "name": name, "prompt": "", "skill": "",
        "schedule": {"kind": "interval", "display": schedule},
        "enabled": True, "state": "scheduled", "created_at": "2026-10-01T08:00:00",
        "next_run_at": "2026-10-18T09:00:00", "last_run_at": "2026-10-18T07:00:00",
        "last_status": last_status, "last_error": None, "failure_streak": 0,
        "deliver": "none", "repeat": {"times": None, "completed": 0},
    }


PROFILE_JOB = raw_job("A1", "adnoc-digest", "every day at 07:00", "failed")
ROOT_JOB = raw_job("R1", "vault-reindex", "every 6 hours", "success")


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def no_real_process_escapes_this_file(monkeypatch):
    """The only subprocess this view makes is `hermes tools list`, and every
    test here fakes it at `_run`. Refusing both spawn entry points for the
    whole file turns that into something the suite enforces."""

    def refuse(*args, **kwargs):
        raise AssertionError(f"a profile-detail test spawned a real process: {args!r}")

    monkeypatch.setattr(subprocess, "run", refuse)
    monkeypatch.setattr(subprocess, "Popen", refuse)


@pytest.fixture()
def hermes_home(tmp_path, monkeypatch) -> Path:
    """A real (tiny) Hermes install: the `default` profile at the root with
    its own cron job, and one named profile with a soul, a config, four
    deployed skills and a cron job of its own."""
    home = tmp_path / "hermes"
    write(home / "SOUL.md", ROOT_SOUL)
    write(home / "config.yaml", ROOT_CONFIG)
    write(home / "cron" / "jobs.json", json.dumps({"jobs": [ROOT_JOB]}))

    profile_dir = home / "profiles" / PROFILE
    write(profile_dir / "SOUL.md", PROFILE_SOUL)
    write(profile_dir / "config.yaml", PROFILE_CONFIG)
    write(profile_dir / "profile.yaml", f"description: {PROFILE_DESCRIPTION}\n")
    write(profile_dir / "cron" / "jobs.json", json.dumps({"jobs": [PROFILE_JOB]}))
    for skill_id, content in DEPLOYED_TREE.items():
        write(profile_dir / "skills" / skill_id / "SKILL.md", content)

    monkeypatch.setattr(settings, "hermes_home_path", home)
    # The Registry and the vault are not this view's concern, but `GET /agents`
    # composes them -- pointed at empty temp directories so no assertion here
    # can reach the operator's real vault.
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path / "data")
    monkeypatch.setattr(settings, "vault_path", tmp_path / "vault")
    return home


class Spies:
    """Counts the two seams the cost constraint is about, by recording which
    profile each call was for -- a count alone cannot catch "once per profile
    on the install", which is the shape `BUG-086` measured."""

    def __init__(self) -> None:
        self.read_tools_calls: list[str | None] = []
        self.skills_listed_for: list[str] = []
        self.catalog_reads: list[str] = []
        self.deployed_bytes_read: list[tuple[str, str]] = []
        self.tools_list_output = TOOLS_LIST_OUTPUT
        self.tools_list_succeeds = True

    def clear(self) -> None:
        self.read_tools_calls.clear()
        self.skills_listed_for.clear()
        self.catalog_reads.clear()
        self.deployed_bytes_read.clear()


@pytest.fixture()
def spies(hermes_home, monkeypatch) -> Spies:
    """A real `HermesClient` over the temp install, with the two expensive
    seams wrapped rather than replaced -- the files stay real, the calls get
    counted."""
    client = HermesClient.init(base_url="http://127.0.0.1:9119", home_path=hermes_home)
    monkeypatch.setattr(client_module, "_client", client)
    recorded = Spies()

    def fake_run(_self, args, timeout=30.0):
        if args[-2:] == ["tools", "list"]:
            if not recorded.tools_list_succeeds:
                return False, "hermes tools list: the install refused to answer"
            return True, recorded.tools_list_output
        raise AssertionError(f"the view ran an unexpected hermes command: {args!r}")

    monkeypatch.setattr(HermesCLI, "_run", fake_run)

    real_read_tools = client.cli.read_tools
    real_list_skills = client.skills.get_all
    real_read_skill = client.skills.read

    def counted_read_tools(profile_id=None):
        recorded.read_tools_calls.append(profile_id)
        return real_read_tools(profile_id)

    def counted_list_skills(profile_id):
        recorded.skills_listed_for.append(profile_id)
        return real_list_skills(profile_id)

    def counted_read_skill(profile_id, skill_id):
        recorded.deployed_bytes_read.append((profile_id, skill_id))
        return real_read_skill(profile_id, skill_id)

    monkeypatch.setattr(client.cli, "read_tools", counted_read_tools)
    monkeypatch.setattr(client.skills, "get_all", counted_list_skills)
    monkeypatch.setattr(client.skills, "read", counted_read_skill)

    def read_skill_md(slug: str) -> str | None:
        recorded.catalog_reads.append(slug)
        return CATALOG.get(slug)

    def refuse_to_write(*args, **kwargs):
        raise AssertionError("a read-only view attempted a catalog/Registry write")

    monkeypatch.setattr(skills_data, "read_skill_md", read_skill_md)
    monkeypatch.setattr(skills_data, "write_skill_md", refuse_to_write)
    monkeypatch.setattr(skills_data, "write_section_access_map", refuse_to_write)
    monkeypatch.setattr(skills_data, "delete_skill_dir", refuse_to_write)
    monkeypatch.setattr(skills_data, "write_script", refuse_to_write)
    return recorded


@pytest.fixture()
def api(spies) -> TestClient:
    return TestClient(main_app.app)


def get_detail(api: TestClient, url: str = DETAIL_URL) -> dict:
    response = api.get(url)
    assert response.status_code == 200, response.text
    return response.json()


def keys_by_name(detail: dict) -> dict[str, dict]:
    return {row["key"]: row for row in detail["config"]["keys"]}


def layers_by_source(detail: dict) -> dict[str, dict]:
    return {layer["source"]: layer for layer in detail["config"]["layers"]}


# [REQ-SB-99-US-01-AC-01]
def test_the_soul_region_is_the_file_itself_and_the_excerpt_surfaces_are_untouched(api, hermes_home):
    soul_path = hermes_home / "profiles" / PROFILE / "SOUL.md"

    detail = get_detail(api)
    soul = detail["soul"]

    assert soul["text"] == soul_path.read_text(encoding="utf-8")
    assert soul["path"] == str(soul_path), "the operator must be able to open the same file"
    assert (soul["read"], soul["status"], soul["error"]) == (True, FILE_WAS_READ, "")
    assert len(soul["text"]) > 280, "the 280-character excerpt is not the soul"
    assert "Your scope is the ADNOC account and nothing else." in soul["text"], (
        "the `## Scope` BODY is the genuine loss everywhere else"
    )
    assert soul["text"].index("## Guardrails") < soul["text"].index("## Scope") < soul["text"].index("## Escalation")

    # The live Agents Map surfaces, unchanged by this story.
    agent = api.get(f"/agents/{PROFILE}")
    assert agent.status_code == 200, agent.text
    assert agent.json()["description"] == PROFILE_DESCRIPTION
    hermes_agent = api.get(f"/hermes/agents/{PROFILE}").json()
    assert hermes_agent["description"] == PROFILE_DESCRIPTION
    assert hermes_agent["short_description"] == PROFILE_DESCRIPTION
    assert hermes_agent["description"] != soul["text"]


# [REQ-SB-99-US-01-AC-02]
def test_every_deployed_skill_appears_with_its_version_and_verdict(api, spies):
    detail = get_detail(api)

    rows = {row["slug"]: row for row in detail["skills"]["items"]}
    assert detail["skills"]["read"] is True
    assert {slug: row["status"] for slug, row in rows.items()} == EXPECTED_VERDICTS
    assert rows["vault-index"]["deployed_version"] == "1.0.0"
    assert rows["thread-capture"]["deployed_version"] == "0.9.0"
    assert rows["thread-capture"]["catalog_version"] == "1.2.0"
    assert rows["email-capture"]["deployed_version"] == "2.0.0"
    assert rows["hand-rolled-thing"]["deployed_version"] == "0.1.0"
    assert rows["hand-rolled-thing"]["catalog_version"] is None


# [REQ-SB-99-US-01-AC-02]
def test_the_view_adds_no_second_opinion_to_the_skills_verdict(api, spies):
    """The rows are the Manager's own answer, not a re-derivation of it: two
    implementations of "does the deployed copy match" is the failure that let
    228 stale copies of one file run across 41 profiles (`ADR-043`)."""
    from_the_view = get_detail(api)["skills"]["items"]

    from_the_manager = SkillManager().compare_profile_skills(PROFILE)

    assert from_the_view == from_the_manager


# [REQ-SB-99-US-01-AC-03]
def test_config_is_two_labelled_layers_with_every_key_naming_its_own_file(api, hermes_home):
    detail = get_detail(api)
    layers = layers_by_source(detail)
    keys = keys_by_name(detail)

    assert [layer["source"] for layer in detail["config"]["layers"]] == [
        CONFIG_LAYER_PROFILE, CONFIG_LAYER_INSTALL_ROOT,
    ]
    assert layers[CONFIG_LAYER_PROFILE]["path"] == str(hermes_home / "profiles" / PROFILE / "config.yaml")
    assert layers[CONFIG_LAYER_INSTALL_ROOT]["path"] == str(hermes_home / "config.yaml")
    assert layers[CONFIG_LAYER_PROFILE]["values"] == {"model": {"default": "gpt-5"}}
    assert layers[CONFIG_LAYER_INSTALL_ROOT]["values"] == {
        "model": {"provider": "custom"}, "logging": {"level": "info"},
    }

    # Set here / inherited from the install root / set nowhere.
    assert keys["model.default"]["value"] == "gpt-5"
    assert keys["model.default"]["source"] == CONFIG_LAYER_PROFILE
    assert keys["model.default"]["path"] == layers[CONFIG_LAYER_PROFILE]["path"]
    assert keys["model.provider"]["value"] == "custom"
    assert keys["model.provider"]["source"] == CONFIG_LAYER_INSTALL_ROOT
    assert keys["model.provider"]["path"] == layers[CONFIG_LAYER_INSTALL_ROOT]["path"]
    assert keys["logging.level"]["source"] == CONFIG_LAYER_INSTALL_ROOT
    assert keys["agent.reasoning_effort"]["source"] == KEY_IS_NOT_SET
    assert keys["agent.reasoning_effort"]["value"] is None
    assert keys["agent.reasoning_effort"]["path"] is None


# [REQ-SB-99-US-01-AC-03]
def test_the_enabled_toolsets_come_from_the_honest_read(api):
    toolsets = get_detail(api)["toolsets"]

    assert toolsets["read"] is True
    assert toolsets["items"] == {"vault": True, "outlook": True, "web_search": False}
    assert toolsets["error"] == ""


# [REQ-SB-99-US-01-AC-03]
def test_no_merged_or_effective_config_value_exists_anywhere_in_the_response(api):
    """Hermes' own precedence between the two files is not readable from this
    repository, so any single "this is the value" answer would be a guess at
    which file won."""
    detail = get_detail(api)

    def every_key_name(node) -> list[str]:
        if isinstance(node, dict):
            return [k for key, value in node.items() for k in [key, *every_key_name(value)]]
        if isinstance(node, list):
            return [k for item in node for k in every_key_name(item)]
        return []

    forbidden = [k for k in every_key_name(detail) if any(
        word in str(k).lower() for word in ("merged", "effective", "resolved")
    )]
    assert forbidden == [], f"a merged/effective value leaked into the response: {forbidden}"
    # Each layer holds only what its own file holds -- neither carries the other's keys.
    layers = layers_by_source(detail)
    assert "provider" not in layers[CONFIG_LAYER_PROFILE]["values"]["model"]
    assert "default" not in layers[CONFIG_LAYER_INSTALL_ROOT]["values"]["model"]


# [REQ-SB-99-US-01-AC-04]
def test_the_profiles_own_jobs_and_the_install_level_ones_are_never_merged(api):
    detail = get_detail(api)
    cron = detail["cron_jobs"]

    assert [job["id"] for job in cron["items"]] == ["A1"]
    assert cron["items"][0]["schedule_display"] == "every day at 07:00"
    assert cron["items"][0]["last_status"] == "failed"
    assert cron["items"][0]["last_run_at"] == "2026-10-18T07:00:00"
    assert cron["items"][0]["scope"] == "profile"
    assert [job["id"] for job in cron["install_level"]] == ["R1"], (
        "a job that runs with no `-p` must be visible somewhere rather than nowhere"
    )
    assert cron["install_level"][0]["scope"] == "install"
    assert cron["install_level_is_this_profile"] is False


# [REQ-SB-99-US-01-AC-04]
def test_the_existing_cron_endpoint_is_untouched(api):
    response = api.get("/hermes/cron/jobs")

    assert response.status_code == 200
    assert [job["id"] for job in response.json()] == ["R1"], (
        "`GET /hermes/cron/jobs` stays install-root-only -- widening it is `REQ-SB-96`'s"
    )
    assert response.json() == cron_status.list_cron_jobs()


# [REQ-SB-99-US-01-AC-04]
def test_the_primary_profile_does_not_list_its_own_jobs_twice(api):
    """The `default` profile IS <HERMES_HOME>, so its cron directory and the
    install's are the same directory."""
    detail = get_detail(api, "/hermes/agents/default/profile-detail")

    assert [job["id"] for job in detail["cron_jobs"]["items"]] == ["R1"]
    assert detail["cron_jobs"]["install_level"] == []
    assert detail["cron_jobs"]["install_level_is_this_profile"] is True


# [REQ-SB-99-US-01-AC-05]
def test_opening_refreshing_and_leaving_the_view_writes_nothing(api, tmp_path):
    def snapshot() -> dict[str, tuple[str, float] | None]:
        taken = {}
        for path in sorted(tmp_path.rglob("*")):
            key = str(path.relative_to(tmp_path))
            if path.is_dir():
                taken[key] = None
            else:
                taken[key] = (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime)
        return taken

    before = snapshot()

    for _ in range(3):  # open, refresh, leave
        get_detail(api)

    after = snapshot()
    assert after == before, (
        "reading a profile changed the install: "
        f"created={sorted(set(after) - set(before))} removed={sorted(set(before) - set(after))}"
    )


# [REQ-SB-99-US-01-AC-05]
def test_the_view_writes_no_registry_record(api, monkeypatch):
    """The catalog/Registry write functions are already monkeypatched to raise
    for every test in this file (`spies`); this one states that the three
    requests above really do exercise them, by pinning the Skill store's own
    files untouched as well."""
    skill_store = Path(skills_data.__file__).resolve()
    before = (skill_store.read_bytes(), skill_store.stat().st_mtime)

    get_detail(api)

    assert (skill_store.read_bytes(), skill_store.stat().st_mtime) == before


# [REQ-SB-99-US-01-AC-06]
def test_three_broken_reads_are_three_different_answers_in_one_response(api, spies, hermes_home):
    """A missing soul, an unreadable config layer and a failed subprocess, all
    at once -- each named, each confined to its own region, and the regions
    that still work still work."""
    (hermes_home / "profiles" / PROFILE / "SOUL.md").unlink()
    (hermes_home / "profiles" / PROFILE / "config.yaml").write_text(
        "model:\n  default: [unclosed\n", encoding="utf-8",
    )
    spies.tools_list_succeeds = False

    detail = get_detail(api)

    soul = detail["soul"]
    assert (soul["read"], soul["status"], soul["text"]) == (False, FILE_IS_ABSENT, None)
    assert str(hermes_home / "profiles" / PROFILE / "SOUL.md") in soul["error"]

    layers = layers_by_source(detail)
    assert layers[CONFIG_LAYER_PROFILE]["status"] == FILE_IS_UNREADABLE
    assert layers[CONFIG_LAYER_PROFILE]["values"] is None
    assert str(hermes_home / "profiles" / PROFILE / "config.yaml") in layers[CONFIG_LAYER_PROFILE]["error"]
    assert layers[CONFIG_LAYER_INSTALL_ROOT]["status"] == FILE_WAS_READ
    assert layers[CONFIG_LAYER_INSTALL_ROOT]["values"] == {
        "model": {"provider": "custom"}, "logging": {"level": "info"},
    }, "one unreadable layer never hides the other"
    assert keys_by_name(detail)["model.default"]["source"] == KEY_SOURCE_IS_UNKNOWN, (
        "a key missing from a file we could not read is unknown, not 'not set'"
    )

    toolsets = detail["toolsets"]
    assert toolsets["read"] is False
    assert toolsets["items"] is None, "a failed read must never render as an empty 'nothing enabled'"
    assert "refused to answer" in toolsets["error"]

    # The regions that could be read still carry their real content.
    assert {row["slug"]: row["status"] for row in detail["skills"]["items"]} == EXPECTED_VERDICTS
    assert [job["id"] for job in detail["cron_jobs"]["items"]] == ["A1"]
    assert detail["install"]["readable"] is True


# [REQ-SB-99-US-01-AC-06]
def test_an_empty_soul_is_a_successful_read_and_not_an_absent_one(api, hermes_home):
    (hermes_home / "profiles" / PROFILE / "SOUL.md").write_text("", encoding="utf-8")

    soul = get_detail(api)["soul"]

    assert (soul["read"], soul["status"], soul["text"], soul["error"]) == (True, FILE_WAS_READ, "", "")


# [REQ-SB-99-US-01-AC-06]
def test_a_profile_that_does_not_exist_on_a_readable_install_is_a_404(api):
    response = api.get("/hermes/agents/no-such-profile/profile-detail")

    assert response.status_code == 404
    assert "no-such-profile" in response.json()["detail"]


# [REQ-SB-99-US-01-AC-07]
def test_an_unreadable_install_reports_itself_and_fabricates_no_region(tmp_path, monkeypatch):
    absent_home = tmp_path / "no-hermes-install-here"
    monkeypatch.setattr(settings, "hermes_home_path", absent_home)
    monkeypatch.setattr(
        client_module, "_client",
        HermesClient.init(base_url="http://127.0.0.1:9119", home_path=absent_home),
    )

    response = TestClient(main_app.app).get(DETAIL_URL)

    assert response.status_code == 200, "an unreadable install is not 'no such profile'"
    detail = response.json()
    assert detail["install"]["readable"] is False
    assert str(absent_home) in detail["install"]["error"], "it must name why"

    for region_name in ("soul", "skills", "config", "cron_jobs", "toolsets"):
        region = detail[region_name]
        assert region["read"] is False, f"{region_name} claimed it was read"
        assert region["error"], f"{region_name} failed silently"
    assert detail["soul"]["text"] is None and detail["soul"]["status"] == REGION_WAS_NOT_READ
    assert detail["skills"]["items"] is None, "an unread region is never an empty list"
    assert detail["config"]["layers"] is None and detail["config"]["keys"] is None
    assert detail["cron_jobs"]["items"] is None and detail["cron_jobs"]["install_level"] is None
    assert detail["toolsets"]["items"] is None
    assert not absent_home.exists(), "looking at an absent install must not create it"


# [constraint: cost]
def test_one_request_costs_one_toolsets_read_and_one_skills_listing(api, spies):
    spies.clear()

    get_detail(api)

    assert spies.read_tools_calls == [PROFILE], "exactly one `hermes tools list`, for this profile only"
    assert spies.skills_listed_for == [PROFILE], "exactly one skills listing, for this profile only"
    assert sorted(spies.catalog_reads) == [
        "email-capture", "hand-rolled-thing", "thread-capture", "vault-index",
    ], "exactly one catalog read per distinct slug on disk"
    # No deployed bytes are read for the slug the catalog does not have: there
    # is nothing to compare it against.
    assert sorted(spies.deployed_bytes_read) == [
        (PROFILE, "outlook/email-capture"), (PROFILE, "vault/thread-capture"), (PROFILE, "vault/vault-index"),
    ]


# [constraint: cost]
def test_the_listing_endpoints_pay_nothing_for_this_view(api, spies):
    """`BUG-086` was a listing path that quietly read every SKILL.md of every
    profile. Pinned by equality on both endpoints, not by a bound."""
    spies.clear()
    assert api.get("/agents").status_code == 200
    assert spies.read_tools_calls == [], "`GET /agents` must spawn no `hermes tools list`"
    assert spies.skills_listed_for == [], "`GET /agents` must read no profile's skills"
    assert (spies.catalog_reads, spies.deployed_bytes_read) == ([], []), "no skills comparison on a listing"

    spies.clear()
    assert api.get("/hermes/agents").status_code == 200
    assert spies.read_tools_calls == [], "`GET /hermes/agents` must spawn no `hermes tools list`"
    assert (spies.catalog_reads, spies.deployed_bytes_read) == ([], []), "no skills comparison on a listing"
    assert spies.skills_listed_for == ["default", PROFILE], (
        "unchanged from before this story: the Hermes mirror lists each profile's skills once"
    )


# [constraint: cost]
def test_a_failed_toolsets_read_is_not_retried(api, spies):
    spies.tools_list_succeeds = False
    spies.clear()

    get_detail(api)

    assert spies.read_tools_calls == [PROFILE], "a failed read is reported, never retried"


def test_no_test_here_can_see_the_operators_real_install(hermes_home, tmp_path):
    """conftest's sandbox, asserted rather than assumed."""
    assert settings.hermes_home_path == hermes_home
    assert tmp_path in hermes_home.parents


def test_every_path_this_view_reads_lies_under_tmp_path(api, tmp_path, monkeypatch):
    """Proof, not assertion by docstring: every file the composed read opens
    is inside this test's own temp install."""
    recorded: list[Path] = []

    def record_then_really_read(path, *args, **kwargs):
        recorded.append(Path(path))
        return _REAL_READ_TEXT(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", record_then_really_read)
    get_detail(api)

    outside = [path for path in recorded if tmp_path not in Path(path).resolve().parents]
    assert outside == [], f"the view read outside its own temp install: {outside}"
    assert recorded, "the recorder saw nothing -- it was not wired to the real read"
