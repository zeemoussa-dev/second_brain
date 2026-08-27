"""Temporary, non-vault raw-byte upload storage (ADR-034) -- the first
extension of the .second-brain/ flat-file state convention
(app/data_access/vault_writer.py's own state store) to raw bytes rather
than JSON. One file per upload, named with a generated id to avoid
collisions (mirrors this project's own standing filename-uniqueness
Constraint, MEMORY.md), deleted once summarized/handed off or on
validation rejection. Deliberately does not import vault_writer -- this
boundary is siblings with it (both under settings.second_brain_data_path),
not layered on top of it; vault_writer.py owns JSON state, this module
owns binary blobs, both compute their own subdirectory under the same
app-database root (System settings page, 2026-08-27 -- independent of
settings.vault_path since then).
"""
from __future__ import annotations

import uuid
from pathlib import Path

import pypdf

from app.config import settings

ACCEPTED_EXTENSIONS = {".pdf", ".txt", ".md"}
MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB (REQ-SB-28-US-01 Constraints)

def _uploads_dir() -> Path:
    path = settings.second_brain_data_path / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _upload_path(upload_id: str, filename: str) -> Path:
    ext = Path(filename).suffix.lower()
    return _uploads_dir() / f"{upload_id}{ext}"


def validate_upload(filename: str, size_bytes: int) -> str | None:
    """Returns None if the upload is acceptable, else a clear, honest,
    user-facing rejection message -- distinguishes an unsupported file
    TYPE (Scenario 7/AC-07 -- e.g. an image) from exceeding the SIZE cap
    (Scenario 8/AC-08), never a single generic message conflating both."""
    ext = Path(filename).suffix.lower()
    if ext not in ACCEPTED_EXTENSIONS:
        return (
            f"'{ext or filename}' files aren't supported yet -- only PDF "
            "(.pdf), plain text (.txt), and Markdown (.md) files can be "
            "summarized today."
        )
    if size_bytes > MAX_UPLOAD_SIZE_BYTES:
        size_mb = size_bytes / (1024 * 1024)
        return f"That file is too large ({size_mb:.1f} MB) -- the limit is 20 MB."
    return None


def save_upload(filename: str, content: bytes) -> str:
    """Stores content under a freshly generated upload_id + the original
    extension; returns the upload_id. Caller must have already confirmed
    validate_upload(filename, len(content)) is None -- this function does
    not re-validate."""
    upload_id = str(uuid.uuid4())
    _upload_path(upload_id, filename).write_bytes(content)
    return upload_id


def extract_text_content(upload_id: str, filename: str) -> str:
    """Reads the stored upload back as plain text -- .txt/.md decoded
    directly, .pdf extracted page-by-page via pypdf. Raises ValueError if
    extraction produces no usable text (e.g. a scanned/image-only PDF
    with no embedded text layer) -- the caller (T04) surfaces this
    honestly, mirroring Scenario 9's "never a fabricated summary"
    posture; this function itself never fabricates placeholder text."""
    path = _upload_path(upload_id, filename)
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        reader = pypdf.PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    else:
        text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        raise ValueError("No extractable text content found in this file.")
    return text


def delete_upload(upload_id: str, filename: str) -> None:
    """Idempotent cleanup -- a no-op if the file is already gone."""
    _upload_path(upload_id, filename).unlink(missing_ok=True)
