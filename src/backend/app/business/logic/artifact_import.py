"""Import orchestrator (`REQ-SB-85-US-03-T05`) -- composes the archive
reader (`sbf_archive.read_archive`, `T01`), conflict detection
(`artifact_import_conflicts.detect_conflicts`, `T02`), the new
Template/Pipeline write paths (`TemplateManager.import_template`/
`PipelineManager.import_pipeline`, `T03`/`T04`, `ADR-015`), and the
Skill/Agent Managers (`SkillManager.deploy`/`.create`/`.update`,
`AgentManager.delete`, `HermesCLI.import_profile`, `ADR-014`) into the
real preview -> per-artifact-decision -> deploy flow the two
`/artifacts/import/{preview,commit}` routes expose.

`commit_import` is the ONLY function in this whole subsystem that ever
writes anything real -- every artifact's own deployment step runs inside
its own `try/except`, so one real failure never aborts the batch or
silently drops another artifact's own independently-reported outcome
(Scenario 9).
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import tempfile
from pathlib import Path

import yaml

from app.business.core.agents.agent_manager import AgentManager
from app.business.core.pipelines.pipeline_manager import PipelineManager
from app.business.core.sections.section_manager import SectionManager
from app.business.core.skills.skill_manager import SkillManager
from app.business.core.templates.template_manager import TemplateManager
from app.business.hermes.client import get_client
from app.business.logic import artifact_import_compat, artifact_import_conflicts, sbf_archive
from app.config import settings
from app.data_access import entities as entities_data
from app.data_access.registry import loader as registry_loader
from app.data_access.registry import writer as registry_writer

_FALLBACK_SECTION_NAME = "Data Gatherer"  # Same real fallback AgentManager/PipelineManager already use.

# Portability placeholders -- the import-side half of artifact_export.py's
# own identically-named constants/mechanism (which itself mirrors `tools/
# hermes_backup.py`/`hermes_restore.py`, MEMORY.md 2026-09-03). Substitutes
# this TARGET machine's own real vault/data/hermes-home path back in for
# every placeholder token a bundle's own Skill/Template/Agent-registry/
# Pipeline text carries, so a Skill deployed here always resolves against
# THIS deployment, never the source machine's own path. Duplicated (not
# imported) from artifact_export.py, matching this codebase's own
# established "each module owns its own business interpretation"
# convention (see this module's own _SEED_DATA_ALLOWLIST docstring).
_PLACEHOLDER_VAULT_PATH = "@@SECOND_BRAIN_VAULT_PATH@@"
_PLACEHOLDER_HERMES_HOME = "@@SECOND_BRAIN_HERMES_HOME@@"
_PLACEHOLDER_DATA_PATH = "@@SECOND_BRAIN_DATA_PATH@@"


def _substitute_placeholder(text: str, placeholder: str, real_value: str, *, json_escaped: bool) -> str:
    """Replaces every occurrence of placeholder with real_value -- the
    JSON-double-backslash-escaped form when the containing file is JSON,
    the raw form otherwise. BUG FIX (2026-09-03, found live building
    this): trying BOTH forms unconditionally in sequence against the same
    placeholder is wrong on this (restore) side -- the first `.replace()`
    call consumes every occurrence, so a second call for the escaped form
    always finds nothing left, silently leaving invalid JSON. Exact same
    fix applied to `tools/hermes_restore.py`'s own identically-shaped bug
    the same day (`MEMORY.md`) -- the placeholder token itself carries no
    backslashes, so which form is needed can never be recovered from the
    token alone; the caller must say so via `json_escaped`."""
    value = real_value.replace("\\", "\\\\") if json_escaped else real_value
    return text.replace(placeholder, value)


def _restore_placeholders(text: str, *, json_escaped: bool) -> str:
    """No ordering concern (unlike a literal-rewrite design) -- each
    placeholder is a unique, non-overlapping token."""
    text = _substitute_placeholder(text, _PLACEHOLDER_VAULT_PATH, str(settings.vault_path), json_escaped=json_escaped)
    text = _substitute_placeholder(text, _PLACEHOLDER_HERMES_HOME, str(settings.hermes_home_path), json_escaped=json_escaped)
    text = _substitute_placeholder(text, _PLACEHOLDER_DATA_PATH, str(settings.second_brain_data_path), json_escaped=json_escaped)
    return text

# Same v1 disclosed allowlist as `artifact_export.py`'s own
# `_SEED_DATA_ALLOWLIST` -- {real target-relative seed/blank-data path ->
# the literal substring a deployed Skill's own bundled content must
# reference for that path to count as "its owning capability was
# deployed". Duplicated rather than imported: each module owns its own
# business interpretation of the same real, single v1 entry
# (`Settings/Entities.md`), matching this codebase's own "zero business
# interpretation shared across module boundaries" discipline.
_SEED_DATA_ALLOWLIST: dict[str, str] = {
    "Settings/Entities.md": "Entities.md",
}
_SEED_DATA_WRITERS: dict[str, "callable"] = {
    "Settings/Entities.md": entities_data.write_raw,
}
_SEED_DATA_READERS: dict[str, "callable"] = {
    "Settings/Entities.md": entities_data.read_raw,
}

_SKILL_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def preview_import(archive_path: str) -> dict:
    """Parses + flags conflicts without deploying anything (Scenario 1).
    `MalformedBundleError` (`T01`) propagates uncaught -- the router maps
    it to a clean 4xx. `available_sections` (2026-09-03) lets the operator
    make a real, explicit choice for every "agent" entry instead of the
    section placement always silently landing on "Data Gatherer" -- a
    bundled Agent's own `Agent.json` never carries a `section_id` at all
    (confirmed by direct reading), so this decision is relevant for
    EVERY agent import, not just a conflict case."""
    manifest, payload = sbf_archive.read_archive(archive_path)
    artifacts = artifact_import_conflicts.detect_conflicts(manifest["artifacts"])
    # Screened here, in the preview, precisely because it is the last point
    # where the operator can still skip the artifact. A bundle predating the
    # 2026-09-04 data_root() fix carries scripts that would silently
    # reintroduce the email-capture outage -- and the placeholder machinery
    # cannot see it, since `.second-brain` is a relative literal, not one of
    # the absolute paths it substitutes.
    artifacts = artifact_import_compat.flag_stale_data_paths(artifacts, payload)
    available_profiles = [profile.id for profile in get_client().profiles.get_all()]
    available_sections = [{"id": s.id, "name": s.name} for s in SectionManager().get_all()]
    return {
        "manifest": manifest, "artifacts": artifacts,
        "available_profiles": available_profiles, "available_sections": available_sections,
    }


def commit_import(
    archive_path: str, decisions: dict[str, str], skill_target_profiles: dict[str, list[str]],
    agent_section_decisions: dict[str, str] | None = None,
) -> list[dict]:
    """Re-parses AND re-detects conflicts fresh -- never trusts a cached
    preview response (same staleness-safety principle as `commit_export`).
    Deploys every artifact per its resolved decision, one outcome dict per
    artifact, regardless of success/failure.

    `agent_section_decisions` ({agent_id: section_id | "__create_new__:
    <name>"}) is OPTIONAL, unlike `decisions` -- section placement is an
    organizational choice, never a destructive one, so an agent id with
    no entry here keeps the existing, always-safe fallback behavior
    (`_resolve_section_id`'s own "Data Gatherer" default) rather than
    failing the whole deploy the way an undecided skill/template/agent
    CONFLICT does."""
    manifest, payload = sbf_archive.read_archive(archive_path)
    artifacts = artifact_import_conflicts.detect_conflicts(manifest["artifacts"])
    agent_section_decisions = agent_section_decisions or {}

    outcomes: list[dict] = []
    deployed_skill_ids: set[str] = set()
    for entry in artifacts:
        kind = entry["kind"]
        artifact_id = entry["id"]
        decision = decisions.get(f"{kind}:{artifact_id}")
        try:
            outcome = _deploy_one(
                entry, decision, payload, skill_target_profiles,
                agent_section_decisions.get(artifact_id) if kind == "agent" else None,
            )
        except Exception as exc:  # noqa: BLE001 -- one real failure must never abort the batch (Scenario 9).
            outcome = {"kind": kind, "id": artifact_id, "status": "failed", "deployed_as": None, "detail": str(exc)}
        outcomes.append(outcome)
        if kind == "skill" and outcome["status"] == "deployed":
            deployed_skill_ids.add(artifact_id)

    _write_seed_data(payload, deployed_skill_ids)
    return outcomes


def _deployed(
    kind: str, artifact_id: str, *, deployed_as: str | None = None, detail: str = "deployed",
    primary_routing_snippet: str | None = None,
) -> dict:
    return {
        "kind": kind, "id": artifact_id, "status": "deployed", "deployed_as": deployed_as, "detail": detail,
        "primary_routing_snippet": primary_routing_snippet,
    }


def _skipped(kind: str, artifact_id: str, *, detail: str = "skipped per operator decision") -> dict:
    return {"kind": kind, "id": artifact_id, "status": "skipped", "deployed_as": None, "detail": detail}


def _deploy_one(
    entry: dict, decision: str | None, payload: dict[str, bytes], skill_target_profiles: dict,
    section_decision: str | None,
) -> dict:
    kind = entry["kind"]
    artifact_id = entry["id"]
    conflicts = bool(entry.get("conflicts"))

    # Every conflicting artifact requires an explicit decision -- no
    # conflict is EVER resolved silently (Scenario 3/Constraints).
    if conflicts and decision not in ("overwrite", "skip", "keep_both"):
        return {
            "kind": kind, "id": artifact_id, "status": "failed", "deployed_as": None,
            "detail": f"{kind} {artifact_id!r} conflicts with an existing artifact -- no explicit decision supplied",
        }

    if kind == "skill":
        return _deploy_skill(artifact_id, entry, conflicts, decision, payload, skill_target_profiles)
    if kind == "template":
        return _deploy_template(artifact_id, conflicts, decision, payload)
    if kind == "pipeline":
        return _deploy_pipeline(artifact_id, conflicts, decision, payload)
    if kind == "agent":
        return _deploy_agent(artifact_id, conflicts, decision, payload, section_decision)
    raise ValueError(f"unrecognized artifact kind {kind!r}")


# -- Skill ---------------------------------------------------------------

def _skill_content_from_payload(payload: dict[str, bytes], skill_id: str) -> tuple[str, dict[str, str]]:
    skill_md_bytes = payload.get(f"skills/{skill_id}/SKILL.md")
    skill_md = (
        _restore_placeholders(skill_md_bytes.decode("utf-8"), json_escaped=False)
        if skill_md_bytes is not None else ""
    )
    scripts_prefix = f"skills/{skill_id}/scripts/"
    scripts = {
        member_path[len(scripts_prefix):]: _restore_placeholders(
            content.decode("utf-8"), json_escaped=member_path.endswith(".json"),
        )
        for member_path, content in payload.items()
        if member_path.startswith(scripts_prefix)
    }
    return skill_md, scripts


def _skill_name_and_description(skill_md: str, fallback_id: str) -> tuple[str, str]:
    """Derives a fresh Skill's own name/description straight from its
    real, bundled SKILL.md frontmatter -- the SAME parsing convention
    `app/hermes/skills.py::_skill_from_md` already uses for a deployed
    Hermes-side skill -- since the manifest's own frozen shape
    (`ADR-013`) never carries Skill metadata (name/description live only
    in the target machine's own Registry `Tools/<tool>/Skills/<id>/
    Skill.json`, which an export never includes). Scope-internal
    judgement call, not a manifest-shape change."""
    match = _SKILL_FRONTMATTER_RE.match(skill_md)
    frontmatter: dict = {}
    if match:
        try:
            parsed = yaml.safe_load(match.group(1))
            frontmatter = parsed if isinstance(parsed, dict) else {}
        except yaml.YAMLError:
            frontmatter = {}
    return str(frontmatter.get("name") or fallback_id), str(frontmatter.get("description") or "")


def _next_alternate_id(base_id: str, get_by_id) -> str:
    candidate = f"{base_id}-imported"
    suffix = 2
    while get_by_id(candidate) is not None:
        candidate = f"{base_id}-imported-{suffix}"
        suffix += 1
    return candidate


def _deploy_skill(
    artifact_id: str, entry: dict, conflicts: bool, decision: str | None,
    payload: dict[str, bytes], skill_target_profiles: dict,
) -> dict:
    kind = "skill"
    skill_md, scripts = _skill_content_from_payload(payload, artifact_id)
    category = entry.get("category")
    targets = skill_target_profiles.get(artifact_id) or ["default"]

    if not conflicts:
        name, description = _skill_name_and_description(skill_md, artifact_id)
        SkillManager().create(
            category, artifact_id, name=name, description=description, skill_md_content=skill_md,
            tool_id="jarvis", scripts=scripts, deploy_to=targets,
        )
        return _deployed(kind, artifact_id)

    if decision == "skip":
        return _skipped(kind, artifact_id)

    if decision == "overwrite":
        updated = SkillManager().update(artifact_id, skill_md_content=skill_md, scripts=scripts)
        already_deployed = set(updated.deployed_to) if updated is not None else set()
        for profile_id in targets:
            if profile_id not in already_deployed:
                SkillManager().deploy(artifact_id, profile_id)
        return _deployed(kind, artifact_id)

    # decision == "keep_both"
    alt_id = _next_alternate_id(artifact_id, SkillManager().get_by_id)
    name, description = _skill_name_and_description(skill_md, artifact_id)
    SkillManager().create(
        category, alt_id, name=f"{name} (imported)", description=description, skill_md_content=skill_md,
        tool_id="jarvis", scripts=scripts, deploy_to=targets,
    )
    return _deployed(kind, artifact_id, deployed_as=alt_id)


# -- Template / Pipeline (same shape) -------------------------------------

def _deploy_template(artifact_id: str, conflicts: bool, decision: str | None, payload: dict[str, bytes]) -> dict:
    kind = "template"
    raw = payload.get(f"templates/{artifact_id}/Template.json")
    data = json.loads(_restore_placeholders(raw.decode("utf-8"), json_escaped=True)) if raw is not None else {}

    if not conflicts or decision == "overwrite":
        TemplateManager().import_template(artifact_id, data)
        return _deployed(kind, artifact_id)
    if decision == "skip":
        return _skipped(kind, artifact_id)

    # decision == "keep_both"
    alt_id = _next_alternate_id(artifact_id, TemplateManager().get_by_id)
    TemplateManager().import_template(alt_id, {**data, "id": alt_id})
    return _deployed(kind, artifact_id, deployed_as=alt_id)


def _deploy_pipeline(artifact_id: str, conflicts: bool, decision: str | None, payload: dict[str, bytes]) -> dict:
    kind = "pipeline"
    raw = payload.get(f"pipelines/{artifact_id}.json")
    data = json.loads(_restore_placeholders(raw.decode("utf-8"), json_escaped=True)) if raw is not None else {}

    if not conflicts or decision == "overwrite":
        PipelineManager().import_pipeline(artifact_id, data)
        return _deployed(kind, artifact_id)
    if decision == "skip":
        return _skipped(kind, artifact_id)

    # decision == "keep_both"
    alt_id = _next_alternate_id(artifact_id, PipelineManager().get_by_id)
    PipelineManager().import_pipeline(alt_id, {**data, "id": alt_id})
    return _deployed(kind, artifact_id, deployed_as=alt_id)


# -- Agent -----------------------------------------------------------------

def _write_agent_scratch_tarball(payload: dict[str, bytes], artifact_id: str) -> str:
    tarball_bytes = payload.get(f"agents/{artifact_id}/profile.tar.gz")
    if tarball_bytes is None:
        raise ValueError(f"bundle has no agents/{artifact_id}/profile.tar.gz member")
    fd, scratch_path = tempfile.mkstemp(suffix=".tar.gz", prefix="second-brain-agent-import-")
    os.close(fd)
    Path(scratch_path).write_bytes(tarball_bytes)
    return scratch_path


_CREATE_NEW_SECTION_PREFIX = "__create_new__:"


def _resolve_section_id(bundled_section_id: str | None, operator_decision: str | None) -> str:
    """Three ways this resolves, in priority order:

    1. `operator_decision` (2026-09-03, the new explicit picker) -- an
       existing target section id, used as-is; or `"__create_new__:<name>"`
       to create a brand new one. Since this was an EXPLICIT choice, an
       id that doesn't actually exist on this machine is a real error
       (fail loud), never silently swapped for a fallback.
    2. A bundled `section_id`, used as-is only if it genuinely exists on
       THIS target machine -- in practice this never fires today (the
       real, current bundle shape never carries one at all: `Agent.json`
       only ever stores section placement via its own folder path, never
       as a JSON field, confirmed by direct reading of `AgentManager.
       _write_registry_agent`/`registry_writer.write_agent_files`) --
       kept for forward-compat if a future export ever does carry one.
    3. No decision at all -- falls back to the target's own real "Data
       Gatherer" section (creating it if missing), matching the
       Constraint's own "never lands under a section that doesn't exist"
       requirement. Organizational default, never a destructive one --
       unlike an undecided skill/template/agent CONFLICT, an unset
       section decision never fails the import."""
    section_manager = SectionManager()
    if operator_decision is not None:
        if operator_decision.startswith(_CREATE_NEW_SECTION_PREFIX):
            name = operator_decision[len(_CREATE_NEW_SECTION_PREFIX):].strip()
            if not name:
                raise ValueError(f"{_CREATE_NEW_SECTION_PREFIX!r} decision needs a real section name after the prefix")
            return section_manager.create(name).id
        if section_manager.get_by_id(operator_decision) is None:
            raise ValueError(f"section {operator_decision!r} does not exist on this machine")
        return operator_decision
    if bundled_section_id is not None and section_manager.get_by_id(bundled_section_id) is not None:
        return bundled_section_id
    for section in section_manager.get_all():
        if section.name == _FALLBACK_SECTION_NAME:
            return section.id
    return section_manager.create(_FALLBACK_SECTION_NAME).id


def _write_agent_registry_side(
    payload: dict[str, bytes], original_id: str, real_deployed_id: str, section_decision: str | None,
) -> str | None:
    """Returns the bundle's own `primary_routing_snippet` (or None) --
    already lands on the target's own Agent.json for free (the whole
    `config` dict is written through as-is, no per-field allowlist), but
    the caller also needs the raw value to surface it as an import-time
    suggestion (see apply_primary_routing_snippet -- never auto-applied
    to the target's own Primary SOUL.md, that's a separate, explicit,
    operator-triggered step)."""
    config_raw = payload.get(f"agents/{original_id}/Agent.json")
    soul_raw = payload.get(f"agents/{original_id}/soul.md")
    config = (
        json.loads(_restore_placeholders(config_raw.decode("utf-8"), json_escaped=True))
        if config_raw is not None else {}
    )
    soul_text = (
        _restore_placeholders(soul_raw.decode("utf-8"), json_escaped=False)
        if soul_raw is not None else f"You are {real_deployed_id}."
    )
    config = {**config, "id": real_deployed_id}

    section_id = _resolve_section_id(config.get("section_id"), section_decision)
    is_background_agent = bool(config.get("is_background_agent", False))
    agent_dir = registry_writer.agent_dir(
        real_deployed_id, section_id=section_id, is_background_agent=is_background_agent,
    )
    registry_writer.write_agent_files(agent_dir, config=config, soul_text=soul_text)
    asyncio.run(registry_loader.boot())
    return config.get("primary_routing_snippet")


def _deploy_agent(
    artifact_id: str, conflicts: bool, decision: str | None, payload: dict[str, bytes],
    section_decision: str | None,
) -> dict:
    kind = "agent"
    if conflicts and decision == "skip":
        return _skipped(kind, artifact_id)

    scratch_path = _write_agent_scratch_tarball(payload, artifact_id)
    try:
        if not conflicts or decision == "overwrite":
            if conflicts:
                AgentManager().delete(artifact_id)  # Mirrors AgentManager.update()'s own delete-then-recreate shape (ADR-014).
            ok, output = get_client().cli.import_profile(scratch_path)
            if not ok:
                raise RuntimeError(f"hermes profile import failed for {artifact_id!r}: {output}")
            snippet = _write_agent_registry_side(payload, artifact_id, artifact_id, section_decision)
            return _deployed(kind, artifact_id, primary_routing_snippet=snippet)

        # decision == "keep_both"
        alt_id = f"{artifact_id}-imported"
        ok, output = get_client().cli.import_profile(scratch_path, name=alt_id)
        if not ok:
            raise RuntimeError(f"hermes profile import failed for {artifact_id!r}: {output}")
        snippet = _write_agent_registry_side(payload, artifact_id, alt_id, section_decision)
        return _deployed(kind, artifact_id, deployed_as=alt_id, primary_routing_snippet=snippet)
    finally:
        Path(scratch_path).unlink(missing_ok=True)


# -- Primary routing (2026-09-03) -------------------------------------------
#
# A bundled Agent's own `primary_routing_snippet` (Registry-side metadata,
# never a Hermes SOUL.md field) is surfaced to the operator as a suggestion
# on every successful agent deploy (see _deploy_agent's own outcome, above)
# -- never applied automatically. This is the ONE explicit, separate step
# that actually writes it into the TARGET's own real Primary SOUL.md,
# matching this whole subsystem's "never silent" discipline for anything
# consequential (the same posture as the secret-scan redact/keep/cancel
# decisions and the skill/template/agent conflict decisions -- an operator
# action, not a side effect of import). Idempotent via a per-agent marker
# pair, the same style `agent_manager.py`'s own _SPECIALISTS_BEGIN/_END
# already establishes for a different auto-generated SOUL.md section.

def _primary_routing_markers(agent_id: str) -> tuple[str, str]:
    return (
        f"<!-- BEGIN PRIMARY ROUTING: {agent_id} (added by Artifacts import) -->",
        f"<!-- END PRIMARY ROUTING: {agent_id} -->",
    )


def apply_primary_routing_snippet(agent_id: str, snippet: str) -> dict:
    """Appends `snippet` to this machine's real Primary SOUL.md
    (`settings.hermes_home_path / "SOUL.md"`), wrapped in a marker pair
    unique to `agent_id`. Re-running for the SAME agent_id is a safe
    no-op (checked by marker presence, not text equality -- an operator
    who's hand-edited the snippet in place since the last apply is never
    silently overwritten). Raises FileNotFoundError if this machine has
    no real Primary SOUL.md yet -- never fabricates one."""
    soul_path = settings.hermes_home_path / "SOUL.md"
    if not soul_path.is_file():
        raise FileNotFoundError(f"no Primary SOUL.md found at {soul_path}")
    begin, end = _primary_routing_markers(agent_id)
    text = soul_path.read_text(encoding="utf-8")
    if begin in text:
        return {"agent_id": agent_id, "applied": False, "detail": "already applied -- marker already present"}
    block = f"\n\n{begin}\n{snippet.strip()}\n{end}\n"
    soul_path.write_text(text.rstrip("\n") + block, encoding="utf-8")
    return {"agent_id": agent_id, "applied": True, "detail": f"appended to {soul_path}"}


# -- Seed / blank data files -------------------------------------------------

def _skill_content_references_needle(payload: dict[str, bytes], skill_id: str, needle: str) -> bool:
    skill_md, scripts = _skill_content_from_payload(payload, skill_id)
    if needle in skill_md:
        return True
    return any(needle in text for text in scripts.values())


def _write_seed_data(payload: dict[str, bytes], deployed_skill_ids: set[str]) -> None:
    """Writes every allowlisted seed/blank-data path this bundle carries
    AND whose owning Skill was genuinely deployed this commit -- silently
    no-op'd when that Skill was skipped entirely (a seed file has no
    conflict/decision concept of its own). Content is ALWAYS forced
    genuinely empty, regardless of what the bundle's own payload bytes
    hold (the same hard capability/data boundary `artifact_export.py`'s
    own writer already guarantees on the export side)."""
    for member_path in payload:
        if not member_path.startswith("seed_data/"):
            continue
        target_path = member_path[len("seed_data/"):]
        needle = _SEED_DATA_ALLOWLIST.get(target_path)
        writer = _SEED_DATA_WRITERS.get(target_path)
        if needle is None or writer is None:
            continue
        owning_capability_deployed = any(
            _skill_content_references_needle(payload, skill_id, needle) for skill_id in deployed_skill_ids
        )
        if owning_capability_deployed:
            writer("")
