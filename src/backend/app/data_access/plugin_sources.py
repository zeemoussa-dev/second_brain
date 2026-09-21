"""Raw data access for a plugin source OUTSIDE the framework's own Marketplace
(`REQ-SB-92`): a folder on this machine, or a git repository at a ref.

Zero business interpretation: nothing here validates a manifest, checks the
framework API or decides whether a plugin may be installed -- that is
MarketplaceManager's job. This module only produces a directory holding the
plugin's source, and says where it came from.

A git source is cloned into a temporary folder, read, and discarded. Nothing
from a source is kept beyond the pieces the install copies, so a repository is
never a second home for installed code.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

GIT = "git"
PATH = "path"
SOURCE_KINDS = (GIT, PATH)

_MANIFEST_FILENAME = "plugin.json"
_CLONE_TIMEOUT_SECONDS = 300


class SourceError(Exception):
    """Why a source could not be read, in words for the operator."""


def _git(*arguments: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    git = shutil.which(GIT)
    if git is None:
        raise SourceError("git was not found on PATH, so a repository cannot be cloned")
    try:
        return subprocess.run(
            [git, *arguments], cwd=cwd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=_CLONE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise SourceError(f"git took longer than {_CLONE_TIMEOUT_SECONDS}s and was stopped") from exc


def fetch(kind: str, location: str, ref: str | None = None) -> dict:
    """Puts a plugin's source on disk and says where it came from:
    `{"directory": Path, "source": {...}, "temporary": bool}`.

    `temporary` marks a clone the caller must `discard()`; a local folder is
    used where it is, never copied and never written to."""
    if kind == PATH:
        directory = Path(location).expanduser()
        if not directory.is_dir():
            raise SourceError(f"{directory} is not a folder on this machine")
        if not (directory / _MANIFEST_FILENAME).is_file():
            raise SourceError(f"{directory} has no {_MANIFEST_FILENAME}, so it is not a plugin")
        return {"directory": directory, "temporary": False,
                "source": {"kind": PATH, "location": str(directory)}}

    if kind != GIT:
        raise SourceError(f"unknown source kind {kind!r} -- expected one of {', '.join(SOURCE_KINDS)}")

    directory = Path(tempfile.mkdtemp(prefix="sb-plugin-source-"))
    try:
        arguments = ["clone", "--depth", "1"]
        if ref:
            # A branch or tag can be cloned directly; a commit sha cannot, and
            # falls through to the fetch below.
            arguments += ["--branch", ref]
        clone = _git(*arguments, str(location), str(directory))
        if clone.returncode != 0 and ref:
            clone = _git("clone", str(location), str(directory))
            if clone.returncode == 0:
                checkout = _git("checkout", ref, cwd=directory)
                if checkout.returncode != 0:
                    raise SourceError(f"{ref!r} is not a branch, tag or commit in that repository")
        if clone.returncode != 0:
            raise SourceError(f"the repository could not be cloned: {clone.stderr.strip()[-400:]}")
        if not (directory / _MANIFEST_FILENAME).is_file():
            raise SourceError(f"that repository has no {_MANIFEST_FILENAME} at its root, so it is not a plugin")
        revision = _git("rev-parse", "HEAD", cwd=directory)
        return {
            "directory": directory, "temporary": True,
            "source": {"kind": GIT, "location": str(location), "ref": ref or None,
                       "commit": revision.stdout.strip() if revision.returncode == 0 else None},
        }
    except BaseException:
        discard(directory)
        raise


def discard(directory: Path | None) -> None:
    """Removes a cloned source. Never raises: a leftover temporary folder is not
    worth failing an install that otherwise succeeded.

    git writes its object and pack files read-only, and on Windows a read-only
    file is simply not deleted -- so a plain `ignore_errors` delete left every
    clone behind in the temp folder."""
    if directory is None:
        return

    def retry_writable(function, failed_path, _exc_info):
        try:
            os.chmod(failed_path, stat.S_IWRITE)
            function(failed_path)
        except OSError:
            pass

    shutil.rmtree(Path(directory), onerror=retry_writable)


def read_manifest(directory: Path) -> dict:
    """Raises SourceError rather than leaking a parse error to the caller."""
    path = Path(directory) / _MANIFEST_FILENAME
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SourceError(f"{_MANIFEST_FILENAME} cannot be read: {exc}") from exc
    if not isinstance(manifest, dict):
        raise SourceError(f"{_MANIFEST_FILENAME} must hold a JSON object")
    return manifest
