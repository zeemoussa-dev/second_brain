"""Secret-shaped-string scan over Second-Brain-owned bundle bytes only
(`ADR-013`) -- a hard gate between "closure resolved"
(`artifact_dependency_resolver.py`) and "archive written" (`T04`'s own
`sbf_archive.py`). Scans ONLY genuinely-new Second-Brain-owned text: a
Skill's own `SKILL.md`/`scripts/**` (`data_access.skills`), a
Template's own `Template.json` (`data_access.templates`), and an
Agent's own Registry-side `Agent.json`/`soul.md` mirror
(`data_access.registry.loader`) -- the same lookup
`agent_visual_registry.py`/`agent_manager.py` already use to find an
agent's real on-disk files, reused here rather than re-derived.

**Never** the nested `agents/<id>/profile.tar.gz` -- that piece arrives
already silently redacted by Hermes' own `export_profile`
(`agent.redact.redact_sensitive_text(..., force=True)`, `ADR-014`).
This module has no code path that even reads that file: an "agent"
closure entry only ever yields its Registry-side `Agent.json`/`soul.md`
text here, never anything from a Hermes profile directory -- a
structural skip-by-kind, not a runtime filter that could be bypassed by
a differently-shaped closure entry.

A "pipeline" closure entry contributes no scanned content here -- the
story's own Objective enumerates only Skill/Template/Agent-registry/
seed-blank-data as the scanned surface; a Pipeline's own `pipelines/
<id>.json` was never named as part of it. Disclosed as a scope-internal
judgement call in the task's Implementation Log, not a silent gap.

Never writes anything to disk -- pure in-memory read + transform.
"""
from __future__ import annotations

import json
import logging
import re

from app.data_access import skills as skills_data
from app.data_access import templates as templates_data
from app.data_access.registry import loader as registry_loader

logger = logging.getLogger(__name__)

_REDACTION_PLACEHOLDER = "[REDACTED-BY-SECOND-BRAIN-EXPORT]"

# A disclosed, non-exhaustive v1 heuristic set (ADR-013's own "acceptable
# v1 limitation, not a blocking defect" framing, same posture already
# applied to the Skill->Template coupling heuristic) -- common
# secret-shaped string patterns, not a claim of catching every possible
# secret shape. Checked in this fixed order per line; the FIRST pattern
# to match a given line wins (see _scan_line) so a finding's own
# "{file_path}:{line}" identity (the key apply_decisions keys decisions
# by) always resolves to exactly one finding, never a same-line
# collision between two different patterns.
_SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "generic-api-key (sk-...)": re.compile(r"sk-[A-Za-z0-9]{20,}"),
    "bearer-token": re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]{16,}=*"),
    "aws-access-key": re.compile(r"AKIA[A-Z0-9]{16}"),
    "generic-hex-token (32+ chars)": re.compile(r"\b[0-9a-fA-F]{32,}\b"),
}


class SecretScanCancelledError(Exception):
    """Raised by apply_decisions when ANY finding's decision is "cancel"
    -- the whole export aborts (ADR-013, Scenario 7), never a partial
    cancel of just that one file."""


class SecretScanIncompleteError(Exception):
    """Raised by apply_decisions when a real finding has no decision at
    all -- never a silent default of "keep" or "redact" (this system's
    own "never silent" promise, Constraints)."""


def _skill_content(skill_id: str) -> dict[str, str]:
    content: dict[str, str] = {}
    skill_md = skills_data.read_skill_md(skill_id)
    if skill_md is not None:
        content[f"skills/{skill_id}/SKILL.md"] = skill_md
    for rel_path, text in skills_data.list_scripts(skill_id).items():
        content[f"skills/{skill_id}/scripts/{rel_path}"] = text
    return content


def _template_content(template_id: str) -> dict[str, str]:
    try:
        raw = templates_data.read_template_json(template_id)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {f"templates/{template_id}/Template.json": json.dumps(raw, indent=2)}


def _agent_content(agent_id: str) -> dict[str, str]:
    """Registry-side `Agent.json`/`soul.md` mirror ONLY -- reached via
    the same `registry_loader.agent_data_dir()` lookup
    `agent_visual_registry.py`/`agent_manager.py` already use. Never
    touches a Hermes profile directory or `profile.tar.gz` at all -- there
    is no code path here that could."""
    agent_dir = registry_loader.agent_data_dir(agent_id)
    if agent_dir is None:
        return {}
    content: dict[str, str] = {}
    config_path = agent_dir / "Agent.json"
    soul_path = agent_dir / "soul.md"
    if config_path.is_file():
        try:
            content[f"agents/{agent_id}/Agent.json"] = config_path.read_text(encoding="utf-8")
        except OSError:
            pass
    if soul_path.is_file():
        try:
            content[f"agents/{agent_id}/soul.md"] = soul_path.read_text(encoding="utf-8")
        except OSError:
            pass
    return content


