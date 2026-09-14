"""SemanticManager -- the sole gateway onto the semantic index (the same
"one real gateway" rule Section/Agent/Pipeline/Vault/Index Manager each
follow). Owns what a note MEANS for retrieval purposes: which text stands
for a note, when a stored vector is stale, and how a query is ranked
against the corpus. Raw file I/O lives in `data_access/semantic_store.py`
and the provider call in `data_access/compass_client.py` -- this file
holds neither.

**Why one vector per note, not per chunk.** REQ-SB-06 names chunking, and
chunking is the right answer for a corpus of long documents. This vault is
not that: 2,014 notes that are already distillations (Thread summaries,
Meeting notes, Customer hubs), where the whole note is a single topic.
One vector per note keeps the store at ~8MB, the rebuild at one pass, and
the result list at "notes", which is the unit the UI, the wikilink graph
and every Skill already speak. Chunking earns its complexity when single
notes grow long enough that their middle is unfindable -- `_semantic_card`
below is the seam where that change would land.

**Why brute force, not a vector database.** At 2,014 notes a full cosine
scan is a few million multiply-adds -- single-digit milliseconds, no
index structure, no service to run, no staleness of its own. An ANN index
(Qdrant et al) starts paying for itself around 1e5-1e6 vectors; adopting
one here would add an install dependency and a second source of truth to
keep in sync for a speed-up smaller than the HTTP round trip that
delivers the query. Evaluated and deferred 2026-09-13 with the trigger
conditions recorded in ADR-020.
"""
from __future__ import annotations

import hashlib
import operator
from array import array
from datetime import datetime, timezone

from app.business.core.vault.vault_manager import VaultManager
from app.config import settings
from app.data_access import semantic_store
from app.data_access import vault_writer
from app.data_access.compass_client import (
    CompassClientError,
    CompassEmbeddingsUnavailableError,
    request_embeddings,
)

# One request per batch of notes. 64 keeps a single failed request cheap to
# retry and stays well inside the provider's own per-request input limits;
# the whole vault is ~32 requests at this size.
_EMBED_BATCH_SIZE = 64
# Bounds the body text that reaches the provider. A Thread summary or
# Meeting note is comfortably inside this; the tail of an unusually long
# note contributes nothing to a whole-note vector anyway, since averaging
# more text only pulls the vector toward the corpus mean.
_MAX_BODY_CHARACTERS = 4000
_DEFAULT_SEARCH_LIMIT = 20
# Frontmatter fields that carry real meaning rather than bookkeeping.
# Everything else (ids, timestamps, provenance) is noise in an embedding.
_MEANINGFUL_FRONTMATTER_FIELDS = (
    "subject", "title", "name", "description", "summary",
    "customer", "partner", "type", "status", "aliases",
)


class SemanticIndexUnavailableError(Exception):
    """No usable semantic index -- never built, or built against a model/
    dimension pair the current configuration no longer matches. Distinct
    from a provider failure: this one is fixed by a rebuild, not by a
    subscription."""


