"""Real `.sbf` archive I/O -- a plain zip file (ADR-013). Writer half
(`REQ-SB-85-US-02-T04`) and reader half (`REQ-SB-85-US-03-T01`) share
this one module/format (both stories deliberately share one format/
module, per ADR-013's own "designed once, not independently per story"
framing).

Pure I/O, zero business decisions made here -- mirrors `data_access/*`'s
own "zero business interpretation" discipline, even though this lives in
`business/logic/` per ADR-013's own explicit "never a 5th Manager"
framing: the writer/reader pair is shared infrastructure composed by
`artifact_export.py`/the import orchestrator, not an entity gateway of
its own.
"""
from __future__ import annotations

import json
import zipfile

_REQUIRED_MANIFEST_KEYS = ("format_version", "generated_at", "artifacts", "secret_scan")


class MalformedBundleError(Exception):
    """Raised for every real `.sbf` structural-validity failure a reader
    can hit -- not a genuine zip, missing/unparsable `manifest.json`, or a
    manifest missing a required top-level key. Never raised for a
    `format_version` mismatch alone (ADR-013's own forward-compat
    extension point -- a caller's own business decision, not a structural
    defect)."""


def write_archive(output_path: str, manifest: dict, payload: dict[str, bytes]) -> None:
    """Writes a real zip at `output_path`: `manifest.json` (the dict,
    JSON-serialized) plus every `payload` key as its own real archive
    member path (e.g. `"skills/create-companies-partners/SKILL.md"`,
    `"agents/compass-expert/profile.tar.gz"`), content = the raw bytes
    value. Makes no decision about what belongs in `payload` -- that is
    entirely the caller's (`artifact_export.commit_export`) job."""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        for member_path, content in payload.items():
            archive.writestr(member_path, content)


def read_archive(archive_path: str) -> tuple[dict, dict[str, bytes]]:
    """Parses a real `.sbf` at `archive_path` into `(manifest_dict,
    payload_bytes_dict)` -- pure parsing, no deployment, no conflict
    detection, no write of any kind, never touches any real Manager or the
    target machine's own current state. Every validation happens BEFORE
    any byte is returned to the caller -- a caller either gets a fully-
    parsed, structurally-valid result or a `MalformedBundleError`, never
    something in between (the story's own "never partially trusts" hard
    boundary)."""
    try:
        archive = zipfile.ZipFile(archive_path, "r")
    except zipfile.BadZipFile as exc:
        raise MalformedBundleError(f"{archive_path!r} is not a valid zip archive") from exc

    with archive:
        try:
            manifest_raw = archive.read("manifest.json")
        except KeyError as exc:
            raise MalformedBundleError(f"{archive_path!r} has no manifest.json member") from exc

        try:
            manifest = json.loads(manifest_raw)
        except json.JSONDecodeError as exc:
            raise MalformedBundleError(f"{archive_path!r}'s manifest.json is not valid JSON") from exc

        for required_key in _REQUIRED_MANIFEST_KEYS:
            if required_key not in manifest:
                raise MalformedBundleError(
                    f"{archive_path!r}'s manifest.json is missing required key {required_key!r}"
                )

        payload: dict[str, bytes] = {}
        for info in archive.infolist():
            if info.filename == "manifest.json" or info.is_dir():
                continue
            payload[info.filename] = archive.read(info.filename)

    return manifest, payload
