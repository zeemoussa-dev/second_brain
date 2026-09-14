"""Semantic + hybrid retrieval (REQ-SB-06).

Every test here stubs the provider. That is not only for speed: this
install's Compass subscription lists embedding models it is not entitled
to call (confirmed live 2026-09-13, HTTP 400 "You may not have a quota"),
so a test that reached the real endpoint would fail for a reason that has
nothing to do with the code under test. The provider contract itself is
pinned separately, by asserting what `request_embeddings` SENDS and how it
reports a refusal.
"""
from __future__ import annotations

import json
from array import array
from pathlib import Path

import httpx
import pytest

from app.business.core.semantic import semantic_manager as semantic_manager_module
from app.business.core.semantic.semantic_manager import (
    SemanticIndexUnavailableError,
    SemanticManager,
)
from app.business.logic import hybrid_search
from app.config import settings
from app.data_access import compass_client, semantic_store


class _StubVaultManager:
    """Stands in for the real in-memory note index, whose own rebuild
    walks a real vault on disk."""

    def __init__(self, index: dict) -> None:
        self._index = index

    def get_index(self) -> dict:
        return self._index

    def rebuild_index(self) -> dict:
        return self._index


def _entry(stem: str, path: Path, *, subject: str = "", tags: list[str] | None = None) -> dict:
    return {
        "stem": stem,
        "path": str(path),
        "frontmatter": {"subject": subject or stem, "type": "Thread"},
        "tags": tags or [],
    }


@pytest.fixture()
def store_at(tmp_path, monkeypatch):
    """Points the store at a temp App Database Folder. `settings` is a
    module-level singleton, so this must be undone per test -- monkeypatch
    handles that."""
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path / "config")
    monkeypatch.setattr(settings, "compass_embedding_model", "test-embedding-model")
    return tmp_path


