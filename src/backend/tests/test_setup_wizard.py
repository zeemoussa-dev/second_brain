"""REQ-SB-89 -- the first-run setup wizard.

The behaviour that matters most here is the one that used to be impossible:
a fresh install with no .env must still IMPORT, still serve, and still be
able to describe what it is missing. Before this, `app.config` raised a
pydantic ValidationError at module scope and nothing below ever ran.
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.business import setup_wizard, system_settings
from app.config import REQUIRED_FOR_STARTUP, settings
from app.main import app

client = TestClient(app)


@pytest.fixture
def unconfigured(monkeypatch):
    """Puts the real settings object into the state a fresh install has."""
    for field in REQUIRED_FOR_STARTUP:
        monkeypatch.setattr(settings, field, None if field == "vault_path" else "")
    return settings


def test_missing_settings_are_reported_not_raised(unconfigured) -> None:
    assert unconfigured.setup_required is True
    assert set(unconfigured.missing_required_settings) == set(REQUIRED_FOR_STARTUP)


def test_a_configured_install_is_not_in_setup_mode() -> None:
    # The real .env this repo runs against -- guards against the wizard
    # hijacking an install that is already working.
    assert settings.setup_required is False


def test_setup_status_is_served_while_unconfigured(unconfigured) -> None:
    response = client.get("/setup/status")

    assert response.status_code == 200
    body = response.json()
    assert body["setup_required"] is True
    assert [step["id"] for step in body["steps"]] == ["vault", "compass", "hermes", "storage"]
    # Every field that blocks startup must actually appear in some step, or
    # the wizard cannot possibly clear setup mode.
    offered = {field["key"] for step in body["steps"] for field in step["fields"]}
    assert set(REQUIRED_FOR_STARTUP) <= offered


def test_other_routes_are_refused_while_unconfigured(unconfigured) -> None:
    response = client.get("/vault/notes")

    assert response.status_code == 503
    assert response.json()["setup_required"] is True


def test_health_and_boot_stay_open_while_unconfigured(unconfigured) -> None:
    assert client.get("/health").status_code == 200
    assert client.get("/boot-status").status_code == 200


def test_compass_url_missing_the_endpoint_is_rejected() -> None:
    # data_access/compass_client.py POSTs to this URL verbatim, so a bare
    # host 404s at first real use rather than at setup.
    assert system_settings.validate_candidate("compass_base_url", "https://api.core42.ai")["ok"] is False
    assert system_settings.validate_candidate(
        "compass_base_url", "https://api.core42.ai/v1/chat/completions"
    )["ok"] is True


def test_vault_folder_check_rejects_a_path_that_does_not_exist(tmp_path: Path) -> None:
    assert system_settings.validate_candidate("vault_path", str(tmp_path / "nope"))["ok"] is False
    assert system_settings.validate_candidate("vault_path", str(tmp_path))["ok"] is True


def test_secret_is_masked_on_read_and_never_written_back(monkeypatch, tmp_path: Path) -> None:
    """A UI that submits a whole form round-trips the mask for any secret the
    operator did not touch -- writing that through would replace a working
    key with bullet characters."""
    monkeypatch.setattr(settings, "compass_api_key", "a-real-key")
    assert system_settings._display_value("compass_api_key") == system_settings.SECRET_MASK

    env_file = tmp_path / ".env"
    env_file.write_text("COMPASS_API_KEY=a-real-key\n", encoding="utf-8")
    monkeypatch.setattr(system_settings, "_ENV_PATH", env_file)

    result = system_settings.update_system_settings({"compass_api_key": system_settings.SECRET_MASK})

    assert result["restart_required"] is False
    assert "a-real-key" in env_file.read_text(encoding="utf-8")
    assert system_settings.SECRET_MASK not in env_file.read_text(encoding="utf-8")


def test_a_real_value_does_reach_the_env_file(monkeypatch, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("SELF_EMAIL=old@example.com\n", encoding="utf-8")
    monkeypatch.setattr(system_settings, "_ENV_PATH", env_file)

    system_settings.update_system_settings({"self_email": "new@example.com"})

    assert "SELF_EMAIL=new@example.com" in env_file.read_text(encoding="utf-8")


def test_hermes_health_reports_a_missing_install_without_raising(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "hermes_home_path", tmp_path / "not-installed")

    health = setup_wizard.get_hermes_health()

    assert health["all_ok"] is False
    assert health["read_only"] is True
    assert {check["key"] for check in health["checks"]} == {
        "installed",
        "gateway",
        "profiles",
        "skills",
        "cron",
        "vault_path",
    }


def _fake_hermes_home(tmp_path: Path, *, vault: str | None, profiles: dict[str, str] | None = None) -> Path:
    home = tmp_path / "hermes"
    (home / "bin").mkdir(parents=True)
    (home / "bin" / "hermes.exe").write_text("", encoding="utf-8")
    if vault is not None:
        (home / ".env").write_text(
            f"# Hermes env\nOBSIDIAN_VAULT_PATH={vault}\nOTHER_KEY=keep-me\n", encoding="utf-8"
        )
    for name, profile_vault in (profiles or {}).items():
        profile = home / "profiles" / name
        profile.mkdir(parents=True)
        (profile / ".env").write_text(f"OBSIDIAN_VAULT_PATH={profile_vault}\n", encoding="utf-8")
    return home


def test_vault_path_is_written_into_hermes_env(monkeypatch, tmp_path: Path) -> None:
    home = _fake_hermes_home(tmp_path, vault=r"C:\old\vault")
    monkeypatch.setattr(settings, "hermes_home_path", home)

    result = setup_wizard.sync_paths_to_hermes(r"C:\new\vault")

    assert result["ok"] is True
    assert result["restart_required"] is True
    written = (home / ".env").read_text(encoding="utf-8")
    assert r"OBSIDIAN_VAULT_PATH=C:\new\vault" in written
    # Unrelated keys and comments must survive -- this is a live Hermes file.
    assert "OTHER_KEY=keep-me" in written
    assert "# Hermes env" in written


def test_a_fresh_install_syncs_exactly_one_file(monkeypatch, tmp_path: Path) -> None:
    """The operator's own point: a new setup has no profiles yet, so this is
    one file, and later `hermes profile create --clone` copies it onward."""
    home = _fake_hermes_home(tmp_path, vault=None)
    monkeypatch.setattr(settings, "hermes_home_path", home)

    result = setup_wizard.sync_paths_to_hermes(r"C:\new\vault")

    assert result["files_written"] == 1
    assert r"OBSIDIAN_VAULT_PATH=C:\new\vault" in (home / ".env").read_text(encoding="utf-8")


def test_existing_profiles_are_not_left_pinned_to_the_old_vault(monkeypatch, tmp_path: Path) -> None:
    home = _fake_hermes_home(
        tmp_path, vault=r"C:\old\vault", profiles={"opp-manager": r"C:\old\vault", "research-agent": r"C:\old\vault"}
    )
    monkeypatch.setattr(settings, "hermes_home_path", home)

    result = setup_wizard.sync_paths_to_hermes(r"C:\new\vault")

    assert result["files_written"] == 3
    for name in ("opp-manager", "research-agent"):
        assert r"OBSIDIAN_VAULT_PATH=C:\new\vault" in (
            home / "profiles" / name / ".env"
        ).read_text(encoding="utf-8")


def test_sync_reports_rather_than_raises_when_hermes_is_absent(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "hermes_home_path", tmp_path / "no-hermes-here")

    result = setup_wizard.sync_paths_to_hermes(r"C:\new\vault")

    assert result["ok"] is False
    assert result["files_written"] == 0


def test_trailing_separator_is_not_reported_as_drift(monkeypatch, tmp_path: Path) -> None:
    """Second Brain's VAULT_PATH conventionally ends in a separator and
    Hermes' does not -- the same folder must not read as a mismatch."""
    home = _fake_hermes_home(tmp_path, vault=r"C:\the\vault")
    monkeypatch.setattr(settings, "hermes_home_path", home)
    monkeypatch.setattr(settings, "vault_path", Path(r"C:\the\vault" + "\\"))

    agrees = setup_wizard._check_vault_path_agrees(home)

    assert agrees["ok"] is True


