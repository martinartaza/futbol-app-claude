#!/usr/bin/env python3
"""The projects of the workspace, read from `workflow.json`, and what each file is.

Every tool of the workflow (TDD state machine, edit and shell guards, post-edit
formatting, Stop checks, explication scope) asks this module the same questions:

- which project owns a file (the one whose `path` is the longest prefix of it);
- whether the file is a test, source code under TDD, or neither;
- which commands format, lint and test that project.

`workflow.json` lives at the workspace root. Shape of one project:

    "backend": {
      "path": "backend",                     folder, relative to the root ("." allowed)
      "label": "backend",                    word used in file counts ("de backend")
      "section": "Backend",                  explication section that lists its files
      "requires": ".venv",                   tools run only when this path exists
      "source": ["app/**/*.py"],             globs, relative to `path`
      "tests": ["tests/**/*.py"],            globs, relative to `path`
      "runnable_tests": ["test_*.py"],       file-name globs a runner can execute
      "test_command": ["uv", "run", "pytest", "-q"],
      "no_tests_exit_codes": [5],
      "no_tests_output": "",
      "checks": [{"name": "ruff", "command": ["uv", "run", "ruff", "check", "."]}],
      "on_edit": [{"extensions": [".py"], "fix": [[...,"{file}"]], "check": [[...,"{file}"]]}],
      "generated": [{"glob": "alembic/versions/*.py", "generator": "alembic revision",
                     "how": "Generate it with ..."},
                    {"glob": "uv.lock", "generator": "uv lock", "how": "...",
                     "edit": "deny"}],      "deny": never edited by hand either
                                            (default: editing an existing one asks)
      "reuse_guard": {"globs": ["src/components/**/*.tsx"], "hint": "..."},
      "explication": true
    }

Commands run with the project folder as working directory; `{file}` is replaced by the
edited file's absolute path. Globs use `pathlib` full matching: `**` spans folders,
braces (`*.{ts,tsx}`) are not supported, so each extension is listed. Requires
Python 3.13 or newer.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[1])
CONFIG = ROOT / "workflow.json"
WILDCARDS = set("*?[")


@dataclass(frozen=True)
class Project:
    """One project of the workspace and its tools."""

    name: str
    path: str
    label: str
    section: str
    requires: str | None
    source: tuple[str, ...]
    tests: tuple[str, ...]
    runnable_tests: tuple[str, ...]
    test_command: tuple[str, ...]
    no_tests_exit_codes: tuple[int, ...]
    no_tests_output: str
    checks: tuple[tuple[str, tuple[str, ...]], ...]
    on_edit: tuple[dict[str, Any], ...]
    generated: tuple[dict[str, str], ...]
    reuse_guard: dict[str, Any] = field(default_factory=dict)
    explication: bool = True

    @property
    def folder(self) -> Path:
        """Absolute folder of the project.

        Returns:
            The root joined with `path`.
        """
        return (ROOT / self.path).resolve() if self.path != "." else ROOT

    @property
    def ready(self) -> bool:
        """Whether the project's tools are installed.

        Returns:
            True when `requires` is unset or exists inside the project folder.
        """
        return self.requires is None or (self.folder / self.requires).exists()

    def inner(self, rel: str) -> str:
        """A workspace-relative path, made relative to this project.

        Args:
            rel: path relative to the workspace root.

        Returns:
            The same path relative to the project folder.
        """
        return rel if self.path == "." else rel[len(self.path) + 1 :]


def project_from(name: str, raw: dict[str, Any]) -> Project:
    """Build a project from its JSON entry, with defaults.

    Args:
        name: key of the project in `workflow.json`.
        raw: its JSON object.

    Returns:
        The project.
    """
    return Project(
        name=name,
        path=raw.get("path", name).strip("/") or ".",
        label=raw.get("label", name),
        section=raw.get("section", name.capitalize()),
        requires=raw.get("requires"),
        source=tuple(raw.get("source", [])),
        tests=tuple(raw.get("tests", [])),
        runnable_tests=tuple(raw.get("runnable_tests", [])),
        test_command=tuple(raw.get("test_command", [])),
        no_tests_exit_codes=tuple(raw.get("no_tests_exit_codes", [])),
        no_tests_output=raw.get("no_tests_output", ""),
        checks=tuple((check["name"], tuple(check["command"])) for check in raw.get("checks", [])),
        on_edit=tuple(raw.get("on_edit", [])),
        generated=tuple(raw.get("generated", [])),
        reuse_guard=raw.get("reuse_guard", {}),
        explication=raw.get("explication", True),
    )


@cache
def projects() -> tuple[Project, ...]:
    """Every project declared in `workflow.json`.

    Returns:
        The projects in file order; empty when the file does not exist yet.
    """
    if not CONFIG.exists():
        return ()
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    return tuple(project_from(name, raw) for name, raw in data.get("projects", {}).items())


def by_name(name: str) -> Project | None:
    """A project by its name.

    Args:
        name: key in `workflow.json`.

    Returns:
        The project, or None.
    """
    return next((project for project in projects() if project.name == name), None)


def relative(path: Path | str) -> str:
    """Path relative to the workspace root, with forward slashes, links not followed.

    Args:
        path: absolute or root-relative path.

    Returns:
        The relative path, or the absolute one when it is outside the workspace.
    """
    raw = Path(path)
    absolute = Path(os.path.normpath(raw if raw.is_absolute() else ROOT / raw))
    try:
        return absolute.relative_to(ROOT).as_posix()
    except ValueError:
        return absolute.as_posix()


def owner(path: Path | str) -> Project | None:
    """The project a file belongs to: the one with the longest matching folder.

    Args:
        path: file path.

    Returns:
        The project, or None when the file is outside every project.
    """
    rel = relative(path)
    if rel.startswith("/"):
        return None
    candidates = [
        project
        for project in projects()
        if project.path == "." or rel == project.path or rel.startswith(project.path + "/")
    ]
    return max(candidates, key=lambda project: len(project.path), default=None)


def matches(rel: str, globs: tuple[str, ...] | list[str]) -> bool:
    """Whether a project-relative path matches any glob (`**` spans folders).

    Args:
        rel: path relative to the project.
        globs: glob patterns.

    Returns:
        True on the first match.
    """
    candidate = PurePosixPath(rel)
    return any(candidate.full_match(pattern) for pattern in globs)


def is_test(path: Path | str) -> bool:
    """Whether a file is a test or test support of its project.

    Args:
        path: file path.

    Returns:
        True when it matches the owner's `tests` globs.
    """
    project = owner(path)
    return project is not None and matches(project.inner(relative(path)), project.tests)


def is_source(path: Path | str) -> bool:
    """Whether a file is implementation under the TDD workflow.

    Args:
        path: file path.

    Returns:
        True when it matches the owner's `source` globs and is not a test.
    """
    project = owner(path)
    if project is None or is_test(path):
        return False
    return matches(project.inner(relative(path)), project.source)


def is_runnable_test(path: Path | str) -> bool:
    """Whether a test file is one the runner executes (not a fixture or a fake).

    Args:
        path: file path.

    Returns:
        True when its name matches the owner's `runnable_tests` globs.
    """
    project = owner(path)
    return (
        project is not None
        and is_test(path)
        and any(PurePosixPath(Path(path).name).full_match(name) for name in project.runnable_tests)
    )


def generated_rule(path: Path | str) -> dict[str, str] | None:
    """The generated-files rule a path falls under, if any.

    Args:
        path: file path.

    Returns:
        The `{"glob", "how"}` entry, or None.
    """
    project = owner(path)
    if project is None:
        return None
    inner = project.inner(relative(path))
    return next((rule for rule in project.generated if matches(inner, (rule["glob"],))), None)


def static_prefix(glob: str) -> str:
    """The folder part of a glob before its first wildcard.

    Args:
        glob: a glob such as `app/**/*.py`.

    Returns:
        The fixed prefix, e.g. `app`; empty when the glob starts with a wildcard.
    """
    parts: list[str] = []
    for part in glob.split("/"):
        if WILDCARDS & set(part):
            break
        parts.append(part)
    return "/".join(parts)


def folders(kind: str) -> tuple[str, ...]:
    """Workspace-relative folders that hold sources or tests, for shell heuristics.

    Args:
        kind: "source" or "tests".

    Returns:
        Folder prefixes, deduplicated.
    """
    found: list[str] = []
    for project in projects():
        for glob in getattr(project, kind):
            prefix = static_prefix(glob)
            if not prefix or "." in PurePosixPath(prefix).name:
                continue
            found.append(prefix if project.path == "." else f"{project.path}/{prefix}")
    return tuple(dict.fromkeys(found))


def fill(command: tuple[str, ...] | list[str], file: Path | None = None) -> list[str]:
    """A command with `{file}` replaced.

    Args:
        command: command template.
        file: edited file, when the command needs one.

    Returns:
        The command ready to run.
    """
    return [part.replace("{file}", str(file)) if file else part for part in command]
