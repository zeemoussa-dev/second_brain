"""IndexManager -- the sole gateway onto Index data (mirrors Section/
Agent/Pipeline/Vault/Template Manager's own "one real gateway" rule). An
Index is a real, user-defined, scoped vault index: which Work/ folders,
which tags, how deep, where the built output lands, and a real Hermes
cron job (created via HermesCli's own `hermes cron create --script
--no-agent`, verified live 2026-08-28 against the real installed CLI)
that rebuilds it on a real schedule.

Mechanism, confirmed live before building this (2026-08-28, a real
disposable cron job, immediately removed): a `--no-agent --script` job
gets ZERO argv and ZERO env passthrough -- a bare `python <script>`
invocation, nothing else. This is why the deployed per-Index script
(`_render_stub`) can't take parameters directly; it bakes in only its
own INDEX_ID plus the app's current DATA_PATH/VAULT_PATH, and reads its
own real Index.json at run time for folders/tags/depth/storage_path --
so updating those fields alone needs no script redeployment.

The actual build engine is `index_builder_lib.py`, which lives beside
this file in `scripts/` -- a generalization of the existing, single,
global `build_vault_index.py`'s own logic (folders/tags/depth become
real parameters instead of "every folder, unlimited depth, no tag
filter"). Deployed as a real file copy (never hand-duplicated) into
whichever profile's own scripts/ dir owns this Index's cron job,
alongside a copy of vault_manager.py for its read_note() sibling import.

That `scripts/` folder is BACKEND-OWNED payload (operator, 2026-09-06):
code this app ships to Hermes and never imports itself. It used to be
sourced from the vault-index Skill's own scripts/ folder under
Hermes-Provisioning/, which is normally held outside the checkout --
so Index creation raised on any install without it.

Raw I/O (2026-08-28 layering correction) lives entirely in
`data_access/indexes.py` -- this file holds zero raw file calls, only
entity-shaping, cron orchestration, and the deployed script's own text
composition (deciding WHAT the script says is business logic; writing
it to disk is not).
"""
from __future__ import annotations

import ast
import re
from datetime import datetime, timezone

from app.business.core.index.index import Index
from app.business.hermes.client import get_client
from app.config import settings
from app.data_access import indexes as indexes_data
from app.obsidian.tags import tag_slug


class IndexCronCreationError(Exception):
    pass


class IndexNotFoundError(Exception):
    pass


# Placeholders are SCREAMING_CASE between double underscores, which keeps
# them distinguishable from Python's own lowercase dunders -- the template
# legitimately contains `__file__`.
_PLACEHOLDER_PATTERN = re.compile(r"__[A-Z][A-Z0-9_]*__")


class IndexRunnerTemplateError(Exception):
    """The runner template rendered with placeholders still in it --
    deploying that would put an unparseable script behind a real cron
    job, which fails silently until someone reads the job's runs."""
    pass


