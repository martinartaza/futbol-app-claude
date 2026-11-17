"""Tests of requirement 0003: `scripts/sync_contracts.py` (ADR 0004 section 5, ADR 0008).

The script validates `design-tokens/base.json` (W3C Design Tokens format, a white and a
dark value per token in `$extensions.modes`, references as `{path}`, background pairs in
`$extensions.pair`), copies `backend/schema.graphql` into each client present and
generates the web tokens (`tokens.css`, `tokens.ts`). Each test runs the script in a
temporary workspace.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[1]
SCHEMA = 'type Query {\n  """The backend\'s state."""\n  health: Health!\n}\n'
GENERATED = Path("web/src/generated")


def color(white: str, dark: str, pair: str | None = None) -> dict[str, Any]:
    """A colour token with its white and dark values and, for a background, its pair."""
    extensions: dict[str, Any] = {"modes": {"white": white, "dark": dark}}
    if pair:
        extensions["pair"] = pair
    return {"$type": "color", "$extensions": extensions}


def valid_tokens() -> dict[str, Any]:
    """A small valid tree: primitives, a role pair and a component token."""
    return {
        "color": {
            "neutral": {
                "0": color("#FFFFFF", "#FFFFFF"),
                "900": color("#1B1F1C", "#1B1F1C"),
                "950": color("#121614", "#121614"),
                "100": color("#E8EDE9", "#E8EDE9"),
            }
        },
        "surface": color("{color.neutral.0}", "{color.neutral.950}", pair="on-surface"),
        "on-surface": color("{color.neutral.900}", "{color.neutral.100}"),
        "nav": {
            "item": {
                "label": {"color": color("{on-surface}", "{on-surface}")},
                "gap": {
                    "$type": "dimension",
                    "$extensions": {"modes": {"white": "8px", "dark": "8px"}},
                },
                "weight": {
                    "$type": "fontWeight",
                    "$extensions": {"modes": {"white": 600, "dark": 600}},
                },
                "font": {
                    "$type": "fontFamily",
                    "$extensions": {"modes": {"white": "Inter", "dark": "Inter"}},
                },
            }
        },
    }


def write_tokens(workspace: Path, tokens: dict[str, Any]) -> None:
    """Write `design-tokens/base.json`."""
    (workspace / "design-tokens" / "base.json").write_text(json.dumps(tokens, indent=2))


