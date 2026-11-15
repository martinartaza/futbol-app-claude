#!/usr/bin/env python3
r"""Enforce the comment rule on Python files.

No comment is allowed inside a function body. A function is described by its
docstring (PEP 257), which is not a comment and is always allowed. The single
exception is a comment block placed right before a line that builds or uses a
regular expression; that block must show an example with an arrow:

    # "15pm 256gb" -> ("15pm", "256gb")
    match = re.fullmatch(r"(\w+)\s+(\d+gb)", text)

Tool pragmas (`# noqa`, `# type: ignore`, `# pragma: no cover`) are ignored, and so
are generated folders such as Alembic `versions/`. Other languages follow the same rule
through their own linter (for TypeScript, the ESLint rule shipped in the workflow kit,
`extras/eslint/no-function-body-comments.mjs`).

    python3 scripts/check_comments.py <file-or-directory>...

Exits 1 when a violation is found.
"""

from __future__ import annotations

import ast
import io
import re
import sys
import tokenize
from pathlib import Path

PRAGMAS = ("noqa", "type:", "pragma:", "pylint:", "mypy:", "fmt:", "spanish-ok")
SKIPPED_PARTS = {".venv", "versions", "node_modules", "__pycache__"}

# "    x = re.sub(r'a', 'b', s)" -> match; "    x = text.split(',')" -> no match
REGEX_USE = re.compile(
    r"\bre\.(compile|match|fullmatch|search|sub|subn|split|findall|finditer)\("
    r"|\bregex\.\w+\("
)
EXAMPLE_ARROW = "->"


def function_ranges(tree: ast.AST) -> list[tuple[int, int]]:
    """Line ranges, from `def` to last line, of every function in the module.

    Args:
        tree: parsed module.

    Returns:
        Inclusive `(first, last)` line pairs; nested functions are listed too.
    """
    return [
        (node.lineno, node.end_lineno or node.lineno)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def is_pragma(comment: str) -> bool:
    """Whether a comment is a tool directive rather than prose.

    Args:
        comment: raw comment token, including the leading `#`.

    Returns:
        True for `# noqa`, `# type: ignore` and the other known pragmas.
    """
    return comment.lstrip("#").strip().lower().startswith(PRAGMAS)


def comment_block(lines: list[str], number: int) -> tuple[list[str], int]:
    """Full-line comment block that contains a line, plus the first code line after it.

    Args:
        lines: file lines.
        number: 1-based line of one comment of the block.

    Returns:
        The block lines and the 1-based number of the next non-comment line
        (`len(lines) + 1` when the file ends first).
    """
    start = number
    while start > 1 and lines[start - 2].lstrip().startswith("#"):
        start -= 1
    end = number
    while end < len(lines) and lines[end].lstrip().startswith("#"):
        end += 1
    following = end + 1
    while following <= len(lines) and not lines[following - 1].strip():
        following += 1
    return lines[start - 1 : end], following


def findings(text: str) -> list[tuple[int, str]]:
    """Comments of a Python source that break the rule.

    Args:
        text: module source.

    Returns:
        `(line, message)` pairs, empty when the file is clean or does not parse.
    """
    try:
        ranges = function_ranges(ast.parse(text))
    except SyntaxError:
        return []
    if not ranges:
        return []
    lines = text.splitlines()
    found: list[tuple[int, str]] = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError):
        return []
    for token in tokens:
        if token.type != tokenize.COMMENT or is_pragma(token.string):
            continue
        number = token.start[0]
        if not any(first <= number <= last for first, last in ranges):
            continue
        if lines[number - 1][: token.start[1]].strip():
            found.append((number, f"trailing comment inside a function: {token.string}"))
            continue
        block, following = comment_block(lines, number)
        if following <= len(lines) and REGEX_USE.search(lines[following - 1]):
            if not any(EXAMPLE_ARROW in line for line in block):
                found.append(
                    (number, "regex comment without an example: add '\"input\" -> output'")
                )
            continue
        found.append((number, f"comment inside a function body: {token.string.strip()}"))
    return found


def expand(targets: list[Path]) -> list[Path]:
    """Python files under the given paths, skipping venvs and generated migrations.

    Args:
        targets: files or directories.

    Returns:
        Unique `.py` files, in a stable order.
    """
    files: list[Path] = []
    for target in targets:
        candidates = sorted(target.rglob("*.py")) if target.is_dir() else [target]
        files.extend(
            path
            for path in candidates
            if path.suffix == ".py" and path.is_file() and not SKIPPED_PARTS & set(path.parts)
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
        for number, message in findings(path.read_text(encoding="utf-8")):
            total += 1
            print(f"{path}:{number}: {message}", file=sys.stderr)
    if total:
        print(
            f"\n{total} comment(s) break the project rule. Describe functions with their "
            "docstring; if a block needs explaining, extract it into a named function. "
            "Only a regex may carry a comment, and it must show '\"input\" -> output'. "
            "See .claude/skills/comment-style/SKILL.md",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
