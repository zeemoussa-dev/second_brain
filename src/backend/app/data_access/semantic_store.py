"""Raw I/O for the semantic index's own on-disk store (REQ-SB-06) --
no shape validation, no defaults applied, no business meaning attached
(the 2026-08-28 layering rule: Managers understand Entities, Data
Access understands stores).

Two files under `<App Database Folder>/semantic/`:

  vectors.f32   every embedding, back to back, little-endian float32
  manifest.json {model, dimensions, built_at, entries: [...]}

Vectors live in a flat binary file rather than inside the manifest
because JSON floats are ~12x larger and parse ~100x slower: at this
vault's scale (2,014 notes x 1024 dims) the binary form is ~8MB and
loads in milliseconds, while the JSON equivalent would be ~100MB. The
`array` module handles both directions in stdlib alone, which keeps
this file deployable beside the Hermes-side payload engines if a future
pass ever needs it there.

Entry N of `entries` owns vector N of the file -- that positional pairing
IS the format. Anything that rewrites one MUST rewrite the other in the
same call, which is why `write_store()` takes both and there is no
function that writes either half alone.
"""
from __future__ import annotations

import json
import sys
from array import array
from pathlib import Path

from app.config import settings

_STORE_DIRECTORY_NAME = "semantic"
_VECTORS_FILENAME = "vectors.f32"
_MANIFEST_FILENAME = "manifest.json"


def _store_directory() -> Path:
    return Path(settings.second_brain_data_path) / _STORE_DIRECTORY_NAME


def manifest_path() -> Path:
    return _store_directory() / _MANIFEST_FILENAME


def vectors_path() -> Path:
    return _store_directory() / _VECTORS_FILENAME


def store_exists() -> bool:
    return manifest_path().is_file() and vectors_path().is_file()


def read_manifest() -> dict | None:
    """None for "no store on disk yet" and for a store too corrupt to
    parse -- both mean the same thing to every caller (rebuild it), and
    neither is an error worth raising through a read."""
    try:
        return json.loads(manifest_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def read_vectors(dimensions: int) -> list[array]:
    """One `array('f')` per stored vector, sliced back out of the flat
    file by `dimensions`. Returns [] when the file is missing or its
    length is not a whole number of vectors -- a truncated write (a
    crash mid-rebuild, a OneDrive sync collision) must read as "no
    usable store", never as a silently shorter corpus."""
    if dimensions <= 0:
        return []
    flat = array("f")
    try:
        with vectors_path().open("rb") as handle:
            flat.frombytes(handle.read())
    except OSError:
        return []
    except ValueError:
        # A file truncated mid-float is not a whole number of 4-byte items
        # at all, so frombytes refuses it before the whole-vector check
        # below ever runs. Same verdict: no usable store.
        return []
    if sys.byteorder == "big":
        # Written little-endian on every platform so a store stays
        # readable if the vault is ever synced to a big-endian host.
        flat.byteswap()
    if not flat or len(flat) % dimensions != 0:
        return []
    return [flat[start:start + dimensions] for start in range(0, len(flat), dimensions)]


def write_store(manifest: dict, vectors: list[array]) -> None:
    """Writes both halves of the store, vectors first: a manifest that
    names more entries than the vector file holds is the one combination
    `read_vectors` cannot detect (it only checks whole-vector lengths),
    so the file that is safe to be ahead is written first."""
    directory = _store_directory()
    directory.mkdir(parents=True, exist_ok=True)

    flat = array("f")
    for vector in vectors:
        flat.extend(vector)
    if sys.byteorder == "big":
        flat.byteswap()
    vectors_path().write_bytes(flat.tobytes())

    manifest_path().write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8",
    )


def delete_store() -> bool:
    """True when something was actually removed -- False for an
    already-absent store is the same {"deleted": False} posture every
    other data_access delete in this app already takes."""
    removed = False
    for path in (vectors_path(), manifest_path()):
        try:
            path.unlink()
            removed = True
        except OSError:
            continue
    return removed
