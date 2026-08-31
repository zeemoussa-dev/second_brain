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
from app.business.logic import artifact_import_conflicts, sbf_archive
from app.data_access import entities as entities_data
from app.data_access.registry import loader as registry_loader
from app.data_access.registry import writer as registry_writer

_FALLBACK_SECTION_NAME = "Data Gatherer"  # Same real fallback AgentManager/PipelineManager already use.

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

_SKILL_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def preview_import(archive_path: str) -> dict:
    """Parses + flags conflicts without deploying anything (Scenario 1).
    `MalformedBundleError` (`T01`) propagates uncaught -- the router maps
    it to a clean 4xx."""
    manifest, _payload = sbf_archive.read_archive(archive_path)
    artifacts = artifact_import_conflicts.detect_conflicts(manifest["artifacts"])
    available_profiles = [profile.id for profile in get_client().profiles.get_all()]
    return {"manifest": manifest, "artifacts": artifacts, "available_profiles": available_profiles}


def commit_import(
    archive_path: str, decisions: dict[str, str], skill_target_profiles: dict[str, list[str]],
) -> list[dict]:
    """Re-parses AND re-detects conflicts fresh -- never trusts a cached
    preview response (same staleness-safety principle as `commit_export`).
    Deploys every artifact per its resolved decision, one outcome dict per
    artifact, regardless of success/failure."""
    manifest, payload = sbf_archive.read_archive(archive_path)
    artifacts = artifact_import_conflicts.detect_conflicts(manifest["artifacts"])

    outcomes: list[dict] = []
    deployed_skill_ids: set[str] = set()
    for entry in artifacts:
        kind = entry["kind"]
        artifact_id = entry["id"]
        decision = decisions.get(f"{kind}:{artifact_id}")
        try:
            outcome = _deploy_one(entry, decision, payload, skill_target_profiles)
        except Exception as exc:  # noqa: BLE001 -- one real failure must never abort the batch (Scenario 9).
            outcome = {"kind": kind, "id": artifact_id, "status": "failed", "deployed_as": None, "detail": str(exc)}
        outcomes.append(outcome)
        if kind == "skill" and outcome["status"] == "deployed":
            deployed_skill_ids.add(artifact_id)

    _write_seed_data(payload, deployed_skill_ids)
    return outcomes


def _deployed(kind: str, artifact_id: str, *, deployed_as: str | None = None, detail: str = "deployed") -> dict:
    return {"kind": kind, "id": artifact_id, "status": "deployed", "deployed_as": deployed_as, "detail": detail}


def _skipped(kind: str, artifact_id: str, *, detail: str = "skipped per operator decision") -> dict:
    return {"kind": kind, "id": artifact_id, "status": "skipped", "deployed_as": None, "detail": detail}


def _deploy_one(entry: dict, decision: str | None, payload: dict[str, bytes], skill_target_profiles: dict) -> dict:
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
        return _deploy_agent(artifact_id, conflicts, decision, payload)
    raise ValueError(f"unrecognized artifact kind {kind!r}")


# -- Skill ---------------------------------------------------------------

def _skill_content_from_payload(payload: dict[str, bytes], skill_id: str) -> tuple[str, dict[str, str]]:
    skill_md_bytes = payload.get(f"skills/{skill_id}/SKILL.md")
    skill_md = skill_md_bytes.decode("utf-8") if skill_md_bytes is not None else ""
    scripts_prefix = f"skills/{skill_id}/scripts/"
    scripts = {
        member_path[len(scripts_prefix):]: content.decode("utf-8")
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
    data = json.loads(raw.decode("utf-8")) if raw is not None else {}

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
    data = json.loads(raw.decode("utf-8")) if raw is not None else {}

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


def _resolve_section_id(section_id: str | None) -> str:
    """A bundled Agent's own `section_id` is used as-is only if it
    genuinely exists on THIS target machine; otherwise (including the
    real, current bundle shape, which never carries one -- `Agent.json`
    only ever stores section placement via its own folder path, never as
    a JSON field, confirmed by direct reading of `AgentManager.
    _write_registry_agent`/`registry_writer.write_agent_files`) falls
    back to the target's own real "Data Gatherer" section, matching the
    Constraint's own "never lands under a section that doesn't exist"
    requirement -- an honest, always-safe fallback, never a fabricated
    section."""
    section_manager = SectionManager()
    if section_id is not None and section_manager.get_by_id(section_id) is not None:
        return section_id
    for section in section_manager.get_all():
        if section.name == _FALLBACK_SECTION_NAME:
            return section.id
    return section_manager.create(_FALLBACK_SECTION_NAME).id


def _write_agent_registry_side(payload: dict[str, bytes], original_id: str, real_deployed_id: str) -> None:
    config_raw = payload.get(f"agents/{original_id}/Agent.json")
    soul_raw = payload.get(f"agents/{original_id}/soul.md")
    config = json.loads(config_raw.decode("utf-8")) if config_raw is not None else {}
    soul_text = soul_raw.decode("utf-8") if soul_raw is not None else f"You are {real_deployed_id}."
    config = {**config, "id": real_deployed_id}

    section_id = _resolve_section_id(config.get("section_id"))
    is_background_agent = bool(config.get("is_background_agent", False))
    agent_dir = registry_writer.agent_dir(
        real_deployed_id, section_id=section_id, is_background_agent=is_background_agent,
    )
    registry_writer.write_agent_files(agent_dir, config=config, soul_text=soul_text)
    asyncio.run(registry_loader.boot())


def _deploy_agent(artifact_id: str, conflicts: bool, decision: str | None, payload: dict[str, bytes]) -> dict:
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
            _write_agent_registry_side(payload, artifact_id, artifact_id)
            return _deployed(kind, artifact_id)

        # decision == "keep_both"
        alt_id = f"{artifact_id}-imported"
        ok, output = get_client().cli.import_profile(scratch_path, name=alt_id)
        if not ok:
            raise RuntimeError(f"hermes profile import failed for {artifact_id!r}: {output}")
        _write_agent_registry_side(payload, artifact_id, alt_id)
        return _deployed(kind, artifact_id, deployed_as=alt_id)
    finally:
        Path(scratch_path).unlink(missing_ok=True)


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
