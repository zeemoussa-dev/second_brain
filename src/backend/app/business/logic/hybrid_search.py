"""Hybrid retrieval -- fuses VaultManager's keyword ranking (BM25,
ADR-026) with SemanticManager's embedding ranking (REQ-SB-06) into one
result list. Cross-Manager composition, so it lives in business/logic
rather than inside either Manager (CLAUDE.md's own module layout).

**Why Reciprocal Rank Fusion rather than blending the scores.** A BM25
score is an unbounded term-frequency sum; a cosine similarity is bounded
-1..1. They share no unit, so any weighted sum of the two needs a
normalisation constant that is really a hidden tuning parameter, and it
drifts the moment the corpus or the model changes. RRF throws the scores
away and keeps only each result's RANK in its own list, which is the part
both rankers agree on the meaning of. A note that both rankers like
outranks one that only a single ranker loves -- which is exactly the
behaviour that makes hybrid search better than either half.

**Why keyword search still runs when semantic is available.** Embeddings
are weakest on the queries this vault gets most: an exact account name, a
tag, a person's surname, a project code. BM25 is unbeatable on those.
Semantic covers the complementary case (a described concept whose words
appear nowhere in the note). Dropping either half loses a class of query.
"""
from __future__ import annotations

from app.business.core.semantic.semantic_manager import (
    SemanticIndexUnavailableError,
    SemanticManager,
)
from app.business.core.vault.vault_manager import VaultManager
from app.data_access.compass_client import CompassClientError

# Standard RRF damping. 60 is the value from the original TREC work and the
# one every mainstream implementation ships; it flattens the difference
# between ranks 1 and 2 enough that a single ranker cannot dominate the
# fused list on its own confidence alone.
_RANK_FUSION_DAMPING = 60
_DEFAULT_SEARCH_LIMIT = 20
# Each half is asked for more than the caller wants, so a note ranked 30th
# by keywords and 3rd by meaning can still surface in a top-20 fused list.
_PER_RANKER_DEPTH_MULTIPLIER = 3


def search(query: str, limit: int = _DEFAULT_SEARCH_LIMIT) -> dict:
    """Fused keyword+semantic results, newest rank first.

    Degrades on purpose: if the semantic half is unavailable (never built,
    or the subscription cannot call the embedding model) the keyword half
    is returned alone, with `semantic_available: false` and the real reason
    in `semantic_error`. A search box that silently returns nothing because
    a provider quota lapsed would look like an empty vault.
    """
    depth = max(limit * _PER_RANKER_DEPTH_MULTIPLIER, limit)
    keyword_results = VaultManager().search(query, limit=depth).get("results", [])

    semantic_results: list[dict] = []
    semantic_error: str | None = None
    try:
        semantic_results = SemanticManager().search(query, limit=depth).get("results", [])
    except (SemanticIndexUnavailableError, CompassClientError) as exc:
        semantic_error = str(exc)

    fused_scores: dict[str, float] = {}
    summaries_by_stem: dict[str, dict] = {}
    contributions: dict[str, dict] = {}

    for source_name, results in (("keyword", keyword_results), ("semantic", semantic_results)):
        for result in results:
            stem = result.get("stem")
            if not stem:
                continue
            rank = result.get("rank") or (results.index(result) + 1)
            fused_scores[stem] = fused_scores.get(stem, 0.0) + 1.0 / (_RANK_FUSION_DAMPING + rank)
            summaries_by_stem.setdefault(stem, {
                "stem": stem,
                "title": result.get("title", stem),
                "kind": result.get("kind", "Unknown"),
                "tags": result.get("tags", []),
            })
            contributions.setdefault(stem, {})[source_name] = rank

    ranked_stems = sorted(fused_scores, key=lambda stem: (-fused_scores[stem], stem))[:limit]
    results = [
        {
            **summaries_by_stem[stem],
            "rank": rank,
            "score": round(fused_scores[stem], 6),
            "matched_by": contributions[stem],
        }
        for rank, stem in enumerate(ranked_stems, start=1)
    ]
    return {
        "query": query,
        "results": results,
        "semantic_available": semantic_error is None,
        "semantic_error": semantic_error,
    }
