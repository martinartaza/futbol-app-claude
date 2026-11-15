#!/usr/bin/env python3
"""Stop hook: run quality checks and tests of the projects touched in this session.

It reads the files recorded by `post_edit.py` and, for every touched project of
`workflow.json` whose tools are installed (`requires`), runs its `checks` (lint, types,
architecture contracts) and the tests of the current ticket only: its own test files,
or every suite in an epic's closing ticket (ADR 0004 section 6).

When everything passes the record is cleared. When something fails Claude is sent back
(exit 2) with the output and the test-failure policy of the current TDD phase
(`scripts/tdd.py`). In the red phase failing tests are the goal, so only check failures
send Claude back.

Everything runs under the workspace test lock (`scripts/run_locked.py`), so a session
and a subagent never run tests at the same time.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
sys.path.insert(0, str(ROOT / "scripts"))

import run_locked  # noqa: E402
import tdd  # noqa: E402
import workflow  # noqa: E402

STATE_DIR = ROOT / ".claude" / "state"

TEST_POLICY = {
    tdd.GREEN: """\
TEST FAILURE POLICY, GREEN phase (CLAUDE.md rule 2, skill `testing`):
1. The tests were approved by the user: keep implementing until they pass.
2. Change the implementation, never the tests. If a test itself seems wrong, stop and
   ask the user for permission for that specific test (the edit guard asks too).
3. Never add code whose only purpose is to make a test pass (special cases for test
   inputs, swallowed exceptions).""",
    tdd.DIRECT: """\
TEST FAILURE POLICY, direct change (CLAUDE.md rule 2, skill `testing`):
1. Tests the direct change touched fail: fix the change if the failure is yours.
2. If a test written before this change fails, do not change it on your own: tell the
   user, in Spanish, which behaviour fails, why, and what you propose.""",
    tdd.NONE: """\
TEST FAILURE POLICY, no TDD task (CLAUDE.md rule 2, skill `testing`):
1. Tests fail outside a TDD task: do not change tests or code on your own.
2. Tell the user, in Spanish, which behaviour fails, why, and what you propose.
   Wait for explicit permission.""",
}


def run(name: str, argv: list[str], cwd: Path) -> str | None:
    """Run one check.

    Args:
        name: label for the report.
        argv: command.
        cwd: working directory.

    Returns:
        The last lines of output when the check fails, None when it passes or its
        executable is not installed.
    """
    try:
        result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None
    if result.returncode == 0:
        return None
    output = (result.stdout + result.stderr).strip().splitlines()
    return f"--- {name}\n" + "\n".join(output[-40:])


def touched_projects(edits: set[str]) -> list[workflow.Project]:
    """Projects that own a recorded source or test file and have their tools installed.

    Args:
        edits: paths relative to the workspace root.

    Returns:
        The projects, in `workflow.json` order.
    """
    names = {
        project.name
        for edit in edits
        if (project := workflow.owner(edit))
        and (workflow.is_source(edit) or workflow.is_test(edit))
    }
    return [project for project in workflow.projects() if project.name in names and project.ready]


def selected_tests(projects: list[workflow.Project]) -> dict[str, list[Path] | None]:
    """The tests to run for the touched projects.

    Inside a task, the task's own tests (`tdd.task_tests`: its test files, or every
    suite for an epic's closing ticket), so older tests run only in the closing ticket
    (ADR 0004 section 6). Outside a task (a direct change) no ticket says which tests
    are its own, so the whole suite of each touched project runs.

    Args:
        projects: the touched projects.

    Returns:
        `{project name: paths}`; None as paths means the whole suite.
    """
    names = {project.name for project in projects if project.test_command}
    current = tdd.load()
    if current["phase"] == tdd.NONE:
        return dict.fromkeys(sorted(names))
    return {name: paths for name, paths in tdd.task_tests(current).items() if name in names}


def test_failures(selected: dict[str, list[Path] | None]) -> list[str]:
    """Run the selected tests and collect the failures.

    Args:
        selected: `{project name: paths}`; None as paths means the whole suite.

    Returns:
        The output of each project whose tests fail.
    """
    failures = []
    for name, paths in selected.items():
        project = workflow.by_name(name)
        if project is None:
            continue
        code, output = tdd.run_tests(project, paths)
        if code and code not in project.no_tests_exit_codes:
            failures.append(f"--- {name}: tests\n{output}")
    return failures


def main() -> int:
    """Run the checks for the touched projects under the test lock.

    Returns:
        2 when something fails, 0 otherwise.
    """
    payload = json.load(sys.stdin)
    if payload.get("stop_hook_active"):
        return 0
    state = STATE_DIR / f"{payload.get('session_id', 'default')}.edits"
    if not state.exists():
        return 0
    projects = touched_projects(set(state.read_text(encoding="utf-8").split()))
    if not projects:
        return check(state, projects)
    names = ", ".join(project.name for project in projects)
    try:
        with run_locked.held(f"stop hook: {names}", run_locked.STOP_HOOK_TIMEOUT):
            return check(state, projects)
    except run_locked.LockTimeoutError as error:
        print(f"Checks and tests not run: {error}. Run them again later.", file=sys.stderr)
        return 2


def check(state: Path, projects: list[workflow.Project]) -> int:
    """Run the checks and tests of the touched projects and report failures.

    Args:
        state: the session's record of edited files, cleared when everything passes.
        projects: the touched projects.

    Returns:
        2 when something fails, 0 otherwise.
    """
    phase = tdd.phase()
    quality = [
        failure
        for project in projects
        for name, command in project.checks
        if (failure := run(f"{project.name}: {name}", list(command), project.folder))
    ]
    tests = [] if phase == tdd.RED else test_failures(selected_tests(projects))
    if not quality and not tests:
        if phase != tdd.RED:
            state.unlink()
        return 0
    report = []
    if quality:
        report.append(
            "Lint/type/architecture checks fail. Fix them: they are part of writing the code. "
            "An architecture-contract failure means the code is in the wrong place: move it; "
            "never add an ignore to the contract without asking the user."
        )
        report.extend(quality)
    if tests:
        report.append("Tests fail.")
        report.extend(tests)
        report.append(TEST_POLICY[phase])
    print("\n\n".join(report), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
