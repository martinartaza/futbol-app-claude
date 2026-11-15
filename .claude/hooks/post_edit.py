#!/usr/bin/env python3
"""PostToolUse hook for Write/Edit/MultiEdit: format the touched file and check rules.

- The owner project's `on_edit` rules (`workflow.json`) for the file's extension: the
  `fix` commands first (formatters, auto-fixers), then the `check` commands, whose
  failures come back to Claude.
- Every code file: English-only identifiers, comments and docstrings
  (`scripts/check_language.py`); Python files also the comment rule
  (`scripts/check_comments.py`). Other languages carry the comment rule in their own
  linter (an ESLint rule, a detekt or SwiftLint rule), declared in `on_edit`.
- Markdown: no ASCII-art diagrams, Mermaid only. An explication (`explications/*.md`)
  must also cover its ticket's git scope and the template sections
  (`scripts/check_explication.py`).
- Generated files are skipped.

The file is also recorded in `.claude/state/<session>.edits` so the Stop hook knows
which projects to check. Problems are handed back to Claude with exit code 2.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
sys.path.insert(0, str(ROOT / "scripts"))

import workflow  # noqa: E402

SCRIPTS = ROOT / "scripts"
EXPLICATIONS = ROOT / "explications"
STATE_DIR = ROOT / ".claude" / "state"
LANGUAGE_CHECKED = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".kt",
    ".kts",
    ".swift",
    ".dart",
}


def run(argv: list[str] | list[str | Path], cwd: Path) -> tuple[int, str]:
    """Run a command and capture its combined output.

    Args:
        argv: command and arguments.
        cwd: working directory.

    Returns:
        Exit code and output; `(0, "")` when the executable is missing.
    """
    try:
        result = subprocess.run(
            [str(arg) for arg in argv], cwd=cwd, capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        return 0, ""
    return result.returncode, (result.stdout + result.stderr).strip()


def record_edit(session_id: str, path: Path) -> None:
    """Append the edited file to this session's list, read later by the Stop hook.

    Args:
        session_id: Claude Code session id.
        path: absolute path of the edited file.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with (STATE_DIR / f"{session_id}.edits").open("a", encoding="utf-8") as state:
        state.write(f"{workflow.relative(path)}\n")


def project_problems(path: Path) -> list[str]:
    """Run the owner project's `on_edit` rules for the file's extension.

    Args:
        path: absolute path of the edited file.

    Returns:
        Outputs of the `check` commands that failed.
    """
    project = workflow.owner(path)
    if project is None or not project.ready:
        return []
    problems = []
    for rule in project.on_edit:
        if path.suffix not in rule.get("extensions", []):
            continue
        for command in rule.get("fix", []):
            run(workflow.fill(command, path), project.folder)
        for command in rule.get("check", []):
            code, output = run(workflow.fill(command, path), project.folder)
            if code:
                problems.append(output)
    return problems


def rule_problems(path: Path) -> list[str]:
    """Run the workspace checkers that apply to every project.

    Args:
        path: absolute path of the edited file.

    Returns:
        Outputs of the checkers that failed.
    """
    checkers: list[list[str | Path]] = []
    if path.suffix == ".py":
        checkers.append([sys.executable, SCRIPTS / "check_comments.py", path])
    if path.suffix in LANGUAGE_CHECKED:
        checkers.append([sys.executable, SCRIPTS / "check_language.py", path])
    if path.suffix == ".md":
        checkers.append([sys.executable, SCRIPTS / "check_markdown.py", path])
        if path.parent == EXPLICATIONS:
            checkers.append([sys.executable, SCRIPTS / "check_explication.py", path])
    found = []
    for checker in checkers:
        code, output = run(checker, ROOT)
        if code:
            found.append(output)
    return found


def main() -> int:
    """Process the file touched by the tool call.

    Returns:
        2 when problems must go back to Claude, 0 otherwise.
    """
    payload = json.load(sys.stdin)
    raw_path = payload.get("tool_input", {}).get("file_path", "")
    if not raw_path:
        return 0
    path = Path(raw_path).resolve()
    if not path.is_file() or not path.is_relative_to(ROOT) or workflow.generated_rule(path):
        return 0
    record_edit(payload.get("session_id", "default"), path)
    problems = project_problems(path) + rule_problems(path)
    if problems:
        print("\n\n".join(problems), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
