"""Export orchestrator (`REQ-SB-85-US-02-T04`, `ADR-013`) -- composes the
dependency-closure resolver (`artifact_dependency_resolver.py`, `T02`),
the secret-scan pass (`artifact_secret_scan.py`, `T03`), and the archive
writer (`sbf_archive.py`, this task) into the real resolve -> scan ->
gate -> write pipeline the two `/artifacts/export/{preview,commit}`
routes expose. `commit_export` is the ONLY function in this whole
subsystem that ever writes a real file.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from app.business.hermes.client import get_client
from app.business.logic import artifact_dependency_resolver, artifact_secret_scan, sbf_archive
from app.config import settings
from app.data_access import pipelines as pipelines_data
from app.data_access import skills as skills_data
from app.data_access import templates as templates_data
from app.data_access.registry import loader as registry_loader

# Portability placeholders -- the exact same mechanism `tools/
# hermes_backup.py` uses (MEMORY.md, 2026-09-03), applied here to
# Skill/Template/Agent-registry/Pipeline TEXT content instead of a whole
# filesystem tree. A Skill's own SKILL.md/scripts can genuinely reference
# THIS machine's real vault/data/hermes-home path (a hardcoded example
# command, a script's own hardcoded fallback default) -- confirmed live,
# 2026-09-03: 16 of ~17 real canonical Skills' own SKILL.md bake this
# machine's literal path into the exact `terminal(command=...)` block the
# agent is instructed to run, and 3 real scripts (email-thread-capture/
# meeting-capture) fall back to a hardcoded literal because the env var
# they check is never actually set anywhere. Those literal values are
# simply wrong the moment the artifact is imported onto a different
# deployment (operator, 2026-09-03: "that is what we did in backup and
# restore" -- apply the same fix here). Duplicated (not imported) from
# hermes_backup.py, matching this codebase's own established "each module
# owns its own business interpretation" convention (see artifact_import.
# py's own identical duplication note for its _SEED_DATA_ALLOWLIST).
_PLACEHOLDER_VAULT_PATH = "@@SECOND_BRAIN_VAULT_PATH@@"
_PLACEHOLDER_HERMES_HOME = "@@SECOND_BRAIN_HERMES_HOME@@"
_PLACEHOLDER_DATA_PATH = "@@SECOND_BRAIN_DATA_PATH@@"


def _substitute_both_forms(text: str, real_value: str, placeholder: str) -> str:
    """Replaces every real occurrence of real_value with placeholder, in
    both its raw form and its JSON-double-backslash-escaped form (a
    Windows path embedded in a JSON string value always carries doubled
    backslashes) -- mirrors hermes_backup.py's own helper exactly."""
    text = text.replace(real_value, placeholder)
    text = text.replace(real_value.replace("\\", "\\\\"), placeholder)
    return text


def _substitute_placeholders(text: str) -> str:
    """Order matters, same reason as hermes_backup.py's own identically-
    shaped function: second_brain_data_path is either unrelated to the
    vault path, or (the common case) vault-relative -- a real string that
    literally CONTAINS the vault path as its own prefix. Substituting the
    vault path first would consume that shared prefix and leave nothing
    for the data-path substitution to match."""
    data_str, vault_str, hermes_str = (
        str(settings.second_brain_data_path), str(settings.vault_path), str(settings.hermes_home_path),
    )
    if data_str != vault_str:
        text = _substitute_both_forms(text, data_str, _PLACEHOLDER_DATA_PATH)
    text = _substitute_both_forms(text, vault_str, _PLACEHOLDER_VAULT_PATH)
    text = _substitute_both_forms(text, hermes_str, _PLACEHOLDER_HERMES_HOME)
    return text


