"""Tests of the workflow tooling: classification, TDD phases, guards and explication scope.

Every test builds a throwaway workspace from this repository's `scripts/`, hooks and
`workflow.json`-like config, and runs the real scripts as subprocesses with
`CLAUDE_PROJECT_DIR` pointing at it, the way Claude Code runs them.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
CONFIG = {
    "projects": {
        "backend": {
            "path": "backend",
            "source": ["app/**/*.py"],
            "tests": ["tests/**/*.py"],
            "runnable_tests": ["test_*.py"],
            "test_command": [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
            "no_tests_exit_codes": [5],
            "generated": [
                {
                    "glob": "alembic/versions/*.py",
                    "generator": "alembic revision",
                    "how": "Use autogenerate.",
                }
            ],
        },
        "app": {
            "path": "app",
            "source": ["src/**/*.ts", "src/**/*.tsx"],
            "tests": ["**/*.test.ts", "**/*.test.tsx"],
            "runnable_tests": ["*.test.ts"],
            "reuse_guard": {"globs": ["src/components/**/*.tsx"], "hint": "Reuse."},
        },
    }
}


def run(workspace: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run a command inside the workspace as Claude Code would."""
    return subprocess.run(
        args,
        cwd=workspace,
        capture_output=True,
        text=True,
        input=stdin,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(workspace)},
        check=False,
    )


def hook(workspace: Path, name: str, payload: dict[str, object]) -> dict[str, str]:
    """Run a PreToolUse hook and return its decision (empty when it lets the call through)."""
    result = run(workspace, sys.executable, f".claude/hooks/{name}", stdin=json.dumps(payload))
    if not result.stdout.strip():
        return {}
    return json.loads(result.stdout)["hookSpecificOutput"]


def edit(workspace: Path, path: str, tool: str = "Edit") -> dict[str, str]:
    """Decision of the edit guard for a file of the workspace."""
    return hook(
        workspace,
        "guard_edit.py",
        {"tool_name": tool, "session_id": "t", "tool_input": {"file_path": str(workspace / path)}},
    )


def bash(workspace: Path, command: str) -> dict[str, str]:
    """Decision of the shell guard for a command."""
    return hook(workspace, "guard_bash.py", {"tool_input": {"command": command}})


def git(workspace: Path, *args: str) -> None:
    """Run git quietly with a fixed identity."""
    run(workspace, "git", "-c", "user.email=t@t", "-c", "user.name=t", *args)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """A committed monorepo workspace with a backend and an app project."""
    shutil.copytree(REPO / "scripts", tmp_path / "scripts")
    shutil.copytree(REPO / ".claude" / "hooks", tmp_path / ".claude" / "hooks")
    (tmp_path / "workflow.json").write_text(json.dumps(CONFIG), encoding="utf-8")
    (tmp_path / "backend" / "app").mkdir(parents=True)
    (tmp_path / "backend" / "tests").mkdir()
    (tmp_path / "backend" / "app" / "__init__.py").write_text("")
    (tmp_path / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return 0\n")
    (tmp_path / "backend" / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\npythonpath = ["."]\n'
    )
    (tmp_path / "app" / "src" / "components").mkdir(parents=True)
    (tmp_path / "app" / "src" / "components" / "match-card.tsx").write_text("")
    git(tmp_path, "init", "-q")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "init")
    return tmp_path


def write_failing_test(workspace: Path) -> None:
    """Write a backend test that fails until `add` is implemented."""
    (workspace / "backend" / "tests" / "test_calc.py").write_text(
        "from app.calc import add\n\n\ndef test_ac1_adds():\n    assert add(1, 2) == 3\n"
    )


def test_without_task_source_and_tests_ask(workspace: Path) -> None:
    """Outside a task every source or test change needs the user."""
    assert edit(workspace, "backend/app/calc.py")["permissionDecision"] == "ask"
    assert edit(workspace, "backend/tests/test_calc.py")["permissionDecision"] == "ask"
    assert edit(workspace, "README.md") == {}


def test_red_locks_source_and_frees_tests(workspace: Path) -> None:
    """In red, source is denied from Write/Edit and from the shell; tests are free."""
    run(workspace, sys.executable, "scripts/tdd.py", "start", "0001-add")
    assert edit(workspace, "backend/app/calc.py")["permissionDecision"] == "deny"
    assert edit(workspace, "app/src/screens/home.tsx", "Write")["permissionDecision"] == "deny"
    assert bash(workspace, "sed -i '' s/0/1/ backend/app/calc.py")["permissionDecision"] == "deny"
    assert edit(workspace, "backend/tests/test_calc.py", "Write") == {}