class SemanticManager:
    def __init__(self, vault_manager: VaultManager | None = None) -> None:
        self._vault_manager = vault_manager or VaultManager()

    # -- what a note means -------------------------------------------------

    def _semantic_card(self, entry: dict) -> str:
        """The text that stands for one note when it is embedded. Built
        from the note's meaningful frontmatter plus a bounded head of its
        body, rather than the raw file: frontmatter carries the note's
        identity (who it is about, what kind of thing it is) in a form the
        body often never restates, and the raw file's provenance blocks
        and ids would otherwise dominate a short note's vector."""
        frontmatter = entry.get("frontmatter") or {}
        lines: list[str] = []

        for field in _MEANINGFUL_FRONTMATTER_FIELDS:
            value = frontmatter.get(field)
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value if item)
            if isinstance(value, str) and value.strip():
                lines.append(f"{field}: {value.strip()}")

        tags = entry.get("tags") or []
        if tags:
            lines.append("tags: " + ", ".join(str(tag) for tag in tags))

        header = "\n".join(lines)
        body = self._read_body(entry)
        return f"{entry.get('stem', '')}\n{header}\n\n{body}".strip()

    def _read_body(self, entry: dict) -> str:
        try:
            _, body = vault_writer.read_note(entry["path"])
        except (OSError, KeyError):
            return ""
        return body[:_MAX_BODY_CHARACTERS]

    def _card_fingerprint(self, card: str) -> str:
        """Content hash, not mtime: OneDrive rewrites mtimes on sync, and
        re-embedding 2,014 unchanged notes because a folder synced would
        cost real money against the provider's quota for no change in
        meaning."""
        return hashlib.sha256(card.encode("utf-8")).hexdigest()

    # -- build -------------------------------------------------------------

    def build(self, *, force: bool = False) -> dict:
        """Embeds every note whose card changed since the last build (or
        every note when `force`), reusing stored vectors for the rest.

        A note that has vanished from the vault drops out of the store by
        construction: the new manifest is assembled from the CURRENT index,
        never patched into the old one.
        """
        index = self._vault_manager.get_index()
        if not index:
            index = self._vault_manager.rebuild_index()

        reusable = {} if force else self._load_reusable_vectors()

        entries: list[dict] = []
        vectors: list[array] = []
        pending_positions: list[int] = []
        pending_cards: list[str] = []

        for stem in sorted(index):
            entry = index[stem]
            card = self._semantic_card(entry)
            fingerprint = self._card_fingerprint(card)
            entries.append({"stem": stem, "path": str(entry.get("path", "")), "fingerprint": fingerprint})

            stored = reusable.get(stem)
            if stored is not None and stored["fingerprint"] == fingerprint:
                vectors.append(stored["vector"])
                continue
            # Placeholder keeps positions aligned with `entries` while the
            # real vector is still unembedded -- filled in below.
            vectors.append(array("f"))
            pending_positions.append(len(vectors) - 1)
            pending_cards.append(card)

        for batch_start in range(0, len(pending_cards), _EMBED_BATCH_SIZE):
            batch_cards = pending_cards[batch_start:batch_start + _EMBED_BATCH_SIZE]
            batch_positions = pending_positions[batch_start:batch_start + _EMBED_BATCH_SIZE]
            for position, vector in zip(batch_positions, request_embeddings(batch_cards)):
                vectors[position] = _normalise(vector)

        dimensions = len(vectors[0]) if vectors else 0
        manifest = {
            "model": settings.compass_embedding_model,
            "dimensions": dimensions,
            "built_at": datetime.now(timezone.utc).isoformat(),
            "entries": entries,
        }
        semantic_store.write_store(manifest, vectors)
        return {
            "built_at": manifest["built_at"],
            "model": manifest["model"],
            "dimensions": dimensions,
            "total_notes": len(entries),
            "embedded_now": len(pending_cards),
            "reused": len(entries) - len(pending_cards),
        }

    def _load_reusable_vectors(self) -> dict[str, dict]:
        """Stored vectors still valid for reuse, keyed by stem. A store
        built against a different model or dimension count is discarded
        wholesale -- mixing two embedding spaces in one file would rank
        notes against each other by numbers that share no meaning, which
        no exception would ever surface."""
        manifest = semantic_store.read_manifest()
        if manifest is None:
            return {}
        if manifest.get("model") != settings.compass_embedding_model:
            return {}
        dimensions = manifest.get("dimensions") or 0
        vectors = semantic_store.read_vectors(dimensions)
        entries = manifest.get("entries") or []
        if len(vectors) != len(entries):
            return {}
        return {
            entry["stem"]: {"fingerprint": entry.get("fingerprint"), "vector": vector}
            for entry, vector in zip(entries, vectors)
            if isinstance(entry, dict) and entry.get("stem")
        }

    # -- search ------------------------------------------------------------

    def search(self, query: str, limit: int = _DEFAULT_SEARCH_LIMIT) -> dict:
        """Cosine ranking of the whole corpus against `query`. Every stored
        vector is already unit-normalised, so cosine similarity IS the dot
        product here -- no per-query normalisation pass over 2,000 vectors.
        Scores run -1..1; results are not thresholded, because a vector
        search always returns its nearest neighbours and deciding "near
        enough" belongs to the caller (hybrid fusion, or a human reading a
        ranked list)."""
        if not query.strip():
            return {"query": query, "results": []}

        manifest = semantic_store.read_manifest()
        if manifest is None:
            raise SemanticIndexUnavailableError(
                "The semantic index has not been built yet -- POST /vault-search/semantic/rebuild"
            )
        dimensions = manifest.get("dimensions") or 0
        vectors = semantic_store.read_vectors(dimensions)
        entries = manifest.get("entries") or []
        if not vectors or len(vectors) != len(entries):
            raise SemanticIndexUnavailableError(
                "The semantic index on disk is unreadable or out of step with its manifest -- rebuild it"
            )

        query_vector = _normalise(request_embeddings([query])[0])
        if len(query_vector) != dimensions:
            raise SemanticIndexUnavailableError(
                f"The stored index has {dimensions} dimensions but the configured model returns "
                f"{len(query_vector)} -- rebuild it"
            )

        scored = [
            (sum(map(operator.mul, query_vector, vector)), entry)
            for vector, entry in zip(vectors, entries)
        ]
        scored.sort(key=lambda pair: (-pair[0], pair[1].get("stem", "")))

        index = self._vault_manager.get_index()
        results = []
        for rank, (score, entry) in enumerate(scored[:limit], start=1):
            stem = entry.get("stem", "")
            indexed = index.get(stem)
            results.append({
                "stem": stem,
                "title": (indexed or {}).get("frontmatter", {}).get("subject") or stem,
                "kind": (indexed or {}).get("frontmatter", {}).get("type", "Unknown"),
                "tags": (indexed or {}).get("tags", []),
                "rank": rank,
                "score": round(score, 4),
            })
        return {"query": query, "results": results}

    # -- status ------------------------------------------------------------

    def get_status(self) -> dict:
        """Honest, never-raising snapshot for the UI and for `/status`
        style callers: whether a store exists, what it was built from, and
        whether the provider will actually answer. `embeddings_available`
        is the question the operator most needs answered on this install,
        where the subscription lists embedding models it cannot call."""
        manifest = semantic_store.read_manifest() or {}
        provider_error: str | None = None
        try:
            request_embeddings(["ping"])
            embeddings_available = True
        except (CompassEmbeddingsUnavailableError, CompassClientError) as exc:
            embeddings_available = False
            provider_error = str(exc)

        return {
            "built": bool(manifest),
            "built_at": manifest.get("built_at"),
            "model": manifest.get("model") or settings.compass_embedding_model,
            "dimensions": manifest.get("dimensions") or settings.compass_embedding_dimensions,
            "total_notes": len(manifest.get("entries") or []),
            "embeddings_available": embeddings_available,
            "provider_error": provider_error,
        }


def _normalise(vector) -> array:
    """Unit-normalises once, at write time, so every later comparison is a
    bare dot product. A zero vector (an empty note, or a provider quirk) is
    left as-is rather than divided by zero -- it then scores 0 against
    every query, which is the honest answer for a note with no content."""
    values = array("f", (float(value) for value in vector))
    magnitude = sum(value * value for value in values) ** 0.5
    if magnitude == 0:
        return values
    return array("f", (value / magnitude for value in values))
