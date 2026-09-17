"""Shared managers deployed onto Hermes' PYTHONPATH: the framework's own, and
those an agent repository ships in the install's config folder
(`<config>/data/managers/`, e.g. sb-pss-agent's `company_index.py`)."""
import pytest

from app.config import settings
from app.data_access import skills as skills_data


@pytest.fixture()
def install(tmp_path, monkeypatch):
    config = tmp_path / "config"
    hermes_home = tmp_path / "hermes"
    monkeypatch.setattr(settings, "second_brain_data_path", config)
    return {"config": config, "hermes_home": hermes_home, "managers": config / "data" / "managers"}


def ship(install, name, content="VALUE = 1\n"):
    install["managers"].mkdir(parents=True, exist_ok=True)
    (install["managers"] / name).write_text(content, encoding="utf-8")


def framework_managers():
    return sorted(p.name for p in skills_data.managers_root().glob("*.py")
                  if p.name != "conftest.py" and not p.name.startswith("test_"))


def test_the_framework_managers_are_deployed_and_company_index_is_not_one_of_them(install):
    result = skills_data.deploy_shared_managers(install["hermes_home"])

    assert result == {"written": framework_managers(), "refused": []}
    assert "vault_manager.py" in result["written"]
    assert "company_index.py" not in result["written"]


def test_an_install_ships_its_own_managers_beside_the_frameworks(install):
    ship(install, "company_index.py", "COMPANIES = True\n")

    result = skills_data.deploy_shared_managers(install["hermes_home"])

    deployed = install["hermes_home"] / "managers" / "company_index.py"
    assert "company_index.py" in result["written"]
    assert deployed.read_text(encoding="utf-8") == "COMPANIES = True\n"


def test_an_install_manager_never_replaces_a_framework_manager(install):
    ship(install, "vault_manager.py", "BROKEN = True\n")

    result = skills_data.deploy_shared_managers(install["hermes_home"])

    assert result["refused"] == ["vault_manager.py"]
    framework_copy = (skills_data.managers_root() / "vault_manager.py").read_text(encoding="utf-8")
    assert (install["hermes_home"] / "managers" / "vault_manager.py").read_text(encoding="utf-8") == framework_copy


def test_an_installs_test_scaffolding_is_not_deployed(install):
    ship(install, "conftest.py")
    ship(install, "test_company_index.py")

    result = skills_data.deploy_shared_managers(install["hermes_home"])

    assert "conftest.py" not in result["written"] and "test_company_index.py" not in result["written"]
    assert not (install["hermes_home"] / "managers" / "conftest.py").exists()


def test_before_setup_only_the_framework_managers_are_deployed(install, monkeypatch):
    monkeypatch.setattr(settings, "second_brain_data_path", None)

    assert skills_data.deploy_shared_managers(install["hermes_home"]) == {"written": framework_managers(), "refused": []}