_CONTENT_READERS = {
    "skill": _skill_content,
    "template": _template_content,
    "agent": _agent_content,
}


def _closure_text_content(closure: list[dict]) -> dict[str, tuple[str, str, str]]:
    """{file_path: (artifact_kind, artifact_id, text)} for every
    genuinely Second-Brain-owned text file the closure names. A kind with
    no reader registered above (e.g. "pipeline") contributes nothing, by
    construction."""
    content: dict[str, tuple[str, str, str]] = {}
    for entry in closure:
        kind = entry.get("kind")
        artifact_id = entry.get("id")
        reader = _CONTENT_READERS.get(kind)
        if reader is None or not artifact_id:
            continue
        for file_path, text in reader(artifact_id).items():
            content[file_path] = (kind, artifact_id, text)
    return content


def _scan_line(line: str) -> tuple[str, str] | None:
    """(matched_pattern name, matched substring) for the first pattern
    (in _SECRET_PATTERNS' own declared order) that matches this line, or
    None. First-match-wins keeps a finding's own file_path:line identity
    unique even when a line could technically match more than one
    pattern."""
    for pattern_name, pattern in _SECRET_PATTERNS.items():
        match = pattern.search(line)
        if match:
            return pattern_name, match.group(0)
    return None


def scan_closure(closure: list[dict]) -> list[dict]:
    """Scans every real Second-Brain-owned text file the resolved
    closure names for a secret-shaped string. Returns one entry per
    finding: {"artifact_kind", "artifact_id", "file_path", "line",
    "matched_pattern", "snippet"} -- an empty list when nothing matches.
    Never touches the nested Hermes profile piece (see module docstring)."""
    findings: list[dict] = []
    for file_path, (artifact_kind, artifact_id, text) in _closure_text_content(closure).items():
        for line_number, line in enumerate(text.splitlines(), start=1):
            match = _scan_line(line)
            if match is None:
                continue
            matched_pattern, _matched_substring = match
            findings.append({
                "artifact_kind": artifact_kind,
                "artifact_id": artifact_id,
                "file_path": file_path,
                "line": line_number,
                "matched_pattern": matched_pattern,
                "snippet": line.strip(),
            })
    return findings


def _finding_key(finding: dict) -> str:
    return f"{finding['file_path']}:{finding['line']}"


def apply_decisions(
    closure_content: dict[str, str],
    findings: list[dict],
    decisions: dict[str, str],
) -> dict[str, str]:
    """Applies an operator's per-finding decision ("redact" | "keep" |
    "cancel") to `closure_content` (the real, in-memory {file_path: text}
    the archive writer would otherwise write verbatim) and returns the
    resulting content dict. Never writes anything to disk itself.

    Raises SecretScanIncompleteError if any real finding has no decision
    at all -- checked BEFORE anything else, so an incomplete decision set
    never gets as far as evaluating cancel/redact/keep. Raises
    SecretScanCancelledError if any decision is "cancel" -- the whole
    export aborts; `closure_content` is never returned on this path, so
    T04's archive writer has nothing to act on."""
    for finding in findings:
        key = _finding_key(finding)
        if key not in decisions:
            raise SecretScanIncompleteError(
                f"No decision recorded for finding {key!r} -- a real finding "
                "never proceeds on an assumed default."
            )

    if any(decisions[_finding_key(finding)] == "cancel" for finding in findings):
        raise SecretScanCancelledError(
            "Operator cancelled the export at the secret-scan confirmation "
            "step -- the whole export aborts, nothing is written."
        )

    result = dict(closure_content)
    for finding in findings:
        key = _finding_key(finding)
        decision = decisions[key]
        file_path = finding["file_path"]
        if decision == "redact":
            lines = result.get(file_path, "").splitlines(keepends=True)
            line_index = finding["line"] - 1
            if 0 <= line_index < len(lines):
                pattern = _SECRET_PATTERNS.get(finding["matched_pattern"])
                if pattern is not None:
                    lines[line_index] = pattern.sub(_REDACTION_PLACEHOLDER, lines[line_index])
                    result[file_path] = "".join(lines)
        elif decision == "keep":
            # Explicit, logged acknowledgment -- never a silent
            # pass-through. The fact this branch can only run at all for
            # a key present in `decisions` (checked above) is itself the
            # "never silent" guarantee; the log line is the durable,
            # inspectable record of it.
            logger.info(
                "Secret-scan finding %s (%s) kept as-is on explicit operator decision.",
                key, finding.get("matched_pattern"),
            )
        # decision == "keep" (or any other explicitly-decided, non-redact,
        # non-cancel value) leaves that file's text byte-for-byte
        # unchanged in `result`.

    return result
