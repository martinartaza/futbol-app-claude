"""Tests of the `edit` policy of generated-file rules.

A generated rule may say `"edit": "deny"` for files that are never touched by hand
(the GraphQL schema, the lock file): editing or overwriting them is denied with the
command that generates them. Rules without it keep asking the user before an edit
(migrations, where the generator can miss a rename or a data backfill).
"""

from __future__ import annotations

import json
from pathlib import Path

from test_workflow_tooling import CONFIG, edit, workspace

__all__ = ["workspace"]


def deny_rules(workspace: Path) -> Path:
    """Add never-edited generated rules to the workspace config and create their files."""
    config = json.loads(json.dumps(CONFIG))
    config["projects"]["backend"]["generated"] += [
        {
            "glob": "schema.graphql",
            "generator": "strawberry export-schema",
            "how": "Run strawberry export-schema.",
            "edit": "deny",
        },
        {
            "glob": "uv.lock",
            "generator": "uv lock",
            "how": "Use uv add or uv remove.",
            "edit": "deny",
        },
    ]
    (workspace / "workflow.json").write_text(json.dumps(config), encoding="utf-8")
    (workspace / "backend" / "schema.graphql").write_text("type Query { ok: Boolean }\n")
    (workspace / "backend" / "uv.lock").write_text("version = 1\n")
    (workspace / "backend" / "alembic" / "versions").mkdir(parents=True)
    (workspace / "backend" / "alembic" / "versions" / "x.py").write_text("")
    return workspace


def test_editing_a_never_edited_file_is_denied(workspace: Path) -> None:
    """Edit on an existing schema is denied and points to the generator command."""
    decision = edit(deny_rules(workspace), "backend/schema.graphql")
    assert decision["permissionDecision"] == "deny"
    assert "strawberry export-schema" in decision["permissionDecisionReason"]


def test_overwriting_a_never_edited_file_is_denied(workspace: Path) -> None:
    """Write over an existing lock file is denied too."""
    decision = edit(deny_rules(workspace), "backend/uv.lock", "Write")
    assert decision["permissionDecision"] == "deny"
    assert "uv add" in decision["permissionDecisionReason"]


def test_rules_without_edit_policy_still_ask(workspace: Path) -> None:
    """An existing migration still asks the user before an edit."""
    decision = edit(deny_rules(workspace), "backend/alembic/versions/x.py")
    assert decision["permissionDecision"] == "ask"
