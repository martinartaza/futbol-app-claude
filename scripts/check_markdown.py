#!/usr/bin/env python3
"""Reject ASCII-art diagrams in Markdown: diagrams are written in Mermaid.

Inside a fenced block that is not ```mermaid, a line is reported when it draws
boxes or arrows (box-drawing characters, `+--`, `-->`, `==>`, `→`, `↓`, a lone `|`
or `v` connector). Outside code blocks only box-drawing characters are reported,
so Markdown tables and prose arrows stay valid.

    python3 scripts/check_markdown.py <file-or-directory>...

Exits 1 when a violation is found.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKIPPED_PARTS = {"node_modules", ".next", ".venv"}

# "┌──────┐" -> match; "| a | b |" -> no match
BOX_DRAWING = re.compile(r"[─-╿▀-▟]")
# "A --> B", "+----+", "  |  ", "  v  ", "A → B" -> match; "a - b" -> no match
ASCII_ART = re.compile(r"\+-{2,}|-{2,}>|<-{2,}|={2,}>|[←-⇿▲-▼▶◀]|^\s*[|v^]\s*$")
# "```mermaid" -> ("```", "mermaid"); "~~~" -> ("~~~", "")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([\w-]*)")


def findings(text: str) -> list[tuple[int, str]]:
    """ASCII-art lines of a Markdown document.

    Args:
        text: Markdown source.

    Returns:
        `(line, content)` pairs.
    """
    found: list[tuple[int, str]] = []
    fence, language = "", ""
    for number, line in enumerate(text.splitlines(), start=1):
        opening = FENCE.match(line)
        if opening and not fence:
            fence, language = opening.group(1), opening.group(2).lower()
            continue
        if fence and line.strip().startswith(fence):
            fence, language = "", ""
            continue
        if fence and language == "mermaid":
            continue
        pattern = ASCII_ART if fence else BOX_DRAWING
        if BOX_DRAWING.search(line) or pattern.search(line):
            found.append((number, line.strip()))
    return found


def expand(targets: list[Path]) -> list[Path]:
    """Markdown files under the given paths.

    Args:
        targets: files or directories.

    Returns:
        Unique `.md` files, skipping dependencies.
    """
    files: list[Path] = []
    for target in targets:
        candidates = sorted(target.rglob("*.md")) if target.is_dir() else [target]
        files.extend(
            path
            for path in candidates
            if path.suffix == ".md" and path.is_file() and not SKIPPED_PARTS & set(path.parts)
        )
    return list(dict.fromkeys(files))


def main(argv: list[str]) -> int:
    """Check every given file and print each violation with its location.

    Args:
        argv: files or directories to check.

    Returns:
        Process exit code: 1 when any violation is found.
    """
    total = 0
    for path in expand([Path(arg) for arg in argv]):
        for number, line in findings(path.read_text(encoding="utf-8")):
            total += 1
            print(f"{path}:{number}: ASCII-art diagram line: {line}", file=sys.stderr)
    if total:
        print(
            f"\n{total} line(s) draw a diagram in ASCII. Write diagrams as a ```mermaid "
            "block (flowchart, sequenceDiagram, erDiagram, stateDiagram-v2).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
