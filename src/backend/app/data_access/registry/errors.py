"""RegistryLoadError -- the fail-loud signal for a broken data/ file
(REQ-SB-80, operator: "Fail Loud so I can fix or remove"). Carries the
exact file path and a plain-English reason so BootScreen can show the
operator precisely what to fix, rather than a generic "boot failed"."""
from __future__ import annotations

from pathlib import Path


class RegistryLoadError(Exception):
    def __init__(self, file: Path, message: str):
        self.file = file
        self.message = message
        super().__init__(f"{file}: {message}")
