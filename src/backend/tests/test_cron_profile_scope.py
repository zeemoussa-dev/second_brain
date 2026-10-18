"""A named profile's cron jobs become readable (`REQ-SB-99-US-01`, `ADR-043`).

`HermesCron` has taken a `profile_id` since 2026-08-28, but
`cron_status.list_cron_jobs()` never passed one -- so `GET /hermes/cron/jobs`
has only ever listed the root/`default` profile's jobs and every named
profile's jobs were invisible in the app. This pins the additive pass-through.

What is pinned: a job's binding is the directory its `jobs.json` lives in, not
a field on `CronJob`; `default`/`""`/omitted all mean `<HERMES_HOME>` itself
(`profiles/default` exists on no install); the no-argument call returns exactly
what it returned before plus the new `scope` label; a missing `jobs.json` is
`[]`, never an exception and never a created file; and one call costs one stat,
one read and zero subprocesses (`BUG-086` is the measured precedent for a read
path that forgets what it costs).

No test here touches a real install: two use a fake client, the rest point
`settings.hermes_home_path` at their own `tmp_path`, on top of conftest's
suite-wide sandbox -- asserted, not assumed, in
`test_no_test_here_can_see_the_operators_real_install`.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main_app
from app.business.hermes import client as client_module
from app.business.hermes import cron_status
from app.config import settings
from app.hermes import HermesClient
from app.hermes.cron import CronJob

PROFILE = "adnoc-expert"


def engineered_job(job_id: str, name: str, schedule: str, last_run_at: str, last_status: str) -> CronJob:
    return CronJob(
        id=job_id, name=name, prompt="", skill="", schedule_kind="interval",
        schedule_display=schedule, enabled=True, state="scheduled",
        created_at="2026-10-01T08:00:00", next_run_at="2026-10-18T09:00:00",
        last_run_at=last_run_at, last_status=last_status, last_error=None,
        failure_streak=0, deliver="none", repeat_times=None, repeat_completed=0,
    )


ROOT_JOB = engineered_job("R1", "vault-reindex", "every 6 hours", "2026-10-18T06:00:00", "success")
PROFILE_JOB = engineered_job("A1", "adnoc-digest", "every day at 07:00", "2026-10-18T07:00:00", "failed")


def raw_job(job: CronJob) -> dict:
    """One job as it really sits in a `cron/jobs.json` on disk."""
    return {
        "id": job.id, "name": job.name, "prompt": job.prompt, "skill": job.skill,
        "schedule": {"kind": job.schedule_kind, "display": job.schedule_display},
        "enabled": job.enabled, "state": job.state, "created_at": job.created_at,
        "next_run_at": job.next_run_at, "last_run_at": job.last_run_at,
        "last_status": job.last_status, "last_error": job.last_error,
        "failure_streak": job.failure_streak, "deliver": job.deliver,
        "repeat": {"times": job.repeat_times, "completed": job.repeat_completed},
    }


class FakeCron:
    """One jobs.json per directory, keyed by the `profile_id` that resolves it.

    Every other cron call raises: listing a profile's jobs must not open the
    executions db or re-read a job it already has.
    """

    def __init__(self, jobs_by_profile_id: dict[str | None, list[CronJob]]):
        self._jobs_by_profile_id = jobs_by_profile_id
        self.profile_ids_asked: list[str | None] = []

    def list_cron_jobs(self, profile_id: str | None = None) -> list[CronJob]:
        self.profile_ids_asked.append(profile_id)
        return list(self._jobs_by_profile_id.get(profile_id, []))

    def _refuse(self, *args, **kwargs):
        raise AssertionError("listing cron jobs reached beyond the one jobs.json it needs")

    get_cron_job = list_cron_executions = get_execution_detail = _refuse


class FakeClient:
    """`cron` and nothing else -- reaching any other surface is the cost bug."""

    def __init__(self, cron: FakeCron):
        self.cron = cron

    def __getattr__(self, name: str):
        raise AssertionError(f"listing cron jobs reached client.{name}")


@pytest.fixture()
def fake_cron(monkeypatch) -> FakeCron:
    """A root jobs.json holding R1 and the profile's own holding A1."""
    cron = FakeCron({None: [ROOT_JOB], PROFILE: [PROFILE_JOB]})
    monkeypatch.setattr(client_module, "_client", FakeClient(cron))
    return cron


@pytest.fixture()
def hermes_home(monkeypatch, tmp_path) -> Path:
    """A real (tiny) Hermes install read by the real `HermesCron`."""
    monkeypatch.setattr(settings, "hermes_home_path", tmp_path)
    monkeypatch.setattr(client_module, "_client", None)
    write_jobs_json(tmp_path / "cron", [ROOT_JOB])
    return tmp_path


def write_jobs_json(cron_dir: Path, jobs: list[CronJob]) -> None:
    cron_dir.mkdir(parents=True, exist_ok=True)
    (cron_dir / "jobs.json").write_text(
        json.dumps({"jobs": [raw_job(job) for job in jobs]}), encoding="utf-8",
    )


def by_id(rows: list[dict]) -> dict[str, dict]:
    return {row["id"]: row for row in rows}


# [REQ-SB-99-US-01-AC-04]
def test_a_named_profiles_own_jobs_are_readable_at_last(fake_cron):
    rows = cron_status.list_cron_jobs(PROFILE)

    assert [row["id"] for row in rows] == ["A1"], (
        "the root's R1 must not be attributed to a named profile, and the "
        "profile's own A1 must no longer be invisible"
    )
    assert rows[0]["schedule_display"] == "every day at 07:00"
    assert rows[0]["last_run_at"] == "2026-10-18T07:00:00"
    assert rows[0]["last_status"] == "failed"
    assert fake_cron.profile_ids_asked == [PROFILE]


