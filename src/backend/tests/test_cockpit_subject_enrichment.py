"""Cockpit asks subject enrichers instead of importing My Day (`BUG-063`,
`REQ-SB-91` Phase 3). Cockpit is a framework component: nothing here may make
it know a business concept or depend on a plugin.
"""
import ast
from pathlib import Path

import pytest

from app.business.core.plugins import plugin_manager as plugin_manager_module
from app.business.logic import cockpit_view

_THREAD = {
    "stem": "2026-09-14 Pricing call",
    "frontmatter": {"type": "Thread", "subject": "Pricing call"},
    "tags": ["partner/g42", "customer/adnoc"],
}
_MEETING_WITH_ITS_OWN_CUSTOMER = {
    "stem": "2026-09-14 Quarterly review",
    "frontmatter": {"type": "Meeting", "customer": "Taqa"},
    "tags": ["customer/adnoc"],
}


def _always(fields):
    return lambda subject_kind, frontmatter, tags: dict(fields)


@pytest.fixture()
def enrichers(monkeypatch):
    """A Cockpit whose sources are stubbed, with no enrichers registered."""
    index = {entry["stem"]: entry for entry in (_THREAD, _MEETING_WITH_ITS_OWN_CUSTOMER)}
    monkeypatch.setattr(cockpit_view._vault_manager, "get_index", lambda: index)
    monkeypatch.setattr(cockpit_view.people, "resolve_people_chips", lambda kind, stem: [])
    monkeypatch.setattr(cockpit_view.documents, "list_documents", lambda stem: [])
    # get_thread persists recommended agents on first read; a test must never write.
    monkeypatch.setattr(cockpit_view.chat_store, "get_thread", lambda kind, stem: {"messages": []})
    registered: list = []
    monkeypatch.setattr(plugin_manager_module, "_builtin_subject_enrichers", [])
    monkeypatch.setattr(plugin_manager_module, "_plugin_subject_enrichers", registered)
    return registered


def test_without_enrichers_the_subject_is_the_note_itself(enrichers):
    view = cockpit_view.build_cockpit_view("email", _THREAD["stem"])

    assert view["subject"] == _THREAD["frontmatter"]


def test_an_enricher_fills_a_field_the_note_leaves_empty(enrichers):
    enrichers.append(_always({"customer": "Adnoc"}))

    subject = cockpit_view.build_cockpit_view("email", _THREAD["stem"])["subject"]

    assert subject["customer"] == "Adnoc"


def test_an_enricher_never_overrides_what_the_note_says(enrichers):
    enrichers.append(_always({"customer": "Adnoc"}))

    subject = cockpit_view.build_cockpit_view("meeting", _MEETING_WITH_ITS_OWN_CUSTOMER["stem"])["subject"]

    assert subject["customer"] == "Taqa"


def test_a_failing_or_malformed_enricher_is_skipped_and_the_rest_still_apply(enrichers):
    def broken(subject_kind, frontmatter, tags):
        raise RuntimeError("a plugin bug")

    enrichers.extend([broken, lambda kind, frontmatter, tags: ["not", "a", "dict"], _always({"customer": "Adnoc"})])

    subject = cockpit_view.build_cockpit_view("email", _THREAD["stem"])["subject"]

    assert subject["customer"] == "Adnoc"


def test_an_enricher_is_told_the_subject_kind_and_the_note_tags(enrichers):
    seen = []
    enrichers.append(lambda kind, frontmatter, tags: seen.append((kind, tags)) or {})

    cockpit_view.build_cockpit_view("email", _THREAD["stem"])

    assert seen == [("email", ["partner/g42", "customer/adnoc"])]


def test_cockpit_no_longer_imports_my_day():
    tree = ast.parse(Path(cockpit_view.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.update(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)

    assert not [name for name in imported if "my_day" in name]
