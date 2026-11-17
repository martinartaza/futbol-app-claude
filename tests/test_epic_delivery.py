"""Tests of delivery by epic (ADR 0004 section 6) in the workflow tooling.

- A ticket runs only its own tests: `tdd.py done` and the Stop hook ignore older tests.
- `tdd.py suite` runs every suite; the closing ticket of an epic
  (`tdd.py start <task> --epic-close`) starts in green and its `done` and Stop hook run
  every suite.
- One explication per epic, `explications/EXX-<slug>.md`, checked against the scope
  from the previous epic's last tag to the epic's closing tag (the `tag` of its
  `kind: epic-close` requirement); ticket notes in `explications/tickets/` are not
  checked.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

from test_workflow_tooling import REPO, git, run, workspace

__all__ = ["workspace"]

OLD_FAILING_TEST = "def test_old_behaviour():\n    assert False\n"
# "## Backend (si aplica)" -> "Backend (si aplica)"
HEADING = re.compile(r"^## (.+?)\s*$", re.MULTILINE)
# "el alcance debe decir «(2 archivos: 1 de backend y 1 de tests)»" -> "(2 archivos: ...)"
EXPECTED_SCOPE = re.compile(r"el alcance debe decir «(.+?)»")


def tdd(workspace: Path, *args: str) -> int:
    """Run `tdd.py` in the workspace and return its exit code."""
    return run(workspace, sys.executable, "scripts/tdd.py", *args).returncode


def phase(workspace: Path) -> str:
    """The current TDD phase of the workspace."""
    status = run(workspace, sys.executable, "scripts/tdd.py", "status")
    return json.loads(status.stdout)["phase"]


def with_old_failing_test(workspace: Path) -> None:
    """Commit an older test that fails, as a regression left by an earlier ticket."""
    (workspace / "backend" / "tests" / "test_old.py").write_text(OLD_FAILING_TEST)
    git(workspace, "add", "-A")
    git(workspace, "commit", "-qm", "old")


def ticket_in_green(workspace: Path) -> None:
    """Start a ticket, write its failing test and approve it."""
    tdd(workspace, "start", "0002-add")
    (workspace / "backend" / "tests" / "test_add.py").write_text(
        "from app.calc import add\n\n\ndef test_ac1_adds():\n    assert add(1, 2) == 3\n"
    )
    assert tdd(workspace, "green") == 0


def implement(workspace: Path) -> None:
    """Make `add` work."""
    (workspace / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")


def fix_old_test(workspace: Path) -> None:
    """Make the older failing test pass, as a regression fix does."""
    (workspace / "backend" / "tests" / "test_old.py").write_text(
        "def test_old_behaviour():\n    assert True\n"
    )


def stop_hook(workspace: Path, *edited: str) -> int:
    """Run the Stop hook with the given files recorded as edited this session."""
    state = workspace / ".claude" / "state"
    state.mkdir(parents=True, exist_ok=True)
    (state / "s.edits").write_text("\n".join(edited) + "\n", encoding="utf-8")
    result = run(
        workspace,
        sys.executable,
        ".claude/hooks/stop_checks.py",
        stdin=json.dumps({"session_id": "s"}),
    )
    return result.returncode


def test_done_runs_only_the_ticket_tests(workspace: Path) -> None:
    """An older failing test does not keep a ticket open: `done` runs only its tests."""
    with_old_failing_test(workspace)
    ticket_in_green(workspace)
    implement(workspace)
    assert tdd(workspace, "done") == 0
    assert phase(workspace) == "none"


def test_suite_runs_every_suite(workspace: Path) -> None:
    """`tdd.py suite` fails on any failing test and passes when all pass."""
    with_old_failing_test(workspace)
    result = run(workspace, sys.executable, "scripts/tdd.py", "suite")
    assert result.returncode == 1
    assert "test_old" in result.stdout
    fix_old_test(workspace)
    assert tdd(workspace, "suite") == 0


def test_epic_close_starts_in_green_and_done_runs_every_suite(workspace: Path) -> None:
    """The closing ticket starts in green; its `done` waits for every suite to pass."""
    with_old_failing_test(workspace)
    assert tdd(workspace, "start", "0003-close-e01", "--epic-close") == 0
    assert phase(workspace) == "green"
    assert tdd(workspace, "done") == 1
    fix_old_test(workspace)
    assert tdd(workspace, "done") == 0
    assert phase(workspace) == "none"


def test_stop_hook_runs_only_the_ticket_tests(workspace: Path) -> None:
    """In a ticket, the Stop hook runs its tests, not the older failing ones."""
    with_old_failing_test(workspace)
    ticket_in_green(workspace)
    implement(workspace)
    assert stop_hook(workspace, "backend/app/calc.py", "backend/tests/test_add.py") == 0


def test_stop_hook_runs_every_suite_in_the_closing_ticket(workspace: Path) -> None:
    """In the closing ticket, the Stop hook runs the whole suite."""
    with_old_failing_test(workspace)
    tdd(workspace, "start", "0003-close-e01", "--epic-close")
    assert stop_hook(workspace, "backend/app/calc.py") == 2
    fix_old_test(workspace)
    assert stop_hook(workspace, "backend/tests/test_old.py") == 0


def closed_epic(workspace: Path) -> None:
    """A previous epic tagged `v0.0.1`, then epic E01 with two tickets and its closing tag.

    E01's first ticket changes `app/calc.py` (`v0.1.1`); its closing ticket adds
    `tests/test_calc.py` (`v0.1.2`).
    """
    requirements = workspace / "requirements"
    requirements.mkdir()
    (requirements / "0002-close-e01.md").write_text(
        "---\nid: '0002'\nkind: epic-close\nepic: E01\ntag: v0.1.2\nprojects: [backend]\n---\n"
    )
    git(workspace, "add", "-A")
    git(workspace, "commit", "-qm", "previous epic")
    git(workspace, "tag", "v0.0.1")
    implement(workspace)
    git(workspace, "add", "-A")
    git(workspace, "commit", "-qm", "ticket 1")
    git(workspace, "tag", "v0.1.1")
    (workspace / "backend" / "tests" / "test_calc.py").write_text(
        "from app.calc import add\n\n\ndef test_adds():\n    assert add(1, 2) == 3\n"
    )
    git(workspace, "add", "-A")
    git(workspace, "commit", "-qm", "closing ticket")
    git(workspace, "tag", "v0.1.2")
    explications = workspace / "explications"
    (explications / "tickets").mkdir(parents=True)
    shutil.copy(REPO / "explications" / "_template.md", explications / "_template.md")


def explication(workspace: Path, files: list[str], scope_line: str = "") -> Path:
    """Write `explications/E01-skeleton.md` with every required template section.

    The backend files go into the "Backend" section; the scope line is added when given.
    """
    template = (workspace / "explications" / "_template.md").read_text(encoding="utf-8")
    parts = [f"# E01 - Esqueleto\n\nAlcance: {scope_line}\n"]
    for heading in HEADING.findall(template):
        name = heading.replace("(si aplica)", "").strip()
        if "(si aplica)" in heading and name != "Backend":
            continue
        body = "| Archivo | Qué hace |\n|---|---|\n" + "".join(
            f"| `{path}` | algo |\n" for path in files
        )
        parts.append(f"## {name}\n\n" + (body if name == "Backend" else "Texto.\n"))
    parts.append("```mermaid\nflowchart LR\n    A --> B\n```\n")
    path = workspace / "explications" / "E01-skeleton.md"
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def check(workspace: Path, path: Path) -> tuple[int, str]:
    """Run the explication checker on a file."""
    result = run(workspace, sys.executable, "scripts/check_explication.py", str(path))
    return result.returncode, result.stderr


def test_epic_explication_must_name_every_file_of_the_epic(workspace: Path) -> None:
    """The scope covers the whole epic: a file of its first ticket must be named too."""
    closed_epic(workspace)
    code, errors = check(workspace, explication(workspace, ["tests/test_calc.py"]))
    assert code == 2
    assert "app/calc.py" in errors


def test_complete_epic_explication_passes(workspace: Path) -> None:
    """Naming every file of the epic and the scope counts passes the checker."""
    closed_epic(workspace)
    files = ["app/calc.py", "tests/test_calc.py"]
    _, errors = check(workspace, explication(workspace, files))
    expected = EXPECTED_SCOPE.search(errors)
    assert expected, errors
    code, errors = check(workspace, explication(workspace, files, expected[1]))
    assert code == 0, errors


def test_a_reopened_epic_is_checked_up_to_its_last_closing_ticket(workspace: Path) -> None:
    """An epic closed twice (a ticket added after its first closing ticket) is checked
    against the scope of its last closing ticket."""
    closed_epic(workspace)
    (workspace / "backend" / "app" / "extra.py").write_text("VALUE = 1\n")
    (workspace / "requirements" / "0003-close-e01-again.md").write_text(
        "---\nid: '0003'\nkind: epic-close\nepic: E01\ntag: v0.1.10\nprojects: [backend]\n---\n"
    )
    git(workspace, "add", "-A")
    git(workspace, "commit", "-qm", "second closing ticket")
    git(workspace, "tag", "v0.1.10")
    code, errors = check(workspace, explication(workspace, ["app/calc.py", "tests/test_calc.py"]))
    assert code == 2
    assert "app/extra.py" in errors


def test_epic_explication_needs_a_closing_ticket(workspace: Path) -> None:
    """Without the epic's closing ticket there is no scope to check against."""
    closed_epic(workspace)
    (workspace / "requirements" / "0002-close-e01.md").unlink()
    code, errors = check(workspace, explication(workspace, ["app/calc.py"]))
    assert code == 2
    assert "E01" in errors