@pytest.fixture()
def notes(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    paths = {}
    for stem, body in {
        "Adnoc-Pricing": "The discount schedule we agreed for the refinery programme.",
        "Masdar-Renewables": "Solar capacity planning notes for the coastal sites.",
        "Taqa-Grid": "Transmission upgrade discussion with the grid operator.",
    }.items():
        path = vault / f"{stem}.md"
        path.write_text(f"---\nsubject: {stem}\ntype: Thread\n---\n\n{body}\n", encoding="utf-8")
        paths[stem] = path
    return paths


def _fixed_vectors(mapping: dict[str, list[float]]):
    """Returns a request_embeddings stub that answers from `mapping`,
    keyed by whichever stem appears in the card text."""

    def _stub(inputs: list[str], **_kwargs) -> list[list[float]]:
        vectors = []
        for text in inputs:
            for key, vector in mapping.items():
                if key in text:
                    vectors.append(vector)
                    break
            else:
                vectors.append([0.0, 0.0, 1.0])
        return vectors

    return _stub


# -- store round trip --------------------------------------------------------


def test_store_round_trips_vectors_and_manifest(store_at):
    vectors = [array("f", [1.0, 0.0]), array("f", [0.0, 1.0])]
    manifest = {"model": "m", "dimensions": 2, "entries": [{"stem": "a"}, {"stem": "b"}]}

    semantic_store.write_store(manifest, vectors)

    assert semantic_store.store_exists()
    assert semantic_store.read_manifest()["entries"][1]["stem"] == "b"
    assert [list(v) for v in semantic_store.read_vectors(2)] == [[1.0, 0.0], [0.0, 1.0]]


def test_truncated_vector_file_reads_as_no_store(store_at):
    semantic_store.write_store({"dimensions": 4}, [array("f", [1.0, 0.0, 0.0, 0.0])])
    # A crash or sync collision mid-write leaves a partial vector behind;
    # reading it as a shorter corpus would silently drop notes.
    path = semantic_store.vectors_path()
    path.write_bytes(path.read_bytes()[:-6])

    assert semantic_store.read_vectors(4) == []


# -- build -------------------------------------------------------------------


def test_build_embeds_every_note_once(store_at, notes, monkeypatch):
    calls: list[list[str]] = []

    def _stub(inputs, **_kwargs):
        calls.append(inputs)
        return [[1.0, 0.0, 0.0] for _ in inputs]

    monkeypatch.setattr(semantic_manager_module, "request_embeddings", _stub)
    index = {stem: _entry(stem, path) for stem, path in notes.items()}

    result = SemanticManager(_StubVaultManager(index)).build()

    assert result["total_notes"] == 3
    assert result["embedded_now"] == 3
    assert result["reused"] == 0
    assert sum(len(batch) for batch in calls) == 3


def test_rebuild_reuses_vectors_for_unchanged_notes(store_at, notes, monkeypatch):
    embedded_counts: list[int] = []

    def _stub(inputs, **_kwargs):
        embedded_counts.append(len(inputs))
        return [[1.0, 0.0, 0.0] for _ in inputs]

    monkeypatch.setattr(semantic_manager_module, "request_embeddings", _stub)
    index = {stem: _entry(stem, path) for stem, path in notes.items()}
    manager = SemanticManager(_StubVaultManager(index))
    manager.build()

    notes["Adnoc-Pricing"].write_text(
        "---\nsubject: Adnoc-Pricing\ntype: Thread\n---\n\nRewritten body.\n", encoding="utf-8",
    )
    second = manager.build()

    # Only the note whose content actually changed is re-embedded -- the
    # whole point of fingerprinting rather than trusting mtimes.
    assert second["embedded_now"] == 1
    assert second["reused"] == 2
    assert embedded_counts == [3, 1]


def test_build_drops_notes_that_left_the_vault(store_at, notes, monkeypatch):
    monkeypatch.setattr(
        semantic_manager_module, "request_embeddings",
        lambda inputs, **_k: [[1.0, 0.0, 0.0] for _ in inputs],
    )
    index = {stem: _entry(stem, path) for stem, path in notes.items()}
    manager = SemanticManager(_StubVaultManager(index))
    manager.build()

    index.pop("Taqa-Grid")
    manager.build()

    stored_stems = {entry["stem"] for entry in semantic_store.read_manifest()["entries"]}
    assert stored_stems == {"Adnoc-Pricing", "Masdar-Renewables"}
    assert len(semantic_store.read_vectors(3)) == 2


def test_model_change_invalidates_every_stored_vector(store_at, notes, monkeypatch):
    monkeypatch.setattr(
        semantic_manager_module, "request_embeddings",
        lambda inputs, **_k: [[1.0, 0.0, 0.0] for _ in inputs],
    )
    index = {stem: _entry(stem, path) for stem, path in notes.items()}
    manager = SemanticManager(_StubVaultManager(index))
    manager.build()

    monkeypatch.setattr(settings, "compass_embedding_model", "a-different-model")
    result = manager.build()

    # Mixing two embedding spaces in one file would rank notes by numbers
    # that share no meaning, and nothing would raise.
    assert result["reused"] == 0
    assert result["embedded_now"] == 3


# -- search ------------------------------------------------------------------


def test_search_ranks_by_cosine_similarity(store_at, notes, monkeypatch):
    monkeypatch.setattr(semantic_manager_module, "request_embeddings", _fixed_vectors({
        "Adnoc-Pricing": [1.0, 0.0, 0.0],
        "Masdar-Renewables": [0.0, 1.0, 0.0],
        "Taqa-Grid": [0.7, 0.7, 0.0],
        "what did we agree on price": [1.0, 0.0, 0.0],
    }))
    index = {stem: _entry(stem, path) for stem, path in notes.items()}
    manager = SemanticManager(_StubVaultManager(index))
    manager.build()

    results = manager.search("what did we agree on price")["results"]

    assert [r["stem"] for r in results] == ["Adnoc-Pricing", "Taqa-Grid", "Masdar-Renewables"]
    assert results[0]["score"] == pytest.approx(1.0, abs=1e-4)
    assert results[0]["rank"] == 1


def test_search_without_a_built_index_raises_rebuildable_error(store_at, notes, monkeypatch):
    monkeypatch.setattr(
        semantic_manager_module, "request_embeddings", lambda inputs, **_k: [[1.0, 0.0]],
    )
    manager = SemanticManager(_StubVaultManager({}))

    with pytest.raises(SemanticIndexUnavailableError):
        manager.search("anything")


def test_search_detects_a_dimension_mismatch(store_at, notes, monkeypatch):
    monkeypatch.setattr(
        semantic_manager_module, "request_embeddings",
        lambda inputs, **_k: [[1.0, 0.0, 0.0] for _ in inputs],
    )
    index = {stem: _entry(stem, path) for stem, path in notes.items()}
    manager = SemanticManager(_StubVaultManager(index))
    manager.build()

    monkeypatch.setattr(
        semantic_manager_module, "request_embeddings", lambda inputs, **_k: [[1.0] * 8],
    )
    with pytest.raises(SemanticIndexUnavailableError):
        manager.search("anything")


# -- hybrid fusion -----------------------------------------------------------


class _StubSearcher:
    def __init__(self, stems: list[str]) -> None:
        self._stems = stems

    def search(self, query: str, limit: int = 20) -> dict:
        return {"query": query, "results": [
            {"stem": stem, "title": stem, "kind": "Thread", "tags": [], "rank": rank}
            for rank, stem in enumerate(self._stems[:limit], start=1)
        ]}


def test_hybrid_prefers_what_both_rankers_agree_on(monkeypatch):
    monkeypatch.setattr(
        hybrid_search, "VaultManager", lambda: _StubSearcher(["keyword-only", "agreed"]),
    )
    monkeypatch.setattr(
        hybrid_search, "SemanticManager", lambda: _StubSearcher(["semantic-only", "agreed"]),
    )

    results = hybrid_search.search("q")["results"]

    # "agreed" is second in BOTH lists and first in neither; RRF still puts
    # it on top, which is the whole reason to fuse rather than concatenate.
    assert results[0]["stem"] == "agreed"
    assert results[0]["matched_by"] == {"keyword": 2, "semantic": 2}


def test_hybrid_degrades_to_keyword_when_semantic_is_unavailable(monkeypatch):
    class _Unavailable:
        def search(self, query, limit=20):
            raise SemanticIndexUnavailableError("not built")

    monkeypatch.setattr(hybrid_search, "VaultManager", lambda: _StubSearcher(["a", "b"]))
    monkeypatch.setattr(hybrid_search, "SemanticManager", _Unavailable)

    response = hybrid_search.search("q")

    assert [r["stem"] for r in response["results"]] == ["a", "b"]
    assert response["semantic_available"] is False
    assert "not built" in response["semantic_error"]


# -- provider contract -------------------------------------------------------


def test_embeddings_url_is_derived_from_the_chat_url(monkeypatch):
    monkeypatch.setattr(settings, "compass_embeddings_url", "")
    monkeypatch.setattr(settings, "compass_base_url", "https://api.example.ai/v1/chat/completions")

    assert settings.compass_embeddings_endpoint == "https://api.example.ai/v1/embeddings"


def test_request_embeddings_sends_model_and_dimensions(monkeypatch):
    sent: dict = {}

    def _fake_post(url, json=None, headers=None, timeout=None):
        sent["url"] = url
        sent["json"] = json
        return httpx.Response(200, json={"data": [{"index": 0, "embedding": [0.1, 0.2]}]})

    monkeypatch.setattr(compass_client.httpx, "post", _fake_post)
    monkeypatch.setattr(settings, "compass_api_key", "k")
    monkeypatch.setattr(settings, "compass_base_url", "https://api.example.ai/v1/chat/completions")
    monkeypatch.setattr(settings, "compass_embedding_model", "text-embedding-3-large")
    monkeypatch.setattr(settings, "compass_embedding_dimensions", 1024)

    vectors = compass_client.request_embeddings(["hello"])

    assert sent["url"] == "https://api.example.ai/v1/embeddings"
    assert sent["json"]["model"] == "text-embedding-3-large"
    assert sent["json"]["dimensions"] == 1024
    assert vectors == [[0.1, 0.2]]


def test_request_embeddings_reorders_by_provider_index(monkeypatch):
    def _fake_post(url, json=None, headers=None, timeout=None):
        # Deliberately out of order: attaching each note to its
        # neighbour's meaning is invisible to any ranking assertion.
        return httpx.Response(200, json={"data": [
            {"index": 1, "embedding": [2.0]},
            {"index": 0, "embedding": [1.0]},
        ]})

    monkeypatch.setattr(compass_client.httpx, "post", _fake_post)
    monkeypatch.setattr(settings, "compass_api_key", "k")
    monkeypatch.setattr(settings, "compass_base_url", "https://api.example.ai/v1/chat/completions")

    assert compass_client.request_embeddings(["first", "second"]) == [[1.0], [2.0]]


def test_quota_refusal_surfaces_the_providers_own_message(monkeypatch):
    real_refusal = json.dumps({"error": {"message": "You may not have a quota or access to use this model"}})

    def _fake_post(url, json=None, headers=None, timeout=None):
        return httpx.Response(400, text=real_refusal)

    monkeypatch.setattr(compass_client.httpx, "post", _fake_post)
    monkeypatch.setattr(settings, "compass_api_key", "k")
    monkeypatch.setattr(settings, "compass_base_url", "https://api.example.ai/v1/chat/completions")

    with pytest.raises(compass_client.CompassEmbeddingsUnavailableError) as caught:
        compass_client.request_embeddings(["hello"])

    assert "quota" in str(caught.value)