def sync(workspace: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run the script in the workspace."""
    return subprocess.run(
        [sys.executable, "scripts/sync_contracts.py", *args],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=False,
    )


def output(result: subprocess.CompletedProcess[str]) -> str:
    """Everything the script printed."""
    return result.stdout + result.stderr


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """A workspace with the scripts, a valid token tree, the backend schema and a web client."""
    shutil.copytree(REPO / "scripts", tmp_path / "scripts")
    (tmp_path / "design-tokens").mkdir()
    write_tokens(tmp_path, valid_tokens())
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "schema.graphql").write_text(SCHEMA)
    (tmp_path / "web").mkdir()
    return tmp_path


def test_ac1_generates_web_tokens_for_white_and_dark(workspace: Path) -> None:
    """AC-1: white values in `:root`, dark under `prefers-color-scheme: dark`; names typed."""
    assert sync(workspace).returncode == 0
    css = (workspace / GENERATED / "tokens.css").read_text()
    root, dark = css.split("@media (prefers-color-scheme: dark)")
    assert ":root" in root
    assert "--surface: #FFFFFF;" in root
    assert "--surface: #121614;" in dark
    assert "--nav-item-gap: 8px;" in root
    typescript = (workspace / GENERATED / "tokens.ts").read_text()
    for name in ("surface", "on-surface", "nav.item.label.color", "color.neutral.0"):
        assert f'"{name}"' in typescript
    assert "export type TokenName" in typescript
    assert "export function token(" in typescript
    assert "var(--nav-item-label-color)" in typescript or "var(--${" in typescript


def test_ac2_references_resolve_per_theme(workspace: Path) -> None:
    """AC-2: a component token pointing at a role takes the role's value in each theme."""
    assert sync(workspace).returncode == 0
    root, dark = (
        (workspace / GENERATED / "tokens.css")
        .read_text()
        .split("@media (prefers-color-scheme: dark)")
    )
    assert "--nav-item-label-color: #1B1F1C;" in root
    assert "--nav-item-label-color: #E8EDE9;" in dark


@pytest.mark.parametrize(
    ("broken", "named"),
    [
        (lambda t: t["on-surface"]["$extensions"]["modes"].pop("dark"), "on-surface"),
        (lambda t: t["on-surface"]["$extensions"]["modes"].pop("white"), "on-surface"),
        (
            lambda t: t["on-surface"]["$extensions"]["modes"].update(white="{color.missing}"),
            "color.missing",
        ),
        (
            lambda t: t["color"]["neutral"]["0"]["$extensions"]["modes"].update(
                white="{color.neutral.0}"
            ),
            "color.neutral.0",
        ),
        (
            lambda t: t["nav"]["item"]["gap"]["$extensions"]["modes"].update(white="eight"),
            "nav.item.gap",
        ),
        (
            lambda t: t["nav"]["item"]["font"]["$extensions"]["modes"].update(dark="Comic Sans"),
            "nav.item.font",
        ),
    ],
    ids=["no-dark", "no-white", "unknown-reference", "cycle", "wrong-type", "font-not-bundled"],
)
def test_ac3_an_invalid_token_fails_naming_it(workspace: Path, broken: Any, named: str) -> None:
    """AC-3: a missing mode, an unknown reference, a cycle or a wrong value fail by name."""
    tokens = valid_tokens()
    broken(tokens)
    write_tokens(workspace, tokens)
    result = sync(workspace)
    assert result.returncode == 1
    assert named in output(result)
    assert not (workspace / GENERATED / "tokens.css").exists()


def test_ac3_every_problem_is_reported_at_once(workspace: Path) -> None:
    """AC-3: all problems are listed in one run, not only the first."""
    tokens = valid_tokens()
    tokens["on-surface"]["$extensions"]["modes"].pop("dark")
    tokens["nav"]["item"]["gap"]["$extensions"]["modes"]["white"] = "eight"
    write_tokens(workspace, tokens)
    printed = output(sync(workspace))
    assert "on-surface" in printed
    assert "nav.item.gap" in printed


def test_ac4_a_pair_below_aa_fails_with_theme_and_ratio(workspace: Path) -> None:
    """AC-4: a background and foreground pair under 4.5:1 fails, naming both and the ratio."""
    tokens = valid_tokens()
    tokens["on-surface"]["$extensions"]["modes"]["dark"] = "#C62F27"
    write_tokens(workspace, tokens)
    result = sync(workspace)
    assert result.returncode == 1
    printed = output(result)
    assert "surface" in printed
    assert "on-surface" in printed
    assert "dark" in printed
    assert "3.33" in printed


def test_ac5_the_schema_is_copied_byte_for_byte(workspace: Path) -> None:
    """AC-5: `backend/schema.graphql` lands unchanged in the web client."""
    assert sync(workspace).returncode == 0
    assert (workspace / GENERATED / "schema.graphql").read_bytes() == SCHEMA.encode()


def test_ac6_check_fails_on_edited_or_stale_files(workspace: Path) -> None:
    """AC-6: `--check` fails after a hand edit or a token change, passes after a run."""
    assert sync(workspace).returncode == 0
    assert sync(workspace, "--check").returncode == 0
    css = workspace / GENERATED / "tokens.css"
    css.write_text(css.read_text().replace("#FFFFFF", "#000000"))
    edited = sync(workspace, "--check")
    assert edited.returncode == 1
    assert "tokens.css" in output(edited)
    assert sync(workspace).returncode == 0
    tokens = valid_tokens()
    tokens["color"]["neutral"]["900"]["$extensions"]["modes"]["white"] = "#000000"
    write_tokens(workspace, tokens)
    assert sync(workspace, "--check").returncode == 1
    assert sync(workspace).returncode == 0
    assert sync(workspace, "--check").returncode == 0


def test_ac7_two_runs_leave_the_same_files(workspace: Path) -> None:
    """AC-7: generation is deterministic (no dates, stable order)."""
    assert sync(workspace).returncode == 0
    first = {path.name: path.read_bytes() for path in (workspace / GENERATED).iterdir()}
    assert sync(workspace).returncode == 0
    second = {path.name: path.read_bytes() for path in (workspace / GENERATED).iterdir()}
    assert first == second
    assert set(first) == {"tokens.css", "tokens.ts", "schema.graphql"}


def test_ac8_the_committed_token_tree_is_valid(workspace: Path) -> None:
    """AC-8: the real `design-tokens/base.json` validates, its pairs meeting AA."""
    shutil.copy(REPO / "design-tokens" / "base.json", workspace / "design-tokens" / "base.json")
    result = sync(workspace)
    assert result.returncode == 0, output(result)
    css = (workspace / GENERATED / "tokens.css").read_text()
    for role in ("--surface:", "--primary:", "--team-red:", "--team-blue:", "--error:"):
        assert role in css