# [REQ-SB-99-US-01-AC-04]
def test_default_and_no_argument_both_mean_the_install_root_itself(fake_cron):
    """`profiles/default` exists on no install -- the `default` profile IS
    `<HERMES_HOME>`, so both forms must reach `HermesCron` as `None`."""
    omitted = cron_status.list_cron_jobs()
    named_default = cron_status.list_cron_jobs("default")
    empty = cron_status.list_cron_jobs("")

    assert fake_cron.profile_ids_asked == [None, None, None]
    assert omitted == named_default == empty
    assert [row["id"] for row in omitted] == ["R1"]


# [REQ-SB-99-US-01-AC-04]
def test_the_existing_callers_payload_is_unchanged_but_for_the_new_label(fake_cron):
    """`GET /hermes/cron/jobs` calls this with no argument: every field it
    already served keeps its exact value, and `scope` is the only addition."""
    rows = cron_status.list_cron_jobs()

    before_this_change = asdict(ROOT_JOB)
    assert rows == [{**before_this_change, "scope": "install"}]
    assert set(rows[0]) - set(before_this_change) == {"scope"}


# [REQ-SB-99-US-01-AC-04]
def test_the_hermes_ops_endpoint_still_sees_the_install_root_and_only_that(fake_cron):
    """The existing route is untouched by this story: it calls the function
    with no argument, so it still lists the root's jobs -- A1 does not appear
    there. Making it install-wide is `ADR-043`'s deliberate non-goal."""
    response = TestClient(main_app.app).get("/hermes/cron/jobs")

    assert response.status_code == 200
    assert response.json() == [{**asdict(ROOT_JOB), "scope": "install"}]
    assert fake_cron.profile_ids_asked == [None]


# [REQ-SB-99-US-01-AC-04]
def test_each_job_says_which_side_of_the_split_it_came_from(fake_cron):
    """Install-level jobs -- the ones that run with no `-p` -- are visible as
    such rather than attributed to a named profile."""
    assert by_id(cron_status.list_cron_jobs())["R1"]["scope"] == "install"
    assert by_id(cron_status.list_cron_jobs("default"))["R1"]["scope"] == "install"
    assert by_id(cron_status.list_cron_jobs(PROFILE))["A1"]["scope"] == "profile"


# [REQ-SB-99-US-01-AC-04]
def test_a_profile_with_no_jobs_json_reads_as_empty_and_creates_nothing(hermes_home):
    """Read-only against a real tree: a missing jobs.json is `[]`, never an
    exception, and the root's own jobs are still there afterwards."""
    assert cron_status.list_cron_jobs(PROFILE) == []
    assert not (hermes_home / "profiles").exists(), "a read created a profile directory"

    assert [row["id"] for row in cron_status.list_cron_jobs()] == ["R1"]


# [REQ-SB-99-US-01-AC-04]
def test_binding_is_the_directory_the_jobs_json_lives_in(hermes_home):
    """Against the real `HermesCron` and real files, because the binding this
    reports is structural -- `CronJob` carries no profile field (`ADR-043`)."""
    write_jobs_json(hermes_home / "profiles" / PROFILE / "cron", [PROFILE_JOB])

    assert [row["id"] for row in cron_status.list_cron_jobs(PROFILE)] == ["A1"]
    assert [row["id"] for row in cron_status.list_cron_jobs()] == ["R1"]
    assert [row["id"] for row in cron_status.list_cron_jobs("default")] == ["R1"], (
        "`default` resolved profiles/default, a path that exists on no install"
    )
    assert "scope" not in raw_job(PROFILE_JOB), "scope is this layer's label, not a stored field"


# [constraint: cost]
def test_one_call_costs_one_stat_one_read_and_no_subprocess(hermes_home, monkeypatch):
    """`BUG-086` is the measured precedent: a read path that does not know what
    it costs is how the Agents Map got to six seconds. This one opens exactly
    the single jobs.json it was asked for."""
    stats: list[str] = []
    reads: list[str] = []
    real_is_file, real_read_text = Path.is_file, Path.read_text

    def counting_is_file(self):
        stats.append(str(self))
        return real_is_file(self)

    def counting_read_text(self, *args, **kwargs):
        reads.append(str(self))
        return real_read_text(self, *args, **kwargs)

    def no_subprocess(*args, **kwargs):
        raise AssertionError("listing cron jobs spawned a subprocess")

    monkeypatch.setattr(Path, "is_file", counting_is_file)
    monkeypatch.setattr(Path, "read_text", counting_read_text)
    monkeypatch.setattr(subprocess, "run", no_subprocess)
    monkeypatch.setattr(subprocess, "Popen", no_subprocess)

    cron_status.list_cron_jobs()

    root_jobs_json = str(hermes_home / "cron" / "jobs.json")
    assert stats == [root_jobs_json]
    assert reads == [root_jobs_json]

    stats.clear()
    reads.clear()
    cron_status.list_cron_jobs(PROFILE)

    profile_jobs_json = str(hermes_home / "profiles" / PROFILE / "cron" / "jobs.json")
    assert stats == [profile_jobs_json]
    assert reads == [], "a jobs.json that does not exist must not be opened"


def test_no_test_here_can_see_the_operators_real_install(fake_cron, tmp_path_factory):
    """Stated rather than assumed: conftest's sandbox points the configured
    install root at a directory that does not exist, and the client this file
    exercises is either a fake object or one built over a `tmp_path`."""
    assert not settings.hermes_home_path.exists()
    assert not isinstance(client_module.get_client(), HermesClient)

    tmp_root = str(tmp_path_factory.getbasetemp())
    assert str(settings.hermes_home_path).startswith(tmp_root)