def test_green_needs_failing_tests_then_asks_for_test_changes(workspace: Path) -> None:
    """`green` refuses without a failing test; in green, tests ask and source is free."""
    run(workspace, sys.executable, "scripts/tdd.py", "start", "0001-add")
    assert run(workspace, sys.executable, "scripts/tdd.py", "green").returncode == 1
    write_failing_test(workspace)
    assert run(workspace, sys.executable, "scripts/tdd.py", "green").returncode == 0
    assert edit(workspace, "backend/app/calc.py") == {}
    assert edit(workspace, "backend/tests/test_calc.py")["permissionDecision"] == "ask"


def test_green_refuses_tests_that_already_pass(workspace: Path) -> None:
    """A new test that passes before the implementation is not a red test."""
    run(workspace, sys.executable, "scripts/tdd.py", "start", "0001-add")
    (workspace / "backend" / "tests" / "test_true.py").write_text(
        "def test_x():\n    assert True\n"
    )
    result = run(workspace, sys.executable, "scripts/tdd.py", "green")
    assert result.returncode == 1
    assert "already pass" in result.stdout


def test_done_closes_only_when_suites_pass(workspace: Path) -> None:
    """`done` keeps the task open while tests fail and closes it when they pass."""
    run(workspace, sys.executable, "scripts/tdd.py", "start", "0001-add")
    write_failing_test(workspace)
    run(workspace, sys.executable, "scripts/tdd.py", "green")
    assert run(workspace, sys.executable, "scripts/tdd.py", "done").returncode == 1
    (workspace / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    assert run(workspace, sys.executable, "scripts/tdd.py", "done").returncode == 0
    assert not (workspace / ".claude" / "state" / "tdd.json").exists()


def test_approval_commands_and_git_writes_ask(workspace: Path) -> None:
    """`tdd.py green`, `tdd.py abort`, `git commit` and `git push` always ask."""
    for command in ("python3 scripts/tdd.py green", "python3 scripts/tdd.py abort"):
        assert bash(workspace, command)["permissionDecision"] == "ask"
    for command in ("git commit -m x", "git -C backend push"):
        assert bash(workspace, command)["permissionDecision"] == "ask"


def test_state_and_config_are_protected(workspace: Path) -> None:
    """The TDD state is never written; workflow.json and settings ask."""
    assert edit(workspace, ".claude/state/tdd.json")["permissionDecision"] == "deny"
    assert bash(workspace, "rm -rf .claude/state")["permissionDecision"] == "deny"
    assert edit(workspace, "workflow.json")["permissionDecision"] == "ask"
    assert edit(workspace, ".claude/settings.json")["permissionDecision"] == "ask"


def test_generated_files_are_only_generated(workspace: Path) -> None:
    """A generated file is denied by hand and from the shell; the generator passes."""
    new = edit(workspace, "backend/alembic/versions/x.py", "Write")
    assert new["permissionDecision"] == "deny"
    assert "autogenerate" in new["permissionDecisionReason"]
    shell = bash(workspace, "cat > backend/alembic/versions/x.py")
    assert shell["permissionDecision"] == "deny"
    assert bash(workspace, "docker compose exec backend alembic revision --autogenerate") == {}
    assert bash(workspace, "rm backend/alembic/versions/x.py")["permissionDecision"] == "ask"


def test_reuse_guard_lists_similar_files_once(workspace: Path) -> None:
    """The first creation of a reusable file is denied with the catalog; the second passes on."""
    first = edit(workspace, "app/src/components/match-row.tsx", "Write")
    assert first["permissionDecision"] == "deny"
    assert "src/components/match-card.tsx" in first["permissionDecisionReason"]
    second = edit(workspace, "app/src/components/match-row.tsx", "Write")
    assert second["permissionDecision"] == "ask"


def test_explication_scope_reads_tags_per_project(workspace: Path) -> None:
    """The scope of `v0.1.0` lists the files changed since the previous tag, per project."""
    git(workspace, "tag", "v0.0.0")
    (workspace / "requirements").mkdir()
    (workspace / "requirements" / "0001-add.md").write_text("---\nprojects: [backend]\n---\n")
    write_failing_test(workspace)
    (workspace / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    git(workspace, "add", "-A")
    git(workspace, "commit", "-qm", "0001")
    git(workspace, "tag", "v0.1.0")
    result = run(workspace, sys.executable, "scripts/explication_scope.py", "v0.1.0")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "backend\tM\tapp/calc.py",
        "backend\tA\ttests/test_calc.py",
    ]


def test_explication_scope_refuses_a_dirty_tree(workspace: Path) -> None:
    """Nothing is computed while a project has uncommitted changes."""
    git(workspace, "tag", "v0.1.0")
    (workspace / "requirements").mkdir()
    (workspace / "requirements" / "0001-add.md").write_text("---\nprojects: [backend]\n---\n")
    (workspace / "backend" / "app" / "calc.py").write_text("x = 1\n")
    result = run(workspace, sys.executable, "scripts/explication_scope.py", "v0.1.0")
    assert result.returncode == 1
    assert "sin commitear" in result.stderr
