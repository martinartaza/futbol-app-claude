"""Tests of the test lock: one process at a time runs tests or database commands.

Two sessions, or a session and a subagent, running tests against the same database at
once break each other. `scripts/run_locked.py -- <command>` runs a command holding a
global OS advisory lock (`flock`) in `.claude/state/test.lock`: a second caller waits
and says who holds the lock, gives up after `WORKFLOW_LOCK_TIMEOUT` seconds naming the
holder, and the lock is released by the OS when the holder dies. The Stop hook and
`tdd.py` run their suites under the same lock, and the shell guard sends bare test and
database commands through the wrapper.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from test_workflow_tooling import CONFIG, bash, run, workspace

__all__ = ["workspace"]

TIMEOUT_EXIT_CODE = 75


def stamp(path: Path) -> str:
    """Python one-liner source that appends the current time to `path`."""
    return f"import time; open({str(path)!r}, 'a').write(f'{{time.time()}}\\n')"


def holder(workspace: Path, seconds: float, label: str = "holder-sleep") -> subprocess.Popen[str]:
    """Start a process that holds the lock for `seconds`, and wait until it holds it.

    The held command writes `started` once it runs (so the lock is taken) and `ended`
    right before it exits.
    """
    started = workspace / "started"
    ended = workspace / "ended"
    source = f"{stamp(started)}; time.sleep({seconds}); {stamp(ended)}  # {label}"
    process = subprocess.Popen(
        [sys.executable, "scripts/run_locked.py", "--", sys.executable, "-c", source],
        cwd=workspace,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(workspace)},
    )
    deadline = time.time() + 10
    while not started.exists():
        assert time.time() < deadline, "the holder never got the lock"
        time.sleep(0.05)
    return process


def first_time(path: Path) -> float:
    """First timestamp written to a stamp file."""
    return float(path.read_text(encoding="utf-8").split()[0])


def locked(workspace: Path, *command: str, timeout: str = "30") -> subprocess.CompletedProcess[str]:
    """Run a command through the wrapper with a given wait timeout."""
    return subprocess.run(
        [sys.executable, "scripts/run_locked.py", "--", *command],
        cwd=workspace,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "CLAUDE_PROJECT_DIR": str(workspace),
            "WORKFLOW_LOCK_TIMEOUT": timeout,
        },
        check=False,
    )


def config_with(workspace: Path, **backend: object) -> None:
    """Override keys of the backend project in the workspace config."""
    config = json.loads(json.dumps(CONFIG))
    config["projects"]["backend"].update(backend)
    config["projects"]["app"]["test_command"] = ["npm", "test"]
    (workspace / "workflow.json").write_text(json.dumps(config), encoding="utf-8")


def test_runs_the_command_and_returns_its_exit_code(workspace: Path) -> None:
    """The wrapper runs the command and exits with its code."""
    assert locked(workspace, sys.executable, "-c", "raise SystemExit(3)").returncode == 3
    assert locked(workspace, sys.executable, "-c", "pass").returncode == 0


def test_second_run_waits_until_the_first_ends(workspace: Path) -> None:
    """A second run starts only after the holder finished."""
    first = holder(workspace, 1.5)
    second = workspace / "second"
    assert locked(workspace, sys.executable, "-c", stamp(second)).returncode == 0
    first.wait(timeout=10)
    assert first_time(second) >= first_time(workspace / "ended")


def test_waiting_run_says_who_holds_the_lock(workspace: Path) -> None:
    """While waiting, the second run names the holder's command."""
    first = holder(workspace, 1.0, label="holder-sleep")
    result = locked(workspace, sys.executable, "-c", "pass")
    first.wait(timeout=10)
    assert result.returncode == 0
    assert "holder-sleep" in result.stderr


def test_gives_up_after_the_timeout_naming_the_holder(workspace: Path) -> None:
    """Past `WORKFLOW_LOCK_TIMEOUT` the second run fails without running its command."""
    first = holder(workspace, 3.0, label="holder-sleep")
    second = workspace / "second"
    result = locked(workspace, sys.executable, "-c", stamp(second), timeout="0.5")
    first.wait(timeout=10)
    assert result.returncode == TIMEOUT_EXIT_CODE
    assert "holder-sleep" in result.stderr
    assert not second.exists()


def test_lock_is_released_when_the_holder_is_killed(workspace: Path) -> None:
    """A killed holder leaves no stale lock: the next run goes ahead at once."""
    first = holder(workspace, 30.0)
    os.kill(first.pid, signal.SIGKILL)
    first.wait(timeout=10)
    started = time.time()
    assert locked(workspace, sys.executable, "-c", "pass", timeout="5").returncode == 0
    assert time.time() - started < 3


def test_nested_run_inside_the_lock_does_not_wait(workspace: Path) -> None:
    """A command already holding the lock can call the wrapper again without deadlock."""
    inner = [sys.executable, "scripts/run_locked.py", "--", sys.executable, "-c", "pass"]
    assert locked(workspace, *inner, timeout="2").returncode == 0


def test_stop_hook_runs_the_suite_under_the_lock(workspace: Path) -> None:
    """The Stop hook waits for the holder before running a touched project's tests."""
    suite = workspace / "suite"
    config_with(workspace, test_command=[sys.executable, "-c", stamp(suite)])
    state = workspace / ".claude" / "state"
    state.mkdir(parents=True, exist_ok=True)
    (state / "s.edits").write_text("backend/app/calc.py\n", encoding="utf-8")
    first = holder(workspace, 1.5)
    result = run(
        workspace,
        sys.executable,
        ".claude/hooks/stop_checks.py",
        stdin=json.dumps({"session_id": "s"}),
    )
    first.wait(timeout=10)
    assert result.returncode == 0, result.stderr
    assert first_time(suite) >= first_time(workspace / "ended")