def test_template_placeholder_epic_id_is_reported(workspace: Path) -> None:
    """A leftover `EXX` from the template is a problem."""
    closed_epic(workspace)
    path = explication(workspace, ["app/calc.py", "tests/test_calc.py"])
    path.write_text(path.read_text(encoding="utf-8") + "\nVer EXX.\n", encoding="utf-8")
    code, errors = check(workspace, path)
    assert code == 2
    assert "EXX" in errors


def test_ticket_notes_are_not_checked(workspace: Path) -> None:
    """Notes in `explications/tickets/` are free text."""
    closed_epic(workspace)
    notes = workspace / "explications" / "tickets" / "E01-T1-backend.md"
    notes.write_text("# E01-T1\n\nInstalamos uv.\n", encoding="utf-8")
    assert check(workspace, notes) == (0, "")


def test_explication_scope_starts_at_the_previous_epic(workspace: Path) -> None:
    """The scope of a closing tag lists every file changed since the previous epic."""
    closed_epic(workspace)
    result = run(workspace, sys.executable, "scripts/explication_scope.py", "v0.1.2")
    assert result.returncode == 0, result.stderr
    assert "backend\tM\tapp/calc.py" in result.stdout.splitlines()
    assert "backend\tA\ttests/test_calc.py" in result.stdout.splitlines()