def test_drift_is_reported_on_the_hermes_step(monkeypatch, tmp_path: Path) -> None:
    home = _fake_hermes_home(tmp_path, vault=r"C:\somewhere\else")
    monkeypatch.setattr(settings, "hermes_home_path", home)
    monkeypatch.setattr(settings, "vault_path", Path(r"C:\the\vault"))

    agrees = setup_wizard._check_vault_path_agrees(home)

    assert agrees["ok"] is False
    assert "somewhere" in agrees["detail"]


def test_data_path_is_synced_alongside_the_vault_path(monkeypatch, tmp_path: Path) -> None:
    """The Hermes-side Skill scripts resolve templates and their own state
    under SECOND_BRAIN_DATA_PATH. Before it was synced they fell back to the
    historical <vault>/.second-brain and silently dropped every email once
    the operator split config out of the vault."""
    home = _fake_hermes_home(tmp_path, vault=r"C:\old\vault")
    monkeypatch.setattr(settings, "hermes_home_path", home)

    setup_wizard.sync_paths_to_hermes(r"C:\new\vault", r"C:\somewhere\config")

    written = (home / ".env").read_text(encoding="utf-8")
    assert r"OBSIDIAN_VAULT_PATH=C:\new\vault" in written
    assert r"SECOND_BRAIN_DATA_PATH=C:\somewhere\config" in written


def test_data_path_falls_back_to_the_configured_setting(monkeypatch, tmp_path: Path) -> None:
    home = _fake_hermes_home(tmp_path, vault=r"C:\old\vault")
    monkeypatch.setattr(settings, "hermes_home_path", home)
    monkeypatch.setattr(settings, "second_brain_data_path", Path(r"C:\configured\data"))

    setup_wizard.sync_paths_to_hermes(r"C:\new\vault")

    assert r"SECOND_BRAIN_DATA_PATH=C:\configured\data" in (home / ".env").read_text(encoding="utf-8")