class IndexManager:
    def _cron_status(self, cron_job_id: str | None, cron_profile_id: str | None) -> dict:
        if cron_job_id is None:
            return {}
        job = get_client().cron.get_cron_job(cron_job_id, cron_profile_id)
        if job is None:
            return {}
        return {
            "cron_enabled": job.enabled,
            "cron_schedule_display": job.schedule_display,
            "cron_last_run_at": job.last_run_at,
            "cron_next_run_at": job.next_run_at,
            "cron_last_status": job.last_status,
        }

    def _to_index(self, index_id: str, data: dict) -> Index:
        cron_job_id = data.get("cron_job_id")
        cron_profile_id = data.get("cron_profile_id")
        return Index(
            id=index_id, name=data.get("name") or index_id,
            folders=list(data.get("folders") or []),
            tags=list(data.get("tags") or []),
            depth=data.get("depth"),
            storage_path=data.get("storage_path", ""),
            schedule=data.get("schedule", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at"),
            cron_profile_id=cron_profile_id,
            cron_job_id=cron_job_id,
            **self._cron_status(cron_job_id, cron_profile_id),
        )

    def get_all(self) -> list[Index]:
        indexes = []
        for index_id in indexes_data.list_index_ids():
            try:
                data = indexes_data.read_index_json(index_id)
            except (OSError, ValueError):
                continue
            indexes.append(self._to_index(index_id, data))
        return indexes

    def get_by_id(self, index_id: str) -> Index | None:
        try:
            data = indexes_data.read_index_json(index_id)
        except (OSError, ValueError):
            return None
        return self._to_index(index_id, data)

    def _render_stub(self, index_id: str) -> str:
        r"""The real per-Index script content -- see the module docstring
        for why it can't just take CLI args.

        Every placeholder sits exactly where a Python literal belongs and
        is replaced by `repr()` of the value, which is what keeps a real
        Windows path safe: written raw, 'C:\Users\...' reads \U as a
        unicode escape and the deployed script fails to parse at all.
        Three live Index cron jobs failed 12 runs in a row on exactly
        that (2026-09-06), so the rendered text is parse-checked here
        rather than trusted -- a script that only breaks once a cron job
        runs it fails where nobody is looking."""
        template = indexes_data.read_index_runner_template()
        values = {
            "__INDEX_ID__": index_id,
            "__DATA_PATH__": str(settings.second_brain_data_path),
            "__VAULT_PATH__": str(settings.vault_path),
        }

        unknown = sorted(set(_PLACEHOLDER_PATTERN.findall(template)) - set(values))
        if unknown:
            raise IndexRunnerTemplateError(
                f"runner template declares placeholders nothing substitutes: {', '.join(unknown)}"
            )

        rendered = template
        for token, value in values.items():
            rendered = rendered.replace(token, repr(value))

        try:
            ast.parse(rendered)
        except SyntaxError as exc:
            raise IndexRunnerTemplateError(f"rendered runner is not valid Python: {exc}") from exc
        return rendered

    def create(
        self, name: str, *, schedule: str, folders: list[str] | None = None,
        tags: list[str] | None = None, depth: int | None = None,
        storage_path: str | None = None, cron_profile_id: str | None = None,
    ) -> Index:
        """Deploys the real build engine + this Index's own stub script,
        writes its definition, then creates the real Hermes cron job --
        in that order, so the job never fires against a script/
        definition that isn't there yet. Raises IndexCronCreationError
        (definition is still written either way -- retry-able) if the
        real `hermes cron create` call doesn't come back with a real
        job id."""
        index_id = tag_slug(name)
        resolved_storage_path = storage_path or str(
            settings.second_brain_data_path / "data" / "Indexes" / index_id / "output.json"
        )
        now = datetime.now(timezone.utc).isoformat()

        indexes_data.deploy_index_builder(cron_profile_id)
        indexes_data.write_index_script(index_id, cron_profile_id, self._render_stub(index_id))

        definition = {
            "id": index_id, "name": name,
            "folders": folders or [], "tags": tags or [], "depth": depth,
            "storage_path": resolved_storage_path, "schedule": schedule,
            "created_at": now, "updated_at": None,
            "cron_profile_id": cron_profile_id, "cron_job_id": None,
        }
        indexes_data.write_index_json(index_id, definition)

        job_id, output = get_client().cli.create_cron_job(
            schedule, name=f"index-{index_id}", script=f"index_{index_id}.py", no_agent=True,
        )
        if job_id is None:
            raise IndexCronCreationError(output)
        definition["cron_job_id"] = job_id
        indexes_data.write_index_json(index_id, definition)

        return self.get_by_id(index_id)

    def register_existing(
        self, index_id: str, name: str, *, cron_job_id: str, cron_profile_id: str | None,
        schedule: str, folders: list[str] | None = None, tags: list[str] | None = None,
        depth: int | None = None, storage_path: str = "",
    ) -> Index:
        """Brings an ALREADY-REAL cron job under this Manager's own
        tracking (operator, 2026-08-28: "the vault index rebuild is an
        index already, it is one of the indexes that the system need to
        be aware of") -- writes only the definition, linking to the
        existing real cron_job_id. Never creates, edits, or removes a
        real cron job, never deploys/overwrites a script -- the job
        keeps running exactly as it already does."""
        now = datetime.now(timezone.utc).isoformat()
        definition = {
            "id": index_id, "name": name,
            "folders": folders or [], "tags": tags or [], "depth": depth,
            "storage_path": storage_path, "schedule": schedule,
            "created_at": now, "updated_at": None,
            "cron_profile_id": cron_profile_id, "cron_job_id": cron_job_id,
        }
        indexes_data.write_index_json(index_id, definition)
        return self.get_by_id(index_id)

    def import_index(self, index_id: str, data: dict) -> Index:
        """Real, narrowly-scoped write path for import provisioning only
        (ADR-015), mirroring PipelineManager.import_pipeline. Validates
        `data` by round-tripping it through the EXISTING `_to_index`
        parser first, so a malformed shape raises and is never written.

        Deliberately creates NO cron job and keeps no incoming
        cron_job_id/cron_profile_id: those are opaque ids minted by one
        machine's own Hermes install and mean nothing on another. An
        imported Index therefore arrives unscheduled -- real, listed, and
        rebuildable, but not silently running a job the operator never
        asked for on this machine."""
        definition = {**data, "id": index_id, "cron_job_id": None, "cron_profile_id": None}
        self._to_index(index_id, definition)
        indexes_data.write_index_json(index_id, definition)
        return self.get_by_id(index_id)

    def update(
        self, index_id: str, *, name: str | None = None, folders: list[str] | None = None,
        tags: list[str] | None = None, depth: int | None = None,
        storage_path: str | None = None, schedule: str | None = None,
    ) -> Index | None:
        """`None` (omitted) = leave unchanged for every field, same
        convention every other Manager's own update() already uses.
        Editing `schedule` also edits the real cron job (if one exists)
        -- every other field is definition-only, picked up by the
        deployed stub's own next real run without any redeployment."""
        try:
            data = indexes_data.read_index_json(index_id)
        except (OSError, ValueError):
            return None

        if name is not None:
            data["name"] = name
        if folders is not None:
            data["folders"] = folders
        if tags is not None:
            data["tags"] = tags
        if depth is not None:
            data["depth"] = depth
        if storage_path is not None:
            data["storage_path"] = storage_path
        if schedule is not None:
            data["schedule"] = schedule
            cron_job_id = data.get("cron_job_id")
            if cron_job_id is not None:
                get_client().cli.edit_cron_job(cron_job_id, schedule=schedule)

        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        indexes_data.write_index_json(index_id, data)
        return self.get_by_id(index_id)

    def delete(self, index_id: str) -> dict:
        """Removes the real cron job, the built output file, the
        deployed stub script, and the definition -- in that order, so a
        failure partway through never leaves the cron job pointing at a
        script/definition that's already gone. Never raises for an
        already-deleted/unknown index -- {"deleted": False} instead
        (ADR-014's own result-dict convention)."""
        index = self.get_by_id(index_id)
        if index is None:
            return {"deleted": False}
        if index.cron_job_id is not None:
            get_client().cli.remove_cron_job(index.cron_job_id)
        indexes_data.delete_output_path(index.storage_path)
        indexes_data.delete_index_script(index_id, index.cron_profile_id)
        indexes_data.delete_index_definition(index_id)
        return {"deleted": True}
