"""Raw storage for files attached in Chat --
`<SECOND_BRAIN_DATA_PATH>/data/chat-uploads/<upload-id>/<filename>`. Zero
interpretation here: no size limit and no filename rules -- the caller hands
over a name that is already a single safe path segment.

Each upload gets its own folder, so two files with the same name never
overwrite each other, and the agent that receives the path reads exactly the
file the operator attached.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from app.config import settings
from app.obsidian.notes import long_path

_UPLOADS_FOLDER = ("data", "chat-uploads")


def save_upload(filename: str, content: bytes) -> Path:
    """Raises FileNotFoundError before setup has configured an App Database
    Folder, and OSError when the file cannot be written."""
    if settings.second_brain_data_path is None:
        raise FileNotFoundError("No App Database Folder is configured")
    folder = Path(settings.second_brain_data_path).joinpath(*_UPLOADS_FOLDER, uuid.uuid4().hex[:12])
    os.makedirs(long_path(folder))
    path = folder / filename
    with open(long_path(path), "wb") as handle:
        handle.write(content)
    return path
