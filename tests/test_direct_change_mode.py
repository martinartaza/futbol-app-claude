"""Tests of the direct-change mode of `tdd.py` (one approval for a whole direct change).

A direct change (scaffolding, a change the user asked for explicitly, lab mode) opens
with `tdd.py start <task> --direct`, which the shell guard asks the user once. While it
is open, source and tests are edited without asking, from Write/Edit and from the
shell; the protections that do not depend on the phase (generated files, the TDD state,
`workflow.json`, settings) stay. `tdd.py done` closes it after running the tests it
changed; the Stop hook runs those tests too and reports failures to the user.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from test_epic_delivery import phase, stop_hook, tdd
from test_workflow_tooling import bash, edit, run, workspace

__all__ = ["workspace"]

FAILING_TEST = "def test_new_behaviour():\n    assert False\n"
PASSING_TEST = "def test_new_behaviour():\n    assert True\n"


def write_test(workspace: Path, body: str) -> None:
    """Write the direct change's own backend test."""
    (workspace / "backend" / "tests" / "test_direct.py").write_text(body)


def test_starting_a_direct_change_asks_the_user_once(workspace: Path) -> None:
    """`start --direct` is the one approval; a normal `start` still does not ask."""
    direct = bash(workspace, "python3 scripts/tdd.py start scaffolding --direct")
    assert direct["permissionDecision"] == "ask"
    assert "direct" in direct["permissionDecisionReason"]
    assert bash(workspace, "python3 scripts/tdd.py start 0002-add") == {}


def test_direct_change_records_its_own_phase(workspace: Path) -> None:
    """The task is in phase `direct`, and a second task cannot start over it."""
    assert tdd(workspace, "start", "scaffolding", "--direct") == 0
    assert phase(workspace) == "direct"
    assert tdd(workspace, "start", "other") == 1


def test_direct_change_frees_source_and_tests(workspace: Path) -> None:
    """In a direct change, source and tests are edited without asking, also by shell."""
    tdd(workspace, "start", "scaffolding", "--direct")
    assert edit(workspace, "backend/app/calc.py") == {}
    assert edit(workspace, "app/src/screens/home.tsx", "Write") == {}
    assert edit(workspace, "backend/tests/test_calc.py") == {}
    assert bash(workspace, "sed -i '' s/0/1/ backend/app/calc.py") == {}


def test_direct_change_keeps_the_other_protections(workspace: Path) -> None:
    """Generated files, the TDD state, workflow.json and settings keep their rules."""
    tdd(workspace, "start", "scaffolding", "--direct")
    assert edit(workspace, "backend/alembic/versions/x.py", "Write")["permissionDecision"] == "deny"
    assert edit(workspace, ".claude/state/tdd.json")["permissionDecision"] == "deny"
    assert edit(workspace, "workflow.json")["permissionDecision"] == "ask"
    assert edit(workspace, ".claude/settings.json")["permissionDecision"] == "ask"


def test_green_does_not_apply_to_a_direct_change(workspace: Path) -> None:
    """A direct change has no red tests to approve: `green` refuses and the phase stays."""
    tdd(workspace, "start", "scaffolding", "--direct")
    write_test(workspace, FAILING_TEST)
    assert tdd(workspace, "green") == 1
    assert phase(workspace) == "direct"


def test_done_closes_a_direct_change_without_tests(workspace: Path) -> None:
    """A direct change with no tests of its own closes with `done`."""
    tdd(workspace, "start", "scaffolding", "--direct")
    (workspace / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    assert tdd(workspace, "done") == 0
    assert phase(workspace) == "none"


def test_done_runs_the_tests_the_direct_change_touched(workspace: Path) -> None:
    """`done` keeps the direct change open while a test it changed fails."""
    tdd(workspace, "start", "scaffolding", "--direct")
    write_test(workspace, FAILING_TEST)
    result = run(workspace, sys.executable, "scripts/tdd.py", "done")
    assert result.returncode == 1
    assert phase(workspace) == "direct"
    write_test(workspace, PASSING_TEST)
    assert tdd(workspace, "done") == 0


def test_stop_hook_reports_failing_tests_of_a_direct_change(workspace: Path) -> None:
    """The Stop hook runs the direct change's tests and blocks while they fail."""
    tdd(workspace, "start", "scaffolding", "--direct")
    write_test(workspace, FAILING_TEST)
    assert stop_hook(workspace, "backend/tests/test_direct.py") == 2
    write_test(workspace, PASSING_TEST)
    assert stop_hook(workspace, "backend/tests/test_direct.py") == 0


def test_status_names_the_direct_kind(workspace: Path) -> None:
    """`status` shows the task as a direct change."""
    tdd(workspace, "start", "scaffolding", "--direct")
    status = json.loads(run(workspace, sys.executable, "scripts/tdd.py", "status").stdout)
    assert status["task"] == "scaffolding"
    assert status["phase"] == "direct"
