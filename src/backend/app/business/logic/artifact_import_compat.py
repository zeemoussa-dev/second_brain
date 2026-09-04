"""Compatibility screening for an incoming bundle: does any Skill script in
it still resolve the App Database Folder the way that broke email capture?

Why this exists (2026-09-04). Every Hermes-side Skill script used to locate
templates, the email noise definition and the person ignore list at a
hardcoded `<vault>/.second-brain/...`. When the operator split config out of
the vault on 2026-09-03 that folder stopped holding any of it, and
`ingest_email.py` began raising for EVERY email -- 54 real messages were
consumed and silently never written. The fix was a single resolver,
`vault_manager.data_root()`, honouring SECOND_BRAIN_DATA_PATH.

The export/import placeholder machinery cannot catch a regression of this
shape on its own. It substitutes ABSOLUTE paths (`@@SECOND_BRAIN_DATA_PATH@@`
and friends), and `.second-brain` is a RELATIVE literal baked into the
script's own source -- so a bundle built before the fix passes through
substitution completely untouched and silently overwrites a corrected script
on import, reintroducing the outage with no error anywhere.

This module does not block anything. It makes the situation visible in the
import preview, where the operator can still choose to skip the artifact --
which is the whole difference between the incident and a caught regression.
"""
from __future__ import annotations

_LEGACY_DATA_DIRNAME = ".second-brain"
# The resolver a corrected script routes through. Its own fallback branch
# legitimately mentions the legacy folder name, so presence of the resolver is
# what separates "already fixed" from "still hardcoded" -- not the mere
# presence of the string.
_RESOLVER_NAME = "data_root"

_MESSAGE = (
    "Contains script(s) that resolve the App Database Folder at the old "
    "<vault>/.second-brain location instead of via vault_manager.data_root(). "
    "Importing this will overwrite the corrected version and can silently "
    "stop email capture from writing anything. Skip it unless you are sure."
)


def _script_is_stale(source: str) -> bool:
    return _LEGACY_DATA_DIRNAME in source and _RESOLVER_NAME not in source


def _stale_members(payload: dict[str, bytes], artifact_id: str) -> list[str]:
    prefix = f"skills/{artifact_id}/"
    stale: list[str] = []
    for member_path, content in payload.items():
        if not member_path.startswith(prefix) or not member_path.endswith(".py"):
            continue
        try:
            source = content.decode("utf-8")
        except UnicodeDecodeError:
            # Undecodable bytes cannot be screened, and guessing either way
            # would be worse than saying so -- a real .py that is not UTF-8 is
            # already anomalous enough to want a human look.
            stale.append(member_path)
            continue
        if _script_is_stale(source):
            stale.append(member_path)
    return stale


def flag_stale_data_paths(artifacts: list[dict], payload: dict[str, bytes]) -> list[dict]:
    """Returns `artifacts` with `stale_data_path` (bool) and, when true,
    `stale_data_path_detail` added to every entry.

    Every artifact is screened; an earlier hit never short-circuits the rest,
    matching `detect_conflicts`'s own per-artifact discipline."""
    screened: list[dict] = []
    for entry in artifacts:
        members = _stale_members(payload, entry.get("id", "")) if entry.get("kind") == "skill" else []
        if members:
            screened.append({
                **entry,
                "stale_data_path": True,
                "stale_data_path_detail": {"message": _MESSAGE, "files": sorted(members)},
            })
        else:
            screened.append({**entry, "stale_data_path": False})
    return screened
