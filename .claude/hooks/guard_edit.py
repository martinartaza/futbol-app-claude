#!/usr/bin/env python3
"""PreToolUse hook for Write/Edit/MultiEdit: generated files, reuse and the TDD lock.

- **Generated files** (`generated` in `workflow.json`, e.g. migrations): writing one is
  denied with the command that generates it; editing a generated one asks the user,
  because a generator can miss things (a rename, a data backfill).
- **Reuse before creating** (`reuse_guard` in `workflow.json`, e.g. UI components):
  the first attempt to create a new file under those globs is denied and the existing
  files are listed, most similar names first. The second attempt goes through.
- **TDD** (CLAUDE.md rule 2, `scripts/tdd.py`):

  | Phase | Source code | Tests |
  |---|---|---|
  | none (no task) | ask the user | ask the user |
  | red | denied | free |
  | green | free | ask the user |
  | direct (`start --direct`) | free | free |

  The TDD state file can never be edited, and `.claude/settings*.json` (which turns the
  hooks on or off) and `workflow.json` (which says what is source) always ask the user.
"""

from __future__ import annotations

import difflib
import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
sys.path.insert(0, str(ROOT / "scripts"))

import tdd  # noqa: E402
import workflow  # noqa: E402

STATE_DIR = ROOT / ".claude" / "state"
PROTECTED = {".claude/settings.json", ".claude/settings.local.json", "workflow.json"}
CATALOG_SIZE = 25


def decision(permission: str, reason: str) -> None:
    """Print a PreToolUse decision for Claude Code.

    Args:
        permission: "allow", "deny" or "ask".
        reason: message shown to Claude (deny) or to the user (ask).
    """
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": permission,
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def generated_decision(tool: str, path: Path) -> tuple[str, str] | None:
    """Decision for a file that a generator owns.

    Args:
        tool: name of the tool being called.
        path: file about to be written.

    Returns:
        `(permission, reason)`, or None when the file is not generated.
    """
    rule = workflow.generated_rule(path)
    if rule is None:
        return None
    if (tool == "Write" and not path.exists()) or rule.get("edit") == "deny":
        return (
            "deny",
            f"{workflow.relative(path)} is generated, never written by hand. {rule['how']}",
        )
    return (
        "ask",
        f"Claude wants to edit a generated file: {workflow.relative(path)}. Approve only if "
        "the generator missed something it cannot detect (a rename, a data backfill).",
    )


def first_attempt(session_id: str, path: Path) -> bool:
    """Record a creation attempt and tell whether it is the first one in the session.

    Args:
        session_id: Claude Code session id.
        path: file about to be created.

    Returns:
        True the first time this path is seen in the session.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state = STATE_DIR / f"{session_id}.created"
    seen = set(state.read_text(encoding="utf-8").split()) if state.exists() else set()
    key = path.as_posix()
    if key in seen:
        return False
    with state.open("a", encoding="utf-8") as handle:
        handle.write(f"{key}\n")
    return True


def catalog(project: workflow.Project, stem: str) -> list[str]:
    """Existing files under the reuse globs, most similar names first.

    Args:
        project: the owner project.
        stem: name of the file about to be created, without extension.

    Returns:
        Project-relative paths, at most `CATALOG_SIZE`.
    """
    globs = project.reuse_guard.get("globs", [])
    found = [
        path.relative_to(project.folder).as_posix()
        for path in project.folder.rglob("*")
        if path.is_file()
        and workflow.matches(path.relative_to(project.folder).as_posix(), globs)
        and not workflow.is_test(path)
    ]
    score = {
        name: difflib.SequenceMatcher(None, stem.lower(), Path(name).stem.lower()).ratio()
        for name in found
    }
    return sorted(found, key=lambda name: (-score[name], name))[:CATALOG_SIZE]


def reuse_decision(tool: str, path: Path, session_id: str) -> tuple[str, str] | None:
    """Deny the first creation of a reusable kind of file and show what exists.

    Args:
        tool: name of the tool being called.
        path: file about to be written.
        session_id: Claude Code session id.

    Returns:
        `(permission, reason)` on the first attempt, None otherwise.
    """
    project = workflow.owner(path)
    if tool != "Write" or path.exists() or project is None or not project.reuse_guard:
        return None
    inner = project.inner(workflow.relative(path))
    if workflow.is_test(path) or not workflow.matches(inner, project.reuse_guard.get("globs", [])):
        return None
    if not first_attempt(session_id, path):
        return None
    listing = "\n".join(f"- {name}" for name in catalog(project, path.stem)) or "(none yet)"
    hint = project.reuse_guard.get("hint", "Reuse, extend or compose an existing one.")
    return (
        "deny",
        f"Reuse before creating. Before {workflow.relative(path)}, check these:\n\n{listing}\n\n"
        f"{hint} If none fits, tell the user in one line why, then write the file again: "
        "the second attempt is allowed.",
    )


def tdd_decision(path: Path) -> tuple[str, str] | None:
    """Decision of the TDD workflow for editing a file, if it restricts it.

    Args:
        path: file about to be written or edited.

    Returns:
        `(permission, reason)` when the edit is denied or needs the user, else None.
    """
    rel = workflow.relative(path)
    if path == tdd.STATE:
        return "deny", "The TDD state changes only through `python3 scripts/tdd.py`."
    if rel in PROTECTED:
        return (
            "ask",
            f"Claude wants to change {rel}, which turns the workflow rules on or off. "
            "Approve only if you asked for this change.",
        )
    source, test = workflow.is_source(path), workflow.is_test(path)
    if not source and not test:
        return None
    current = tdd.load()
    phase = current["phase"]
    if phase == tdd.NONE:
        kind = "source code" if source else "a test"
        return (
            "ask",
            f"No TDD task is active and Claude wants to change {kind}: {rel}. Approve only "
            "if you asked for this change; Claude should start a task "
            "(`python3 scripts/tdd.py start <task>`, or `--direct` for a direct change).",
        )
    if phase == tdd.RED and source:
        return (
            "deny",
            f"Task '{current['task']}' is in RED: only tests may be written. Finish the "
            "tests, run them, show the user that they fail, and ask to move to green "
            "(`python3 scripts/tdd.py green`). Skill `testing`.",
        )
    if phase == tdd.GREEN and test:
        return (
            "ask",
            f"Task '{current['task']}' is in GREEN and Claude wants to change a test: {rel}. "
            "Approved tests change only with your permission for this specific case.",
        )
    return None


def main() -> int:
    """Read the tool call from stdin and apply the guards in order.

    Returns:
        Always 0; the decision travels in the JSON printed to stdout.
    """
    payload = json.load(sys.stdin)
    raw_path = payload.get("tool_input", {}).get("file_path", "")
    if not raw_path:
        return 0
    tool = payload.get("tool_name", "")
    path = Path(os.path.normpath(raw_path))
    session_id = payload.get("session_id", "default")
    guards = (
        lambda: generated_decision(tool, path),
        lambda: reuse_decision(tool, path, session_id),
        lambda: tdd_decision(path),
    )
    for guard in guards:
        found = guard()
        if found:
            decision(*found)
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
