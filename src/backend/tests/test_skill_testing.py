"""skill_testing.py -- how an agent repository's Skill tests find the framework (BUG-069).

Moved Skills' tests counted parent folders to reach the framework, true only inside
the framework's own tree, or borrowed the copies deployed to Hermes."""
import json
import sys

import pytest

import skill_testing


@pytest.fixture()
def layout(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "path", list(sys.path))

    framework = tmp_path / "second_brain"
    (framework / skill_testing._SHARED_MANAGERS).mkdir(parents=True)
    (framework / skill_testing._SHARED_MANAGERS / "vault_manager.py").write_text("", encoding="utf-8")
    masters = framework / skill_testing._MASTER_TEMPLATES
    for template_id in ("thread", "note"):
        (masters / template_id).mkdir(parents=True)
        (masters / template_id / "Template.json").write_text(json.dumps({"id": template_id}), encoding="utf-8")
    for version in ("1.0.0", "1.10.0", "1.2.0"):
        package = framework / skill_testing._MARKETPLACE / "entities" / version / "templates" / "customer"
        package.mkdir(parents=True)
        (package / "Template.json").write_text(json.dumps({"id": "customer", "v": version}), encoding="utf-8")

    repository = tmp_path / "sb-agent"
    (repository / ".git").mkdir(parents=True)
    (repository / "data" / "managers").mkdir(parents=True)
    (repository / "data" / "managers" / "company_index.py").write_text("", encoding="utf-8")
    (repository / "data" / "Templates" / "note").mkdir(parents=True)
    (repository / "data" / "Templates" / "note" / "Template.json").write_text('{"id": "note", "own": true}', encoding="utf-8")
    scripts = repository / "data" / "Tools" / "vault" / "Skills" / "some-skill" / "scripts"
    scripts.mkdir(parents=True)
    conftest = scripts / "conftest.py"
    conftest.write_text("", encoding="utf-8")
    return {"framework": framework, "repository": repository, "scripts": scripts, "conftest": conftest}


def configure(layout):
    return skill_testing.configure(layout["conftest"], framework=layout["framework"])


def test_the_skill_its_repository_and_the_framework_engines_go_on_the_path_in_that_order(layout):
    configure(layout)

    assert sys.path[:3] == [
        str(layout["scripts"]),
        str(layout["repository"] / "data" / "managers"),
        str(layout["framework"] / skill_testing._SHARED_MANAGERS),
    ]


def test_configuring_twice_does_not_duplicate_path_entries(layout):
    configure(layout)
    configure(layout)

    assert sys.path.count(str(layout["scripts"])) == 1


def test_the_repository_is_found_by_its_git_folder_not_by_counting(layout):
    assert configure(layout).repository == layout["repository"]


def test_engines_come_from_the_repository_first_then_the_framework_source(layout):
    paths = configure(layout)

    assert paths.shared_engine("company_index.py") == layout["repository"] / "data" / "managers" / "company_index.py"
    assert paths.shared_engine("vault_manager.py") == layout["framework"] / skill_testing._SHARED_MANAGERS / "vault_manager.py"
    with pytest.raises(FileNotFoundError, match="missing.py"):
        paths.shared_engine("missing.py")


def test_a_template_the_repository_ships_wins_over_the_framework_master(layout):
    assert json.loads(configure(layout).master_template("note").read_text(encoding="utf-8"))["own"] is True


def test_a_framework_master_is_found_in_the_framework_source(layout):
    assert configure(layout).master_template("thread") == (
        layout["framework"] / skill_testing._MASTER_TEMPLATES / "thread" / "Template.json")


def test_a_template_that_moved_into_a_plugin_comes_from_its_newest_package(layout):
    template = configure(layout).master_template("customer")

    assert json.loads(template.read_text(encoding="utf-8"))["v"] == "1.10.0"


def test_a_template_nobody_ships_fails_loudly_rather_than_skipping(layout):
    with pytest.raises(FileNotFoundError, match="'nowhere'"):
        configure(layout).master_template("nowhere")


def test_a_framework_skill_is_found_in_the_catalog_source(layout):
    skill = layout["framework"] / skill_testing._SKILL_CATALOG / "vault" / "summarize-and-tag-files"
    (skill / "scripts").mkdir(parents=True)
    paths = configure(layout)

    assert paths.framework_skill("summarize-and-tag-files") == skill / "scripts"
    assert paths.framework_skill("not-shipped") is None


def test_the_real_framework_resolves_its_own_shared_engine_and_masters():
    paths = skill_testing.SkillTestPaths(skill_testing.FRAMEWORK_ROOT, None, skill_testing.FRAMEWORK_ROOT)

    assert paths.shared_engine("vault_manager.py").is_file()
    assert paths.master_template("thread").is_file()
    assert paths.master_template("customer").is_file()
    assert (paths.framework_skill("summarize-and-tag-files") / "retag_files_from_summaries.py").is_file()