def test_tdd_runs_its_suites_under_the_lock(workspace: Path) -> None:
    """`tdd.py green` waits for the holder before running the new tests."""
    suite = workspace / "suite"
    config_with(
        workspace,
        test_command=[sys.executable, "-c", f"{stamp(suite)}; raise SystemExit(1)"],
    )
    run(workspace, sys.executable, "scripts/tdd.py", "start", "0001-add")
    (workspace / "backend" / "tests" / "test_calc.py").write_text(
        "def test_ac1_fails():\n    assert False\n", encoding="utf-8"
    )
    first = holder(workspace, 1.5)
    result = run(workspace, sys.executable, "scripts/tdd.py", "green")
    first.wait(timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
    assert first_time(suite) >= first_time(workspace / "ended")


def test_guard_sends_bare_test_and_database_commands_through_the_wrapper(
    workspace: Path,
) -> None:
    """pytest, a project's test command and alembic are denied unless wrapped."""
    config_with(workspace)
    for command in (
        "uvx --python 3.13 pytest -q tests",
        "cd backend && .venv/bin/pytest -q",
        "uv run pytest tests/test_calc.py",
        "npm test",
        "docker compose exec backend alembic upgrade head",
    ):
        found = bash(workspace, command)
        assert found.get("permissionDecision") == "deny", command
        assert "run_locked.py" in found["permissionDecisionReason"], command


def test_guard_lets_wrapped_and_read_only_commands_through(workspace: Path) -> None:
    """Wrapped commands and commands that only mention pytest are not blocked."""
    config_with(workspace)
    for command in (
        "python3 scripts/run_locked.py -- uvx pytest -q tests",
        "python3 scripts/run_locked.py -- docker compose exec backend alembic upgrade head",
        "grep -rn pytest workflow.json",
        "cat tests/test_calc.py",
    ):
        assert bash(workspace, command) == {}, command


def with_timeout(
    workspace: Path, *command: str, stdin: str | None = None, timeout: str = "0.5"
) -> subprocess.CompletedProcess[str]:
    """Run a workspace script with a short lock timeout."""
    return subprocess.run(
        command,
        cwd=workspace,
        capture_output=True,
        text=True,
        input=stdin,
        env={
            **os.environ,
            "CLAUDE_PROJECT_DIR": str(workspace),
            "WORKFLOW_LOCK_TIMEOUT": timeout,
        },
        check=False,
    )


def test_tdd_green_stops_when_the_lock_times_out(workspace: Path) -> None:
    """A lock timeout is not a failing test: `green` stops, names the holder, stays in red."""
    suite = workspace / "suite"
    config_with(
        workspace,
        test_command=[sys.executable, "-c", f"{stamp(suite)}; raise SystemExit(1)"],
    )
    run(workspace, sys.executable, "scripts/tdd.py", "start", "0001-add")
    (workspace / "backend" / "tests" / "test_calc.py").write_text(
        "def test_ac1_fails():\n    assert False\n", encoding="utf-8"
    )
    first = holder(workspace, 3.0, label="holder-sleep")
    result = with_timeout(workspace, sys.executable, "scripts/tdd.py", "green")
    first.wait(timeout=10)
    assert result.returncode != 0
    assert "holder-sleep" in result.stdout + result.stderr
    assert not suite.exists()
    status = run(workspace, sys.executable, "scripts/tdd.py", "status")
    assert json.loads(status.stdout)["phase"] == "red"


def test_stop_hook_reports_who_holds_the_lock_on_timeout(workspace: Path) -> None:
    """The Stop hook gives up past the timeout, names the holder and runs nothing."""
    suite = workspace / "suite"
    config_with(workspace, test_command=[sys.executable, "-c", stamp(suite)])
    state = workspace / ".claude" / "state"
    state.mkdir(parents=True, exist_ok=True)
    (state / "s.edits").write_text("backend/app/calc.py\n", encoding="utf-8")
    first = holder(workspace, 3.0, label="holder-sleep")
    result = with_timeout(
        workspace,
        sys.executable,
        ".claude/hooks/stop_checks.py",
        stdin=json.dumps({"session_id": "s"}),
    )
    first.wait(timeout=10)
    assert result.returncode == 2
    assert "holder-sleep" in result.stderr
    assert not suite.exists()


def test_guard_lets_migration_generation_and_dependency_changes_through(
    workspace: Path,
) -> None:
    """`alembic revision` and package commands that only name pytest are not locked."""
    config_with(workspace)
    for command in (
        "docker compose exec backend alembic revision --autogenerate -m x",
        "uv add --dev pytest",
        "uv remove pytest",
        "uv pip install pytest",
        "uv sync",
        "python3 -m pip install pytest",
    ):
        assert bash(workspace, command) == {}, command


def test_guard_judges_every_part_of_a_command_with_the_wrapper(workspace: Path) -> None:
    """Mentioning the wrapper does not free the other parts of a command."""
    config_with(workspace)
    for command in (
        "cat scripts/run_locked.py && uv run pytest",
        "python3 scripts/run_locked.py -- true; pytest -q",
    ):
        assert bash(workspace, command).get("permissionDecision") == "deny", command
