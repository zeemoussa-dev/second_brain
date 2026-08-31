"""Real `.sbd` archive writer -- a plain zip file, no manifest (`REQ-SB-
86-US-02-T02`, `ADR-016`'s own explicit divergence from `sbf_archive.py`'s
always-writes-`manifest.json` shape: real vault DATA has no import reader
to design a manifest for).

Pure I/O, zero business decisions made here -- mirrors `sbf_archive.py`'s
own "zero business interpretation" discipline: which files belong in the
export, their archive-member paths, and the flat-collision-disambiguation
naming are all decided by the caller (`vault_export.build_export`), never
here.
"""
from __future__ import annotations

import zipfile


def write_archive(output_path: str, members: dict[str, str]) -> None:
    """Writes a real zip at `output_path`. `members` maps each real
    archive-member path (already computed by the caller per the flat/
    hierarchy + collision-disambiguation rules) to its real source file
    path on disk -- raw bytes copied verbatim, one member per entry. No
    `manifest.json`, no other metadata (`ADR-016`)."""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for member_path, source_path in members.items():
            archive.write(source_path, arcname=member_path)
