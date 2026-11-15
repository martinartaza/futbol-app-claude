#!/usr/bin/env python3
"""The files an epic changed, read from git tags: the scope of its explication.

Every ticket of an epic is tagged `v0.E.T` in the four code repositories (ADR 0004
section 6). Given the epic's closing tag, the scope of each project whose repository has
it is `git diff --name-status <previous epic's last tag> <tag> -- <project folder>`: the
previous tag is the highest `v0.X.Y` with X below E in that repository (the empty tree
for the first epic). Projects with `"explication": false` are left out. A `v0.X.0` tag
(the earlier per-requirement scheme) still takes its projects from the `projects` field
of `requirements/<X>-*.md`.

Works whether each project is its own repository or several share one (a monorepo):
tags and cleanliness are checked per repository.

Nothing is computed unless every involved project is clean (`git status --porcelain`
empty) and the tag exists in its repository: the explication must describe exactly
what was committed and tagged.

Usage: `python3 scripts/explication_scope.py v0.3.5`. It prints one tab-separated
`<project> <A|M|D|R> <path>` line per file (path relative to the project), or the
reason it stopped (exit code 1).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import workflow  # noqa: E402
from workflow import ROOT, Project  # noqa: E402

EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
# "v0.25.1" -> minor "25", patch "1"
TAG_PATTERN = re.compile(r"^v0\.(\d+)\.(\d+)$")
# "projects: [backend, app]" -> "backend, app"
PROJECTS_FIELD = re.compile(r"^projects:\s*\[(.*)\]\s*$", re.MULTILINE)

Scope = dict[str, list[tuple[str, str]]]


class ScopeError(Exception):
    """The scope cannot be computed; the message (Spanish) says why, for the user."""


def git(folder: Path, *args: str) -> str:
    """Run a read-only git command.

    Args:
        folder: where to run it.
        *args: git arguments.

    Returns:
        Its standard output.
    """
    result = subprocess.run(["git", *args], cwd=folder, capture_output=True, text=True, check=True)
    return result.stdout


def version(tag: str) -> tuple[int, int] | None:
    """The version of a `v0.X.Y` tag, comparable as numbers.

    Args:
        tag: a tag name.

    Returns:
        `(X, Y)`, or None when the tag is not `v0.X.Y`.
    """
    match = TAG_PATTERN.match(tag)
    return (int(match[1]), int(match[2])) if match else None


def has_tag(project: Project, tag: str) -> bool:
    """Whether the project's repository has the tag.

    Args:
        project: a workspace project.
        tag: tag name.

    Returns:
        True when it exists.
    """
    return tag in git(project.folder, "tag", "--list", tag).split()


def previous_tag(project: Project, tag: str) -> str | None:
    """The last tag of the previous epic in the project's repository.

    Args:
        project: a workspace project.
        tag: a `v0.E.T` tag.

    Returns:
        The highest `v0.X.Y` tag with X below E, or None when this is the first epic.
    """
    current = version(tag)
    lower = [
        (found, name)
        for name in git(project.folder, "tag", "--list").split()
        if (found := version(name)) is not None and current is not None and found[0] < current[0]
    ]
    return max(lower)[1] if lower else None


def explained() -> list[Project]:
    """Projects whose changes go into explications.

    Returns:
        Every project with `explication` true.
    """
    return [project for project in workflow.projects() if project.explication]


def touched_projects(tag: str) -> list[Project]:
    """The projects a ticket touched.

    Args:
        tag: the ticket's `v0.X.Y` tag.

    Returns:
        From the requirement for `v0.X.0`, or the projects whose repository has the tag
        for a patch tag.

    Raises:
        ScopeError: when the requirement of a `v0.X.0` tag does not exist.
    """
    minor, patch = version(tag) or (0, 0)
    if patch:
        return [project for project in explained() if has_tag(project, tag)]
    number = f"{minor:04d}"
    files = sorted((ROOT / "requirements").glob(f"{number}-*.md"))
    if not files:
        raise ScopeError(f"no existe requirements/{number}-*.md")
    field = PROJECTS_FIELD.search(files[0].read_text(encoding="utf-8"))
    named = {name.strip() for name in field[1].split(",")} if field else set()
    return [project for project in explained() if project.name in named]


def changed_files(project: Project, start: str, tag: str) -> list[tuple[str, str]]:
    """The files of a project changed between two revisions.

    Args:
        project: a workspace project.
        start: the previous epic's last tag, or the empty tree.
        tag: the epic's closing tag.

    Returns:
        `(status, path relative to the project)` pairs; a rename gives `R` and the new path.
    """
    top = Path(git(project.folder, "rev-parse", "--show-toplevel").strip())
    prefix = project.folder.relative_to(top).as_posix() if project.folder != top else ""
    files = []
    for line in git(
        top, "diff", "--name-status", "-M", start, tag, "--", prefix or "."
    ).splitlines():
        status, *paths = line.split("\t")
        path = paths[-1]
        if prefix:
            path = path[len(prefix) + 1 :]
        if (found := workflow.owner(project.folder / path)) and found.name == project.name:
            files.append((status[0], path))
    return files


def scope(tag: str) -> Scope:
    """The files an epic changed in each project that has its closing tag.

    Args:
        tag: the epic's closing tag `v0.E.T`.

    Returns:
        Project name to its `(status, path)` pairs.

    Raises:
        ScopeError: when the tag is not `v0.X.Y`, a project is dirty or lacks the tag.
    """
    if version(tag) is None:
        raise ScopeError(f"{tag} no es un tag v0.X.Y")
    projects = touched_projects(tag)
    dirty = [
        project.name
        for project in explained()
        if git(project.folder, "status", "--porcelain", "--", ".").strip()
    ]
    if dirty:
        raise ScopeError(
            f"hay cambios sin commitear en {', '.join(dirty)}: commiteá y tagueá antes de "
            "escribir la explicación"
        )
    result: Scope = {}
    for project in projects:
        if not has_tag(project, tag):
            raise ScopeError(f"falta el tag {tag} en {project.name}")
        start = previous_tag(project, tag) or EMPTY_TREE
        result[project.name] = changed_files(project, start, tag)
    return result


def main(argv: list[str]) -> int:
    """Print the scope of a tag.

    Args:
        argv: command-line arguments.

    Returns:
        0 with the scope, 1 when it cannot be computed.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    args = parser.parse_args(argv)
    try:
        found = scope(args.tag)
    except ScopeError as error:
        print(str(error), file=sys.stderr)
        return 1
    for project, files in found.items():
        for status, path in files:
            print(f"{project}\t{status}\t{path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