# v1 disclosed allowlist (this task's own scope-internal judgement call,
# logged in the Implementation Log -- the PRD names one real example, not
# an enumerated list): {real target-relative seed/blank-data path -> the
# literal substring a closure Skill's own content must reference for that
# path to be considered genuinely needed}. Exactly one entry today,
# matching Scenario 5's own real example -- `Settings/Entities.md` is the
# only real seed/blank-data store of this shape in the app
# (`data_access/entities.py`).
_SEED_DATA_ALLOWLIST: dict[str, str] = {
    "Settings/Entities.md": "Entities.md",
}


def _text_content_for_scan(closure: list[dict]) -> dict[str, str]:
    """{file_path: text} for every genuinely Second-Brain-owned text file
    the closure names -- a Skill's own `SKILL.md`/`scripts/**`, a
    Template's own `Template.json`, and an Agent's own Registry-side
    `Agent.json`/`soul.md` mirror. Deliberately the SAME `file_path`
    convention `artifact_secret_scan.py`'s own (module-private) content
    readers use, so a finding's own `file_path` (from `scan_closure`)
    always resolves to a real key here -- confirmed by direct reading of
    that module before writing this one (`T03` is frozen/`Done`; this
    composes it from the outside, never edits it, never imports its
    private names). Never includes Pipeline content (`T03`'s own
    disclosed scope-internal judgement call: a Pipeline's own
    `pipelines/<id>.json` was never part of the scanned surface) and
    never touches an Agent's own Hermes `profile.tar.gz` piece (`ADR-014`'s
    opaque-bytes boundary -- there is no code path here that could)."""
    content: dict[str, str] = {}
    for entry in closure:
        kind = entry.get("kind")
        artifact_id = entry.get("id")
        if not artifact_id:
            continue
        if kind == "skill":
            skill_md = skills_data.read_skill_md(artifact_id)
            if skill_md is not None:
                content[f"skills/{artifact_id}/SKILL.md"] = skill_md
            for rel_path, text in skills_data.list_scripts(artifact_id).items():
                content[f"skills/{artifact_id}/scripts/{rel_path}"] = text
        elif kind == "template":
            try:
                raw = templates_data.read_template_json(artifact_id)
            except (FileNotFoundError, json.JSONDecodeError):
                continue
            content[f"templates/{artifact_id}/Template.json"] = json.dumps(raw, indent=2)
        elif kind == "agent":
            agent_dir = registry_loader.agent_data_dir(artifact_id)
            if agent_dir is None:
                continue
            config_path = agent_dir / "Agent.json"
            soul_path = agent_dir / "soul.md"
            if config_path.is_file():
                try:
                    content[f"agents/{artifact_id}/Agent.json"] = config_path.read_text(encoding="utf-8")
                except OSError:
                    pass
            if soul_path.is_file():
                try:
                    content[f"agents/{artifact_id}/soul.md"] = soul_path.read_text(encoding="utf-8")
                except OSError:
                    pass
        # "pipeline" contributes nothing here -- see docstring.
    return content


def _closure_references_seed_needle(closure: list[dict], needle: str) -> bool:
    """The same literal-substring static-scan heuristic `T02`'s own
    Skill->Template coupling detection uses, applied to the seed/blank-
    data allowlist instead: does any closure Skill's own `SKILL.md`/
    script content reference `needle` literally."""
    for entry in closure:
        if entry.get("kind") != "skill":
            continue
        skill_id = entry.get("id")
        skill_md = skills_data.read_skill_md(skill_id) or ""
        if needle in skill_md:
            return True
        if any(needle in text for text in skills_data.list_scripts(skill_id).values()):
            return True
    return False


def _add_seed_data_entries(closure: list[dict], payload: dict[str, bytes]) -> None:
    """Adds every allowlisted seed/blank-data path the closure's own
    Skills genuinely reference, content ALWAYS forced to `b""` --
    regardless of what the real, current file on this machine actually
    contains (the hard capability/data boundary, Scenarios 4/5). Never
    reads the real file's own content -- `data_access.entities.read_raw()`
    is never called anywhere in this module."""
    for target_path, needle in _SEED_DATA_ALLOWLIST.items():
        if _closure_references_seed_needle(closure, needle):
            payload[f"seed_data/{target_path}"] = b""


