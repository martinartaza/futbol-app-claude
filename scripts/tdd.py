#!/usr/bin/env python3
"""Test-driven development at the user's pace (CLAUDE.md rule 2).

A task goes through two phases, recorded in `.claude/state/tdd.json`:

- **red**: only tests are written. They must fail, because the behaviour does not exist
  yet. Source code cannot be edited (the edit and shell guards deny it).
- **green**: the user approved the failing tests; now the implementation is written.
  Source code can be edited freely to make the tests pass; changing a test asks the user.

A **direct change** (scaffolding, a change the user asked for explicitly, lab mode) has
one phase of its own, **direct**: starting it is the user's one approval (the Bash
guard asks), and while it is open source and tests are edited without asking.

What is a test and what is source comes from `workflow.json` (`scripts/workflow.py`).

Commands (from the workspace root):

    python3 scripts/tdd.py start <task>   begin a task in red (e.g. 0003-match-list)
    python3 scripts/tdd.py start <task> --epic-close
                                          begin an epic's closing ticket in green (its
                                          approved findings are the red)
    python3 scripts/tdd.py start <task> --direct
                                          begin a direct change (the Bash guard asks
                                          the user: the one approval of the change)
    python3 scripts/tdd.py status         show the current task and phase
    python3 scripts/tdd.py green          check the new tests fail, then move to green
                                          (the Bash guard asks the user: this is the
                                          approval to start developing)
    python3 scripts/tdd.py done           run the task's own tests (every suite for a
                                          closing ticket); when they pass, close it
                                          (also a direct change)
    python3 scripts/tdd.py suite          run every suite of every project
    python3 scripts/tdd.py abort          drop the task (the Bash guard asks the user)

A ticket runs only its own tests; the full suite runs in each epic's closing ticket
(ADR 0004 section 6).

The hooks import this module to read the phase.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_locked  # noqa: E402
import workflow  # noqa: E402
from workflow import ROOT, Project  # noqa: E402

STATE = ROOT / ".claude" / "state" / "tdd.json"
NONE, RED, GREEN, DIRECT = "none", "red", "green", "direct"
EPIC_CLOSE = "epic-close"
EPIC_CLOSE_FLAG = "--epic-close"
DIRECT_FLAG = "--direct"
FLAGS = {EPIC_CLOSE_FLAG, DIRECT_FLAG}
# "My Task 3" -> "my-task-3"
UNSAFE_TASK_CHARS = re.compile(r"[^a-z0-9-]+")

relative = workflow.relative
is_test = workflow.is_test
is_source = workflow.is_source


def load() -> dict[str, Any]:
    """Current task state.

    Returns:
        The stored state, or `{"phase": "none"}` when no task is active.
    """
    if not STATE.exists():
        return {"phase": NONE}
    return json.loads(STATE.read_text(encoding="utf-8"))


def phase() -> str:
    """Phase of the current task.

    Returns:
        "none", "red" or "green".
    """
    return load().get("phase", NONE)


def save(state: dict[str, Any]) -> None:
    """Store the task state.

    Args:
        state: task, phase and timestamps.
    """
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def git_toplevel(folder: Path) -> Path | None:
    """Root of the git repository that contains a folder.

    Args:
        folder: any folder.

    Returns:
        The repository root, or None when the folder is not in a repository.
    """
    if not folder.is_dir():
        return None
    result = subprocess.run(
        ["git", "-C", str(folder), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    return Path(result.stdout.strip()) if result.returncode == 0 else None


def changed_files(project: Project) -> list[Path]:
    """Files changed or added in a project, relative to the HEAD of its repository.

    Args:
        project: a workspace project.

    Returns:
        Absolute paths of modified and untracked files that still exist and belong to
        this project (not to a nested one).
    """
    top = git_toplevel(project.folder)
    if top is None:
        return []
    result = subprocess.run(
        [
            "git",
            "-C",
            str(project.folder),
            "status",
            "--porcelain",
            "--untracked-files=all",
            "--",
            ".",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    paths = [top / line[3:].split(" -> ")[-1].strip('"') for line in result.stdout.splitlines()]
    return [
        path
        for path in paths
        if path.is_file() and (found := workflow.owner(path)) and found.name == project.name
    ]


def digest(path: Path) -> str:
    """Content hash of a file.

    Args:
        path: existing file.

    Returns:
        SHA-1 of its bytes.
    """
    return hashlib.sha1(path.read_bytes(), usedforsecurity=False).hexdigest()


def snapshot() -> dict[str, str]:
    """Hash of every uncommitted file in every project, taken when a task starts.

    Returns:
        `{relative path: hash}`.
    """
    return {
        relative(path): digest(path)
        for project in workflow.projects()
        for path in changed_files(project)
    }


def changed_tests(baseline: dict[str, str]) -> dict[str, list[Path]]:
    """Runnable test files created or modified since the task started.

    Args:
        baseline: snapshot taken by `start`.

    Returns:
        `{project name: [paths]}`, non-empty only.
    """
    tests = {
        project.name: [
            path
            for path in changed_files(project)
            if workflow.is_runnable_test(path) and baseline.get(relative(path)) != digest(path)
        ]
        for project in workflow.projects()
    }
    return {name: paths for name, paths in tests.items() if paths}


def run_tests(project: Project, paths: list[Path] | None = None) -> tuple[int, str]:
    """Run a project's test suite, or only some of its files.

    Args:
        project: the project.
        paths: test files to run; the whole suite when None.

    Returns:
        Exit code and the last lines of output; exit code 127 when the runner is missing.

    Raises:
        LockTimeoutError: the test lock stayed busy; nothing ran.
    """
    targets = [str(path.relative_to(project.folder)) for path in paths or []]
    try:
        with run_locked.held(f"tdd.py: {project.name} tests"):
            result = subprocess.run(
                [*project.test_command, *targets],
                cwd=project.folder,
                capture_output=True,
                text=True,
                check=False,
            )
    except FileNotFoundError:
        return 127, f"test runner not found: {project.test_command[0]}"
    output = (result.stdout + result.stderr).strip().splitlines()
    return result.returncode, "\n".join(output[-25:])


def outcome(project: Project, code: int, output: str) -> str:
    """Meaning of a test run for the red phase.

    Args:
        project: the project that ran.
        code: exit code of the runner.
        output: runner output.

    Returns:
        "passing", "failing", or "none" when the runner found no tests to run.
    """
    if code == 0:
        return "passing"
    if code in project.no_tests_exit_codes:
        return "none"
    if project.no_tests_output and project.no_tests_output in output:
        return "none"
    return "failing"


def now() -> str:
    """Current local time for the state file.

    Returns:
        ISO timestamp with minutes.
    """
    return datetime.now().isoformat(timespec="minutes")


def start(task: str, epic_close: bool = False, direct: bool = False) -> int:
    """Begin a task in red, an epic's closing ticket in green, or a direct change.

    Args:
        task: short name, ideally the requirement or bug slug.
        epic_close: the task is an epic's closing ticket (skill `close-epic`): the
            findings the user approved are its red, so it starts in green and its `done`
            runs every suite.
        direct: the task is a direct change, without red tests to approve: source and
            tests are free until `done`.

    Returns:
        Process exit code.
    """
    current = load()
    if current["phase"] != NONE:
        print(f"Task '{current['task']}' is already in {current['phase']}. Finish or abort it.")
        return 1
    slug = UNSAFE_TASK_CHARS.sub("-", task.lower()).strip("-")
    if epic_close and direct:
        print(f"Choose one of {EPIC_CLOSE_FLAG} and {DIRECT_FLAG}.")
        return 2
    if direct:
        save({"task": slug, "phase": DIRECT, "started": now(), "baseline": snapshot()})
        print(
            f"Direct change '{slug}' started: source and tests are free; `done` runs the "
            "tests it changed and closes it."
        )
        return 0
    if epic_close:
        save(
            {
                "task": slug,
                "kind": EPIC_CLOSE,
                "phase": GREEN,
                "started": now(),
                "approved": now(),
                "baseline": snapshot(),
            }
        )
        print(
            f"Closing ticket '{slug}' started in GREEN: fix the approved findings; `done` "
            "runs every suite."
        )
        return 0
    save({"task": slug, "phase": RED, "started": now(), "baseline": snapshot()})
    print(
        f"Task '{slug}' started in RED. Write the tests only; source code is locked until "
        "the user approves the failing tests (`tdd.py green`)."
    )
    return 0


def is_epic_close(current: dict[str, Any]) -> bool:
    """Whether a task is an epic's closing ticket.

    Args:
        current: the task state.

    Returns:
        True for a task started with `--epic-close`.
    """
    return current.get("kind") == EPIC_CLOSE


def task_tests(current: dict[str, Any]) -> dict[str, list[Path] | None]:
    """The tests a task runs: its own test files, or every suite for a closing ticket.

    Args:
        current: the task state.

    Returns:
        `{project name: paths}`; None as paths means the whole suite.
    """
    if is_epic_close(current):
        return {project.name: None for project in suites()}
    return dict(changed_tests(current.get("baseline", {})))


def suites() -> list[Project]:
    """Projects whose whole suite can run.

    Returns:
        Every project with a test command and its tools installed.
    """
    return [project for project in workflow.projects() if project.test_command and project.ready]


def run_suites(selected: dict[str, list[Path] | None]) -> list[str]:
    """Run tests per project and print their output.

    Args:
        selected: `{project name: paths}`; None as paths means the whole suite.

    Returns:
        The names of the projects whose tests fail.

    Raises:
        LockTimeoutError: the test lock stayed busy.
    """
    failed = []
    for name, paths in selected.items():
        project = workflow.by_name(name)
        if project is None:
            continue
        code, output = run_tests(project, paths)
        print(f"--- {name}\n{output}\n")
        if code and code not in project.no_tests_exit_codes:
            failed.append(name)
    return failed


def suite() -> int:
    """Run every suite of every project, as an epic's closing ticket does.

    Returns:
        Process exit code: 1 when any suite fails.
    """
    try:
        failed = run_suites({project.name: None for project in suites()})
    except run_locked.LockTimeoutError as error:
        return locked_out(error)
    if failed:
        print(f"Tests fail in {', '.join(failed)}.")
        return 1
    print("Every suite passes.")
    return 0


def locked_out(error: run_locked.LockTimeoutError) -> int:
    """Report that the suites did not run because the test lock stayed busy.

    Args:
        error: the timeout, naming the lock holder.

    Returns:
        The lock timeout exit code; the task phase is unchanged.
    """
    print(f"Tests not run, the phase is unchanged: {error}. Try again when it is free.")
    return run_locked.TIMEOUT_EXIT_CODE


def green() -> int:
    """Check the new tests fail and move the task to green.

    Returns:
        Process exit code.
    """
    try:
        return move_to_green()
    except run_locked.LockTimeoutError as error:
        return locked_out(error)


def move_to_green() -> int:
    """Run the changed tests, and move the task to green when they all fail.

    Returns:
        Process exit code.

    Raises:
        LockTimeoutError: the test lock stayed busy; the phase is unchanged.
    """
    current = load()
    if current["phase"] != RED:
        print(f"Only a task in red can go green; current phase: {current['phase']}.")
        return 1
    changed = changed_tests(current.get("baseline", {}))
    if not changed:
        print("No test file created or changed since the task started: write the failing tests.")
        return 1
    passing, failing = [], []
    for name, paths in changed.items():
        project = workflow.by_name(name)
        if project is None:
            continue
        code, output = run_tests(project, paths)
        print(f"--- {name}: {', '.join(relative(path) for path in paths)}\n{output}\n")
        result = outcome(project, code, output)
        if result == "passing":
            passing.append(name)
        elif result == "failing":
            failing.append(name)
    if not failing and not passing:
        print("The runners found no tests in the changed files: write the failing tests.")
        return 1
    if passing:
        print(
            f"The new tests of {', '.join(passing)} already pass. In TDD they must fail "
            "before the implementation exists: check that they test the new behaviour."
        )
        return 1
    save({**current, "phase": GREEN, "approved": now()})
    print(f"Task '{current['task']}' is GREEN: implement until the tests pass.")
    return 0


def done() -> int:
    """Run the suites of the projects touched by the task and close it when they pass.

    Returns:
        Process exit code.
    """
    try:
        return close()
    except run_locked.LockTimeoutError as error:
        return locked_out(error)


def close() -> int:
    """Run the task's tests and close the task when they pass.

    A ticket or a direct change runs only its own test files; an epic's closing ticket
    runs every suite.

    Returns:
        Process exit code.

    Raises:
        LockTimeoutError: the test lock stayed busy; the task stays open.
    """
    current = load()
    if current["phase"] not in {GREEN, DIRECT}:
        print(
            f"Only a task in green or a direct change can be closed; current phase: "
            f"{current['phase']}."
        )
        return 1
    failed = run_suites(task_tests(current))
    if failed:
        print(f"Tests fail in {', '.join(failed)}: keep implementing (tests stay as approved).")
        return 1
    STATE.unlink()
    print(f"Task '{current['task']}' done: all tests pass.")
    return 0


def abort() -> int:
    """Drop the current task.

    Returns:
        Process exit code.
    """
    current = load()
    if current["phase"] == NONE:
        print("No active task.")
        return 0
    STATE.unlink()
    print(f"Task '{current['task']}' aborted.")
    return 0


def main(argv: list[str]) -> int:
    """Dispatch the command.

    Args:
        argv: command-line arguments.

    Returns:
        Process exit code.
    """
    if not argv or argv[0] not in {"start", "status", "green", "done", "abort", "suite"}:
        print(__doc__)
        return 2
    command = argv[0]
    if command == "start":
        names = [arg for arg in argv[1:] if arg not in FLAGS]
        if len(names) != 1:
            print(f"Usage: python3 scripts/tdd.py start <task> [{EPIC_CLOSE_FLAG} | {DIRECT_FLAG}]")
            return 2
        return start(names[0], EPIC_CLOSE_FLAG in argv[1:], DIRECT_FLAG in argv[1:])
    if command == "status":
        print(json.dumps(load(), indent=2))
        return 0
    return {"green": green, "done": done, "abort": abort, "suite": suite}[command]()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
