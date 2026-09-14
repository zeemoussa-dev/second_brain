"""A Pipeline must resolve the Hermes job it names.

It did not, for any Pipeline linked by the job id `hermes cron create` prints:
the manager matched `job.name == cron_job_id`, and looked only in the named
profile's store while `hermes cron create` writes to the shared one. The Agents
Map showed every pipeline with no schedule, no last run and no status -- which
made the live delta pipelines look like abandoned one-off runs (2026-09-11).
"""
from app.business.core.pipelines import pipeline_manager as pm
from app.hermes.cron import CronJob


def job(job_id: str, name: str, *, schedule: str = "every 30m") -> CronJob:
    return CronJob(
        id=job_id, name=name, prompt="", skill="vault/summarize-and-tag-files",
        schedule_kind="interval", schedule_display=schedule, enabled=True,
        state="scheduled", created_at="", next_run_at="2026-09-11T14:30:00+04:00",
        last_run_at=None, last_status="ok", last_error=None, failure_streak=0,
        deliver="local", repeat_times=None, repeat_completed=0,
    )


class _Cron:
    def __init__(self, stores: dict):
        self._stores = stores

    def list_cron_jobs(self, profile_id=None):
        return self._stores.get(profile_id, [])


class _Client:
    def __init__(self, stores: dict):
        self.cron = _Cron(stores)


def lookup(monkeypatch, stores: dict, cron_job_id: str, cron_profile_id=None) -> dict:
    monkeypatch.setattr(pm, "get_client", lambda: _Client(stores))
    manager = pm.PipelineManager.__new__(pm.PipelineManager)
    return manager._cron_status(cron_job_id, cron_profile_id)


def test_a_job_is_found_by_the_id_hermes_printed(monkeypatch):
    status = lookup(monkeypatch, {None: [job("d78ad501da2c", "SB file enrichment")]},
                    "d78ad501da2c")
    assert status["cron_schedule"] == "every 30m"
    assert status["cron_enabled"] is True


def test_a_job_is_still_found_by_name_for_older_definitions(monkeypatch):
    status = lookup(monkeypatch, {None: [job("30df78b1b719", "email-delta-capture")]},
                    "email-delta-capture")
    assert status["cron_schedule"] == "every 30m"


def test_a_named_profile_without_the_job_falls_back_to_the_shared_store(monkeypatch):
    """`hermes cron create` always writes to the shared store."""
    stores = {"files-manager": [], None: [job("d78ad501da2c", "SB file enrichment")]}
    status = lookup(monkeypatch, stores, "d78ad501da2c", "files-manager")
    assert status["cron_schedule"] == "every 30m"


def test_a_job_under_its_own_profile_is_preferred(monkeypatch):
    stores = {"meeting-prep-agent": [job("aaa", "meeting-capture-recurring", schedule="every 60m")],
              None: [job("bbb", "meeting-capture-recurring", schedule="every 5m")]}
    status = lookup(monkeypatch, stores, "meeting-capture-recurring", "meeting-prep-agent")
    assert status["cron_schedule"] == "every 60m"


def test_an_unknown_job_resolves_to_nothing(monkeypatch):
    assert lookup(monkeypatch, {None: [job("d78ad501da2c", "x")]}, "no-such-job") == {}