def _export_agent_profile_tarball(agent_id: str) -> bytes:
    """The RAW, unmodified output of `HermesCLI.export_profile`
    (`ADR-014`) -- that CLI needs a real output path, not a byte stream,
    so this writes to a scratch temp path first, reads it back as bytes,
    then deletes the scratch path immediately -- never left on disk after
    this call returns, success or failure."""
    fd, scratch_path = tempfile.mkstemp(suffix=".tar.gz", prefix="second-brain-agent-export-")
    os.close(fd)
    try:
        ok, output = get_client().cli.export_profile(agent_id, scratch_path)
        if not ok:
            raise RuntimeError(f"hermes profile export failed for {agent_id!r}: {output}")
        return Path(scratch_path).read_bytes()
    finally:
        Path(scratch_path).unlink(missing_ok=True)


def preview_export(selection: list[dict]) -> dict:
    """Resolves + scans without writing anything (Scenario 1/2)."""
    closure = artifact_dependency_resolver.resolve_closure(selection)
    findings = artifact_secret_scan.scan_closure(closure)
    return {"closure": closure, "secret_findings": findings}


def commit_export(selection: list[dict], secret_decisions: dict[str, str]) -> str:
    """Re-resolves and re-scans FRESH -- never trusts a client-cached
    preview response (closes a real staleness window between preview and
    commit). Raises `SecretScanIncompleteError`/`SecretScanCancelledError`
    (propagated uncaught, for the router to map to a clean 4xx) before
    anything below is ever reached -- no archive byte is written while an
    unresolved finding remains undecided, or after a cancel (Scenario
    3/7). Returns the real scratch `.sbf` path on success; the router owns
    streaming it and cleaning it up afterward."""
    closure = artifact_dependency_resolver.resolve_closure(selection)
    findings = artifact_secret_scan.scan_closure(closure)
    closure_content = _text_content_for_scan(closure)
    redacted_content = artifact_secret_scan.apply_decisions(closure_content, findings, secret_decisions)

    payload: dict[str, bytes] = {}
    manifest_artifacts: list[dict] = []
    for entry in closure:
        kind = entry["kind"]
        artifact_id = entry["id"]
        manifest_artifacts.append({
            "kind": kind,
            "id": artifact_id,
            "included_reason": entry["included_reason"],
            "depends_via": entry["depends_via"],
            "category": skills_data.category_of(artifact_id) if kind == "skill" else None,
        })

        if kind == "pipeline":
            try:
                pipeline_json = pipelines_data.read_pipeline_json(artifact_id)
            except (FileNotFoundError, ValueError):
                continue
            pipeline_text = _substitute_placeholders(json.dumps(pipeline_json, indent=2))
            payload[f"pipelines/{artifact_id}.json"] = pipeline_text.encode("utf-8")
            continue

        prefix = f"{kind}s/{artifact_id}/"
        for file_path, text in redacted_content.items():
            if file_path.startswith(prefix):
                payload[file_path] = _substitute_placeholders(text).encode("utf-8")

        if kind == "agent":
            payload[f"agents/{artifact_id}/profile.tar.gz"] = _export_agent_profile_tarball(artifact_id)

    _add_seed_data_entries(closure, payload)

    redacted_count = sum(
        1 for finding in findings
        if secret_decisions.get(f"{finding['file_path']}:{finding['line']}") == "redact"
    )
    manifest = {
        "format_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": manifest_artifacts,
        "secret_scan": {"findings_decided": len(findings), "redacted_count": redacted_count},
    }

    fd, scratch_sbf_path = tempfile.mkstemp(suffix=".sbf", prefix="second-brain-export-")
    os.close(fd)
    sbf_archive.write_archive(scratch_sbf_path, manifest, payload)
    return scratch_sbf_path
