#!/usr/bin/env python3
"""Check that an epic explication covers its epic: every changed file, every section.

An explication `explications/EXX-<slug>.md` is checked against the scope of its epic
(`explication_scope.py`): from the previous epic's last tag to the `tag` of the epic's
closing ticket (the requirement with `kind: epic-close` and `epic: EXX`):

- every file of the scope is named in backticks, with or without its project prefix,
  in its project's section (`section` in `workflow.json`) or in "Tests";
- every `##` section of `explications/_template.md` is there, in the template order;
  sections marked "(si aplica)" may be left out;
- there is at least one Mermaid diagram and no template placeholder (`<!--`, `NNNN`,
  `EXX`);
- the scope line says the counts with the tests apart:
  `(N archivos: B de backend, A de app y T de tests)`.

A failed precondition of the scope (no closing ticket, a dirty repository, a missing
tag) blocks too. Ticket notes (`explications/tickets/`), `*-tutorial.md`, `README.md`
and `_template.md` are not checked.

Usage: `python3 scripts/check_explication.py <file>`; exit code 2 with the problems on
stderr, so the PostToolUse hook blocks the edit.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import workflow  # noqa: E402
from explication_scope import Scope, ScopeError, scope  # noqa: E402
from workflow import ROOT  # noqa: E402

OPTIONAL = "(si aplica)"
TESTS_SECTION = "Tests"
# "E04-accounts-and-login.md" -> epic "E04"; "0025-match-list.md" -> no match
NAME_PATTERN = re.compile(r"^(E\d{2,})-[a-z0-9][a-z0-9-]*\.md$")
# "kind: epic-close" -> match
CLOSING_KIND = re.compile(r"^kind:\s*epic-close\s*$", re.MULTILINE)
# "epic: E04" -> "E04"
EPIC_FIELD = re.compile(r"^epic:\s*(E\d+)\s*$", re.MULTILINE)
# "tag: v0.3.5" -> "v0.3.5"
TAG_FIELD = re.compile(r"^tag:\s*(v0\.\d+\.\d+)\s*$", re.MULTILINE)
# "## Backend (si aplica)" -> "Backend (si aplica)"
HEADING = re.compile(r"^## (.+?)\s*$", re.MULTILINE)
# "| `app/x.py`, `src/y.tsx` |" -> "app/x.py", "src/y.tsx"
CODE_SPAN = re.compile(r"`([^`]+)`")
# "Requerimiento NNNN." -> "NNNN"; "Épica EXX." -> "EXX"; "0025" -> no match
PLACEHOLDER = re.compile(r"\b(?:NNNN|EXX)\b")


def checked_tag(path: Path) -> str | None:
    """The tag whose scope an epic explication must cover: its closing ticket's tag.

    Args:
        path: the explication file.

    Returns:
        `v0.E.T`, or None when the file is not checked (ticket notes, tutorials, other
        files).

    Raises:
        ScopeError: when the epic has no closing ticket with a tag.
    """
    if path.parent.name == "tickets" or path.name.endswith("-tutorial.md"):
        return None
    match = NAME_PATTERN.match(path.name)
    if not match:
        return None
    epic = match[1]
    for requirement in sorted((ROOT / "requirements").glob("*.md")):
        text = requirement.read_text(encoding="utf-8")
        field = EPIC_FIELD.search(text)
        tag = TAG_FIELD.search(text)
        if CLOSING_KIND.search(text) and field and field[1] == epic and tag:
            return tag[1]
    raise ScopeError(
        f"la épica {epic} no tiene ticket de cierre (kind: epic-close) con tag: cerrá la "
        "épica antes de escribir su explicación"
    )


def scope_counts(changed: Scope) -> str:
    """The counts the scope line of an explication must say.

    Args:
        changed: the ticket's scope, project to `(status, path)` pairs.

    Returns:
        For example `(6 archivos: 2 de backend, 1 de app y 3 de tests)`.
    """
    parts, tests, total = [], 0, 0
    for name, files in changed.items():
        project = workflow.by_name(name)
        if project is None:
            continue
        test_count = sum(1 for _, path in files if workflow.is_test(project.folder / path))
        tests += test_count
        total += len(files)
        parts.append(f"{len(files) - test_count} de {project.label}")
    parts.append(f"{tests} de tests")
    listed = ", ".join(parts[:-1]) + f" y {parts[-1]}"
    return f"({total} archivos: {listed})"


def template_sections() -> list[tuple[str, bool]]:
    """The `##` sections of the template, in order.

    Returns:
        `(name, required)` pairs; a "(si aplica)" section is not required.
    """
    text = (ROOT / "explications" / "_template.md").read_text(encoding="utf-8")
    return [
        (heading.replace(OPTIONAL, "").strip(), OPTIONAL not in heading)
        for heading in HEADING.findall(text)
    ]


def sections(text: str) -> dict[str, str]:
    """The `##` sections of an explication and their bodies.

    Args:
        text: the explication.

    Returns:
        Section name to its body, in document order.
    """
    found = list(HEADING.finditer(text))
    return {
        match[1].replace(OPTIONAL, "").strip(): text[
            match.end() : found[index + 1].start() if index + 1 < len(found) else len(text)
        ]
        for index, match in enumerate(found)
    }


def section_problems(found: dict[str, str]) -> list[str]:
    """Missing or misplaced template sections.

    Args:
        found: the explication's sections.

    Returns:
        One problem per missing required section, and one when the order differs.
    """
    template = template_sections()
    problems = [
        f"falta la sección «{name}» del template"
        for name, required in template
        if required and name not in found
    ]
    order = list(found)
    positions = [order.index(name) for name, _ in template if name in found]
    if positions != sorted(positions):
        expected = [name for name, _ in template if name in found]
        problems.append("las secciones no siguen el orden del template: " + " → ".join(expected))
    return problems


def file_problems(found: dict[str, str], changed: Scope) -> list[str]:
    """Scope files the explication does not name where they belong.

    Args:
        found: the explication's sections.
        changed: the ticket's scope.

    Returns:
        One problem per missing project section and per missing file.
    """
    problems = []
    for name, files in changed.items():
        project = workflow.by_name(name)
        section = project.section if project else name
        if files and section not in found:
            problems.append(f"falta la sección «{section}»: {name} cambió {len(files)} archivos")
        named = set(CODE_SPAN.findall(found.get(section, "") + found.get(TESTS_SECTION, "")))
        problems.extend(
            f"falta `{name}/{path}` ({status}) en «{section}» o «{TESTS_SECTION}»"
            for status, path in files
            if path not in named and f"{name}/{path}" not in named
        )
    return problems


def problems(path: Path) -> list[str]:
    """Everything an explication is missing.

    Args:
        path: the explication file.

    Returns:
        Human-readable problems (Spanish, for the user); empty when it is complete or
        not checked. A failed scope precondition is the only problem returned.
    """
    try:
        tag = checked_tag(path)
        if tag is None:
            return []
        changed = scope(tag)
    except ScopeError as error:
        return [str(error)]
    text = path.read_text(encoding="utf-8")
    found = sections(text)
    result = section_problems(found)
    if "```mermaid" not in text:
        result.append("falta al menos un diagrama Mermaid")
    if "<!--" in text:
        result.append("quedan comentarios del template (<!--)")
    if placeholder := PLACEHOLDER.search(text):
        result.append(f"queda {placeholder[0]} del template")
    result.extend(file_problems(found, changed))
    expected = scope_counts(changed)
    if expected not in text:
        result.append(f"el alcance debe decir «{expected}»")
    return result


def main(argv: list[str]) -> int:
    """Check one explication and report its problems.

    Args:
        argv: command-line arguments.

    Returns:
        0 when it is complete or not checked, 2 otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    args = parser.parse_args(argv)
    found = problems(args.file)
    if not found:
        return 0
    print(
        f"{args.file.name} incompleta:\n" + "\n".join(f"- {problem}" for problem in found),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
