"""Publishing a plugin into the Marketplace (`ADR-022`, `REQ-SB-91` Phase 4b).

The two slow gates -- a plugin's own tests and building its screens inside the
frontend -- are passed in as stubs here; each has its own refusal test. Every
plugin repository is written into a temporary folder, and so is the Marketplace.
"""
import importlib.util
import json
import textwrap
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


publish_plugin = _load("publish_plugin")
check_plugin_imports = _load("check_plugin_imports")

_GOOD_BACKEND = '''
from fastapi import APIRouter

from app import plugin_api


def register(api):
    api.register_router(APIRouter())
'''

_GOOD_UI = '''
import { useState } from 'react';
import type { PluginUi } from '../../pluginHost/types';
import { apiFetch } from '../../pluginHost/api';
import { DayPage } from './screens/DayPage';

const ui: PluginUi = { routes: [{ path: '/my-day', component: DayPage }] };
export default ui;
'''


@pytest.fixture()
def marketplace(tmp_path):
    return tmp_path / "marketplace"


@pytest.fixture()
def repo(tmp_path):
    root = tmp_path / "sb-plugins-my-day"
    (root / "backend" / "tests").mkdir(parents=True)
    (root / "backend" / "__pycache__").mkdir()
    (root / "ui" / "screens").mkdir(parents=True)
    write_manifest(root)
    (root / "backend" / "__init__.py").write_text(textwrap.dedent(_GOOD_BACKEND), encoding="utf-8")
    (root / "backend" / "tests" / "test_inside.py").write_text("def test_x():\n    pass\n", encoding="utf-8")
    (root / "backend" / "__pycache__" / "junk.pyc").write_bytes(b"\x00")
    (root / "ui" / "index.tsx").write_text(textwrap.dedent(_GOOD_UI), encoding="utf-8")
    (root / "ui" / "screens" / "DayPage.tsx").write_text(
        "import { Link } from 'react-router';\nexport function DayPage() { return null; }\n", encoding="utf-8")
    return root


def write_manifest(root: Path, **overrides) -> None:
    manifest = {
        "id": "my-day", "name": "My Day", "version": "1.0.0",
        "framework_api": publish_plugin.host_framework_api(), "requires": ["graph|outlook"],
    }
    manifest.update(overrides)
    (root / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")


def passing(*_args):
    return None


def publish(repo, marketplace, **kwargs):
    kwargs.setdefault("test_runner", passing)
    kwargs.setdefault("screen_builder", passing)
    return publish_plugin.publish(repo, marketplace_root=marketplace, **kwargs)


def refusal(repo, marketplace, **kwargs) -> list[str]:
    with pytest.raises(publish_plugin.PublishRefused) as refused:
        publish(repo, marketplace, **kwargs)
    return refused.value.problems


# -- publishing ------------------------------------------------------------------


def test_the_host_framework_api_is_read_from_plugin_api():
    from app import plugin_api

    assert publish_plugin.host_framework_api() == plugin_api.FRAMEWORK_API


def test_a_valid_plugin_is_published_without_its_tests_or_build_output(repo, marketplace):
    result = publish(repo, marketplace)

    package = marketplace / "my-day" / "1.0.0"
    assert result["published"] is True
    assert (package / "plugin.json").is_file()
    assert (package / "backend" / "__init__.py").is_file()
    assert (package / "ui" / "screens" / "DayPage.tsx").is_file()
    assert not (package / "backend" / "tests").exists()
    assert not (package / "backend" / "__pycache__").exists()


def test_a_dry_run_checks_everything_and_publishes_nothing(repo, marketplace):
    result = publish(repo, marketplace, dry_run=True)

    assert result["dry_run"] is True
    assert not marketplace.exists()


# -- refusals ----------------------------------------------------------------------


@pytest.mark.parametrize("overrides, expected", [
    ({"framework_api": 999}, "framework API"),
    ({"id": "My Day"}, "not a valid plugin id"),
    ({"version": "1.0"}, "not x.y.z"),
])
def test_a_bad_manifest_is_refused(repo, marketplace, overrides, expected):
    write_manifest(repo, **overrides)

    problems = refusal(repo, marketplace)

    assert any(expected in problem for problem in problems)
    assert not marketplace.exists()


def test_a_published_version_is_never_overwritten(repo, marketplace):
    publish(repo, marketplace)

    problems = refusal(repo, marketplace)

    assert any("never overwritten" in problem for problem in problems)


def test_a_backend_reaching_past_the_plugin_api_is_refused(repo, marketplace):
    (repo / "backend" / "leak.py").write_text("from app.business.my_day import summary\n", encoding="utf-8")

    problems = refusal(repo, marketplace)

    assert any("app.business.my_day" in problem for problem in problems)


def test_screens_reaching_into_framework_internals_are_refused(repo, marketplace):
    (repo / "ui" / "screens" / "Leak.tsx").write_text(
        "import { MarketplaceCard } from '../../../features/settings/MarketplaceCard';\n", encoding="utf-8")

    problems = refusal(repo, marketplace)

    assert any("features/settings/MarketplaceCard" in problem for problem in problems)


def test_the_cheap_problems_are_all_reported_together(repo, marketplace):
    (repo / "backend" / "leak.py").write_text("import app.config\n", encoding="utf-8")
    (repo / "ui" / "Leak.tsx").write_text("import _ from 'lodash';\n", encoding="utf-8")

    problems = refusal(repo, marketplace)

    assert len(problems) == 2


def test_failing_plugin_tests_stop_publishing(repo, marketplace):
    problems = refusal(repo, marketplace, test_runner=lambda _repo: "the plugin's own tests fail")

    assert problems == ["the plugin's own tests fail"]
    assert not marketplace.exists()


def test_screens_that_do_not_build_stop_publishing(repo, marketplace):
    problems = refusal(repo, marketplace, screen_builder=lambda _repo, _id: "the screens do not build")

    assert problems == ["the screens do not build"]
    assert not marketplace.exists()


# -- the screen import rule ----------------------------------------------------------


def write_ui(tmp_path: Path, relative: str, source: str) -> Path:
    ui = tmp_path / "ui"
    path = ui / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return ui


def test_screens_may_import_their_own_files_the_host_contract_and_react(tmp_path):
    ui = write_ui(tmp_path, "deep/nested/Screen.tsx", textwrap.dedent('''
        import React, { useEffect } from 'react';
        import { Link } from 'react-router';
        import type { PluginUi } from '../../../../pluginHost/types';
        import { apiFetch } from '../../../../pluginHost/api';
        import { helper } from '../../helper';
        import './Screen.css';
        const lazy = import('./Other');
    '''))

    assert check_plugin_imports.check_plugin_ui(ui, "my-day") == []


def test_screens_may_not_escape_into_another_plugin_or_the_framework(tmp_path):
    ui = write_ui(tmp_path, "index.tsx", textwrap.dedent('''
        import { thing } from '../entities/index';
        import {
          apiFetch,
        } from '../../api/client';
        export { x } from 'date-fns';
    '''))

    violations = check_plugin_imports.check_plugin_ui(ui, "my-day")

    assert len(violations) == 3
