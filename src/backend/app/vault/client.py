"""VaultClient -- the "Vault Manager" Business Logic talks to for any
Template-driven write. Zero logic of its own: constructed with a
Template (already fetched by the Template Manager, app/data_access/
templates/) plus the vault root, it just forwards each call to
vault_manager.py's real, already-working engine. Short-lived and scoped
to one job -- construct, do the work, dispose -- unlike
app/business/hermes/client.py's persistent singleton, because a
DIFFERENT Template is a genuinely different job, not a stable
connection to reconfigure.

Root/whole-vault access (listing a folder, scanning the whole vault) is
NOT this class's job -- that's app/obsidian/'s plain functions, called
directly with vault_path, no construction needed. VaultClient exists
only for the "I have a Template, I want to instantiate/modify it" path.
"""
from __future__ import annotations

from pathlib import Path

from app.vault import vault_manager


class VaultClient:
    def __init__(self, vault_path: Path, template: dict):
        self._vault_path = Path(vault_path)
        self._template = template
        self._disposed = False

    def __enter__(self) -> "VaultClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.dispose()

    def dispose(self) -> None:
        """No held resource actually needs releasing today -- every
        vault_manager.py call is a self-contained, synchronous file
        operation, not a connection or handle kept open across calls.
        This exists for the explicit lifecycle boundary (a disposed
        client refuses further calls), not because there's a real
        resource leak risk yet."""
        self._disposed = True

    def _check_alive(self) -> None:
        if self._disposed:
            raise RuntimeError("this VaultClient has already been disposed")

    def create_structure(
        self, note_name: str, title: str, *, note_id: str | None = None,
        frontmatter: dict | None = None, sections: dict[str, str] | None = None,
        folder_date: str | None = None,
    ) -> dict:
        self._check_alive()
        return vault_manager.create(
            self._vault_path, self._template, note_name, title,
            note_id=note_id, frontmatter=frontmatter, sections=sections, folder_date=folder_date,
        )

    def write_file(self, path: Path, frontmatter: dict, body: str) -> None:
        """Raw, non-templated write at an already-resolved path -- for
        when the caller has already decided exactly where and what to
        write (e.g. a companion note for an uploaded file) rather than
        letting the Template's own naming/collision rules decide."""
        self._check_alive()
        vault_manager.write_note(Path(path), frontmatter, body)

    def write_section(self, note_id: str, section: str, content: str, *, mode: str = "replace",
                       note_name: str | None = None, title: str | None = None, frontmatter: dict | None = None) -> dict:
        self._check_alive()
        return vault_manager.modify_section(
            self._vault_path, self._template, note_id, section, content, mode,
            note_name=note_name, title=title, frontmatter=frontmatter,
        )

    def update_property(self, note_path: Path, key: str, value) -> dict:
        self._check_alive()
        return vault_manager.update(self._vault_path, Path(note_path), frontmatter={key: value})

    def find(self, by: str, value: str, note_name: str | None = None):
        self._check_alive()
        return vault_manager.find(self._vault_path, by, value, note_name)

    def get_last_modified_files(self, note_name: str, limit: int | None = None) -> list[Path]:
        """Every real note under this Template's own note_name folder,
        most recently modified first."""
        self._check_alive()
        paths = vault_manager.find_in_folder(self._vault_path, note_name)
        paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return paths[:limit] if limit is not None else paths
