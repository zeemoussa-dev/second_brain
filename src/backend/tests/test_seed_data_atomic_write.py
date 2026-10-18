"""Seed data files are written atomically: a write that fails part-way leaves
the previous content, never a half-written file, and no temporary file behind."""
from __future__ import annotations

import os

import pytest

from app.config import settings
from app.data_access import seed_data


@pytest.fixture
def data_path(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path)
    return tmp_path


def test_a_rewrite_replaces_the_content_and_leaves_no_temporary_file(data_path):
    seed_data.write_text("Plugin/Cache.json", '{"a": 1}')
    seed_data.write_text("Plugin/Cache.json", '{"a": 2}')

    assert seed_data.read_text("Plugin/Cache.json") == '{"a": 2}'
    assert os.listdir(data_path / "Plugin") == ["Cache.json"]


def test_a_write_that_fails_part_way_keeps_the_previous_content(data_path, monkeypatch):
    seed_data.write_text("Plugin/Cache.json", '{"a": 1}')

    def stopped(source, target):
        raise OSError("the backend stopped")

    monkeypatch.setattr(seed_data.os, "replace", stopped)
    with pytest.raises(OSError):
        seed_data.write_text("Plugin/Cache.json", '{"a": 2, "half": ')

    assert seed_data.read_text("Plugin/Cache.json") == '{"a": 1}'
    assert os.listdir(data_path / "Plugin") == ["Cache.json"]


def test_a_briefly_locked_file_is_replaced_once_the_lock_goes(data_path, monkeypatch):
    seed_data.write_text("Plugin/Cache.json", "old")
    real_replace, refusals = os.replace, [PermissionError("locked by OneDrive")] * 2
    monkeypatch.setattr(seed_data.time, "sleep", lambda _: None)

    def locked_twice(source, target):
        if refusals:
            raise refusals.pop()
        real_replace(source, target)

    monkeypatch.setattr(seed_data.os, "replace", locked_twice)
    seed_data.write_text("Plugin/Cache.json", "new")

    assert seed_data.read_text("Plugin/Cache.json") == "new"
