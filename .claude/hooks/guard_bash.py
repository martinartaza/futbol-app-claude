#!/usr/bin/env python3
"""PreToolUse hook for Bash: git confirmation, generated files and the TDD lock.

- `git commit` and `git push` always ask the user first, even in auto mode.
- A shell command that writes into a generated folder (`generated` in `workflow.json`)
  is denied, unless it is the generator itself; deleting a generated file asks.
- `tdd.py green` is the user's approval of the failing tests, `tdd.py start --direct`
  the one approval of a direct change, and `tdd.py abort` drops a task, so the three
  always ask. Writing to the TDD state from the shell, or importing
  `tdd` to change it, is denied; reading it is fine.
- The TDD lock also holds from the shell. A command that writes, deletes or restores a
  file (`>`, `tee`, `sed -i`, `cp`, `mv`, `rm`, `git checkout/restore`, formatters and
  fixers, `git apply`, `patch`, scripts run by an interpreter...) is judged by the files
  it mentions, like the edit guard judges Write/Edit. A fixer with no path counts as
  touching source; an interpreter script with no known path asks in red. Heredoc
  bodies and quoted strings are not read as operators. This is a heuristic: it closes
  the likely paths, not every possible one.
- Tests and database commands (pytest, alembic except `alembic revision`, any
  project's `test_command`) are denied unless they run through
  `scripts/run_locked.py`, which holds the workspace test lock so two sessions or
  subagents never run them at once.

  | Phase | Source code | Tests |
  |---|---|---|
  | none | ask | ask |
  | red | deny | allow |
  | green | allow | ask |
  | direct | allow | allow |
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
sys.path.insert(0, str(ROOT / "scripts"))

import tdd  # noqa: E402
import workflow  # noqa: E402

# "git -C x commit -m 'a'" -> match "commit"; "git log --oneline" -> no match
GIT_WRITE = re.compile(r"\bgit\b(?:\s+-\S+(?:\s+\S+)?)*\s+(commit|push)\b")
# "cmd 2>&1" -> removed; "cmd > /dev/null" -> removed; "cat > a.py" -> kept
HARMLESS_REDIRECT = re.compile(r"\d*>&\d+|\d*>\s*/dev/null")
# "cat <<'EOF'\nstep -> next\nEOF" -> "cat <<'EOF'\n" (the body is text, not shell)
HEREDOC_BODY = re.compile(r"(<<-?\s*(['\"]?)(\w+)\2[^\n]*)\n.*?(?:\n\s*\3\s*(?=\n|$)|$)", re.DOTALL)
# "grep 'a -> b' x" -> "grep  x"; 'echo "x" >> f' -> "echo  >> f"
QUOTED = re.compile(r"'[^']*'|\"(?:\\.|[^\"\\])*\"")
# "cat > a.py" -> match; "cat >> a.py" -> match; "a -> b" -> no match; "a => b" -> no match
REDIRECT = re.compile(r"(?<![-=<>])>{1,2}")
# "sed -i '' s/a/b/ x" -> match; "git restore x" -> match; "rsync a b" -> match
SHELL_WRITE = re.compile(
    r"\bsed\s+-i|\bperl\s+-[ip]|\bcp\b|\bmv\b|\btouch\b|\brm\b|\bunlink\b"
    r"|\btruncate\b|\bln\b|\brsync\b|\bdd\b.*\bof="
    r"|\bgit\b.*\b(?:checkout|restore|reset|clean|stash|rm)\b"
)
# "npx prettier --write src" -> match; "ruff format x" -> match; "dart format ." -> match
FIXER = re.compile(
    r"\bprettier\b.*--write|\beslint\b.*--fix|\bruff\s+format\b|\bruff\b.*--fix"
    r"|\bblack\b|\bisort\b|\bdart\s+(?:format|fix)\b|\bktlint\b.*(?:-F|--format)"
    r"|\bswiftformat\b|\bswiftlint\b.*--fix|\bgit\s+apply\b|\bpatch\b"
    r"|\bnpm\s+run\s+(?:format|lint:fix)\b|\bnpm\s+run\s+lint\b.*--fix"
)
# "cat > out.txt" -> "out.txt"; "cmd >> /tmp/log" -> "/tmp/log"
REDIRECT_TARGET = re.compile(r"(?<![-=<>])>{1,2}\s*([^\s;|&<>()]+)")
# "echo x | tee -a /tmp/log" -> "/tmp/log"
TEE_TARGET = re.compile(r"\btee\s+(?:-a\s+)?([^\s;|&<>()]+)")
# "python3 -c ..." -> match; "python3 - <<EOF" -> match; "bash -c ..." -> match
INTERPRETER = re.compile(
    r"\bpython3?\s+(?:-c\b|-(?=\s|$)|<<)|\b(?:ba|z)?sh\s+-c\b|\bnode\s+-e\b|\bperl\s+-e\b"
)
# "rm alembic/versions/2026_x.py" -> match
SHELL_REMOVE = re.compile(r"\brm\b")
# "python3 scripts/tdd.py green" -> match "green"; "python3 scripts/tdd.py status" -> no match
TDD_APPROVAL = re.compile(r"\btdd\.py\s+(green|abort)\b")
# "python3 scripts/tdd.py start scaffolding --direct" -> match; "tdd.py start 0002-add" -> no match
TDD_DIRECT_START = re.compile(r"\btdd\.py\s+start\b[^;&|\n]*\s--direct\b")
# "python3 -c 'import tdd'" -> match; "from tdd import save" -> match
TDD_IMPORT = re.compile(r"\bimport\s+tdd\b|\bfrom\s+tdd\s+import\b")
# "rm -rf .claude/state" -> match; ".claude/state/tdd.json" -> match
STATE_PATH = re.compile(r"\.claude/state\b|\btdd\.json\b")
# "backend/app/main.py" -> match; "'backend/app/x.py'" -> match "backend/app/x.py"
PATH_LIKE = re.compile(r"[\w.-]*(?:/[\w.-]+)+")
# "cd backend && uv run pytest | tail" -> ["cd backend ", " uv run pytest ", " tail"]
SEGMENT = re.compile(r"&&|\|\||[;|\n]")
# "DEBUG=1" -> match; "--python" -> no match
ENV_ASSIGNMENT = re.compile(r"^\w+=")
# "pytest==9.2.0" -> "pytest"; "ruff@0.17" -> "ruff"
VERSION_SUFFIX = re.compile(r"(?:==|@).*$")
LOCKED_TOOLS = {"pytest", "alembic"}
LAUNCHERS = {
    "uv",
    "uvx",
    "npx",
    "pnpm",
    "docker",
    "python",
    "python3",
    "poetry",
    "pipx",
    "env",
    "time",
    "exec",
}
WRAPPER = "run_locked.py"
PYTHONS = {"python", "python3"}
PACKAGE_MANAGERS = {"uv", "pnpm", "npm", "poetry", "pipx", "pip", "pip3"}
PACKAGE_SUBCOMMANDS = {"add", "remove", "pip", "sync", "lock", "install", "uninstall"}


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


def shell_part(command: str) -> str:
    """The part of a command that the shell interprets as operators.

    Args:
        command: shell command.

    Returns:
        The command without heredoc bodies, quoted strings and harmless redirections.
    """
    without_bodies = HEREDOC_BODY.sub(lambda match: match.group(1) + "\n", command)
    return HARMLESS_REDIRECT.sub(" ", QUOTED.sub(" ", without_bodies))


def writes(command: str) -> bool:
    """Whether a command may write, delete or restore files.

    Args:
        command: shell command.

    Returns:
        True for redirections, file tools, fixers and scripts run by an interpreter.
    """
    shell = shell_part(command)
    return any(
        pattern.search(shell) for pattern in (REDIRECT, TEE_TARGET, SHELL_WRITE, FIXER, INTERPRETER)
    )


def kind_of(candidate: str) -> str | None:
    """Classify a path mentioned in a command.

    Args:
        candidate: path relative to the workspace, or absolute.

    Returns:
        "test", "source" or None.
    """
    rel = workflow.relative(candidate)
    if workflow.is_test(ROOT / rel) or any(
        rel == folder or rel.startswith(f"{folder}/") for folder in workflow.folders("tests")
    ):
        return "test"
    if workflow.is_source(ROOT / rel) or any(
        rel == folder or rel.startswith(f"{folder}/") for folder in workflow.folders("source")
    ):
        return "source"
    return None


def touched_kinds(command: str) -> set[str]:
    """Kinds of files a command mentions, trying each path from the root and each project.

    Args:
        command: shell command.

    Returns:
        A subset of {"source", "test"}.
    """
    prefixes = ["", *(f"{project.path}/" for project in workflow.projects() if project.path != ".")]
    kinds: set[str] = set()
    for candidate in PATH_LIKE.findall(command):
        for prefix in prefixes:
            kind = kind_of(prefix + candidate)
            if kind:
                kinds.add(kind)
                break
    return kinds


def written_kinds(command: str) -> set[str]:
    """Kinds of project files a command may write.

    Args:
        command: shell command.

    Returns:
        A subset of {"source", "test"}.
    """
    shell = shell_part(command)
    targets = REDIRECT_TARGET.findall(shell) + TEE_TARGET.findall(shell)
    kinds = set().union(*(touched_kinds(target) for target in targets))
    if SHELL_WRITE.search(shell) or FIXER.search(shell):
        kinds |= touched_kinds(shell)
    if INTERPRETER.search(shell):
        kinds |= touched_kinds(command)
    if FIXER.search(shell) and not kinds:
        kinds.add("source")
    return kinds


def tdd_shell_decision(command: str) -> tuple[str, str] | None:
    """Decision of the TDD lock for a command that writes files.

    Args:
        command: shell command.

    Returns:
        `(permission, reason)` when the command is denied or needs the user, else None.
    """
    if not writes(command):
        return None
    shell = shell_part(command)
    kinds = written_kinds(command)
    current = tdd.load()
    phase = current["phase"]
    if not kinds:
        if INTERPRETER.search(shell) and phase == tdd.RED:
            return (
                "ask",
                f"Task '{current['task']}' is in RED and Claude wants to run a script through "
                "an interpreter that may write files. Approve only if it does not change code.",
            )
        return None
    if phase == tdd.NONE:
        return (
            "ask",
            "No TDD task is active and this shell command changes code or tests. Approve "
            "only if you asked for this direct change.",
        )
    if phase == tdd.RED and "source" in kinds:
        return (
            "deny",
            f"Task '{current['task']}' is in RED: source code is locked, also from the shell. "
            "Write the tests only (skill `testing`).",
        )
    if phase == tdd.GREEN and "test" in kinds:
        return (
            "ask",
            f"Task '{current['task']}' is in GREEN and this shell command changes approved "
            "tests. Approve only for this specific case.",
        )
    return None


def generated_shell_decision(command: str) -> tuple[str, str] | None:
    """Decision for a shell command that touches a generated folder.

    Args:
        command: shell command.

    Returns:
        `(permission, reason)`, or None when no generated folder is mentioned.
    """
    for project in workflow.projects():
        for rule in project.generated:
            folder = workflow.static_prefix(rule["glob"])
            full = folder if project.path == "." else f"{project.path}/{folder}"
            if not folder or (full not in command and folder not in command):
                continue
            if rule.get("generator") and rule["generator"] in command:
                return None
            if SHELL_REMOVE.search(shell_part(command)):
                return "ask", f"Claude wants to delete a generated file under {full}."
            if writes(command):
                return "deny", f"Files under {full} are generated, never written. {rule['how']}"
    return None


def tool_name(token: str) -> str:
    """The program a command token names, without folder or pinned version.

    Args:
        token: one word of a command.

    Returns:
        The bare program name (`.venv/bin/pytest` and `pytest==9.2.0` give `pytest`).
    """
    return VERSION_SUFFIX.sub("", Path(token).name)


def wrapped(names: list[str]) -> bool:
    """Whether a simple command runs through the test lock wrapper.

    Args:
        names: program names of the command's words.

    Returns:
        True when the program, or the script given to python, is `run_locked.py`.
    """
    return names[0] == WRAPPER or (names[0] in PYTHONS and names[1:2] == [WRAPPER])


def package_command(names: list[str]) -> bool:
    """Whether a simple command manages packages instead of running them.

    Args:
        names: program names of the command's words.

    Returns:
        True for `uv add pytest`, `uv pip install pytest`, `python3 -m pip ...` and alike.
    """
    if names[0] in PACKAGE_MANAGERS and names[1:2] and names[1] in PACKAGE_SUBCOMMANDS:
        return True
    return names[0] in PYTHONS and names[1:3] == ["-m", "pip"]


def needs_lock(segment: str) -> bool:
    """Whether one simple command runs tests or database commands.

    Args:
        segment: one command of a pipeline or list, without quoted strings.

    Returns:
        True for pytest and alembic, run directly or through a launcher, and for the
        `test_command` of any project. `alembic revision` is free: it only compares the
        models with the development database and writes a migration file.
    """
    tokens = [token for token in segment.split() if not ENV_ASSIGNMENT.match(token)]
    if not tokens:
        return False
    names = [tool_name(token) for token in tokens]
    if wrapped(names) or package_command(names):
        return False
    if "alembic" in names and names[names.index("alembic") + 1 :][:1] == ["revision"]:
        return False
    if names[0] in LOCKED_TOOLS or (names[0] in LAUNCHERS and LOCKED_TOOLS & set(names)):
        return True
    return any(
        project.test_command and tokens[: len(project.test_command)] == list(project.test_command)
        for project in workflow.projects()
    )


def lock_decision(command: str) -> tuple[str, str] | None:
    """Decision for a test or database command run outside the test lock.

    Args:
        command: shell command.

    Returns:
        A denial pointing to `scripts/run_locked.py`, or None.
    """
    if not any(needs_lock(segment) for segment in SEGMENT.split(shell_part(command))):
        return None
    return (
        "deny",
        "Tests and database commands run one at a time under the workspace test lock. "
        "Run it as `python3 <workspace>/scripts/run_locked.py -- <command>` from the "
        "folder the command needs (it runs in the current folder); it waits while another "
        "session or subagent holds the lock.",
    )


def main() -> int:
    """Read the Bash command from stdin and decide whether it needs the user.

    Returns:
        Always 0; the decision travels in the JSON printed to stdout.
    """
    command = json.load(sys.stdin).get("tool_input", {}).get("command", "")
    git_write = GIT_WRITE.search(command)
    if git_write:
        decision("ask", f"git {git_write.group(1)} needs your explicit confirmation.")
        return 0
    tdd_approval = TDD_APPROVAL.search(command)
    if tdd_approval:
        reason = {
            "green": "Claude asks to move the TDD task to GREEN: you approve the failing "
            "tests shown and allow the implementation to start.",
            "abort": "Claude asks to abort the current TDD task.",
        }[tdd_approval.group(1)]
        decision("ask", reason)
        return 0
    if TDD_DIRECT_START.search(command):
        decision(
            "ask",
            "Claude asks to start a direct change (no red tests): this is your one approval; "
            "until `tdd.py done`, source and tests are edited without asking.",
        )
        return 0
    if TDD_IMPORT.search(command) or (STATE_PATH.search(command) and writes(command)):
        decision("deny", "The TDD state changes only through `python3 scripts/tdd.py`.")
        return 0
    for found in (
        lock_decision(command),
        generated_shell_decision(command),
        tdd_shell_decision(command),
    ):
        if found:
            decision(*found)
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
