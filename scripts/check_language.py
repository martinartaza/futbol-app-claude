#!/usr/bin/env python3
"""Enforce English in code: identifiers, comments and docstrings.

String literals are not checked, because the text users read is Spanish on purpose
(UI copy, error messages, notifications). Quoted fragments inside comments are ignored
for the same reason, so `# e.g. "partido del domingo"` is fine.

- Identifiers are split into words (snake_case and camelCase) and matched against
  `glossary.py`; a hit is reported with its English name.
- Comments and docstrings are reported when they carry Spanish characters or at least
  two common Spanish function words.

Python is read with its tokenizer and AST. C-family languages (TypeScript, JavaScript,
Kotlin, Swift, Dart) are read with a small scanner: `//` and `/* */` comments, and
names declared with a keyword (`const`, `fun`, `func`, `class`...).

A line ending in `spanish-ok` is skipped.

    python3 scripts/check_language.py <file-or-directory>...

Exits 1 when a violation is found.
"""

from __future__ import annotations

import ast
import io
import re
import sys
import tokenize
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from glossary import GLOSSARY  # noqa: E402

PYTHON_EXT = {".py"}
C_FAMILY_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".kt", ".kts", ".swift", ".dart"}
SKIPPED_PARTS = {
    ".venv",
    "versions",
    "node_modules",
    ".next",
    "__pycache__",
    "build",
    ".gradle",
    "Pods",
    ".expo",
    "DerivedData",
}
SKIP_MARK = "spanish-ok"

SPANISH_CHARS = re.compile(r"[áéíóúñÁÉÍÓÚÑ¿¡]")
SPANISH_WORDS = {
    "el",
    "los",
    "las",
    "del",
    "una",
    "para",
    "que",
    "esta",
    "este",
    "cuando",
    "porque",
    "pero",
    "hay",
    "son",
    "debe",
    "puede",
    "tiene",
    "sin",
    "donde",
}
# 'a "quoted" `b` c' -> 'a   c'
QUOTED = re.compile(r"\"[^\"]*\"|'[^']*'|`[^`]*`")
# "matchListCron" -> ["match", "List", "Cron"]; "get_score_list" -> ["get", "score", "list"]
WORD_PARTS = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])")
# "export const obtenerPartido = () =>" -> "obtenerPartido"; "fun crearEquipo(" -> "crearEquipo"
DECLARATION = re.compile(
    r"\b(?:const|let|var|val|function|fun|func|class|struct|interface|protocol|type"
    r"|typealias|enum|object)\s+([A-Za-z_$][\w$]*)"
)


def fold(word: str) -> str:
    """Lowercase a word and strip its accents.

    Args:
        word: any word.

    Returns:
        The word in ASCII lowercase, e.g. "Ubicación" becomes "ubicacion".
    """
    decomposed = unicodedata.normalize("NFKD", word.lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def spanish_terms(identifier: str) -> list[str]:
    """Glossary words found in an identifier.

    Args:
        identifier: a name from the code.

    Returns:
        `"spanish -> english"` hints, one per glossary word in the name.
    """
    hits = []
    for part in WORD_PARTS.findall(identifier):
        word = fold(part)
        for candidate in (word, word[:-1], word[:-2]):
            if candidate in GLOSSARY:
                hits.append(f"{part} -> {GLOSSARY[candidate]}")
                break
    return hits


def is_spanish_prose(text: str) -> bool:
    """Whether a comment or docstring is written in Spanish.

    Args:
        text: comment or docstring content.

    Returns:
        True when, after dropping quoted fragments, it has Spanish characters or two
        different Spanish function words.
    """
    prose = QUOTED.sub(" ", text)
    if SPANISH_CHARS.search(prose):
        return True
    words = {fold(word) for word in re.findall(r"[A-Za-zÀ-ÿ]+", prose)}
    return len(words & SPANISH_WORDS) >= 2


def python_findings(text: str) -> list[tuple[int, str]]:
    """Spanish identifiers, comments and docstrings in a Python source.

    Args:
        text: module source.

    Returns:
        `(line, message)` pairs.
    """
    found: list[tuple[int, str]] = []
    lines = text.splitlines()
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
        tree = ast.parse(text)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return []
    for token in tokens:
        number = token.start[0]
        if token.type not in (tokenize.NAME, tokenize.COMMENT):
            continue
        if lines[number - 1].rstrip().endswith(SKIP_MARK):
            continue
        if token.type == tokenize.NAME:
            found.extend(
                (number, f"Spanish identifier '{token.string}': {hit}")
                for hit in spanish_terms(token.string)
            )
        elif is_spanish_prose(token.string):
            found.append((number, f"Spanish comment: {token.string.strip()}"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node, clean=False)
            if docstring and is_spanish_prose(docstring):
                line = node.body[0].lineno if node.body else 1
                found.append((line, "Spanish docstring"))
    return list(dict.fromkeys(found))


def comment_spans(text: str) -> list[tuple[int, int, int]]:
    """Where the comments of a C-family source are, skipping string literals.

    Args:
        text: source.

    Returns:
        `(line, start, end)` per comment: its first line and its character range.
    """
    comments: list[tuple[int, int, int]] = []
    index, line, quote = 0, 1, ""
    while index < len(text):
        char = text[index]
        if char == "\n":
            line += 1
        if quote:
            if char == "\\":
                index += 2
                continue
            if char == quote:
                quote = ""
        elif char in "\"'`":
            quote = char
        elif text.startswith("//", index):
            end = text.find("\n", index)
            end = len(text) if end < 0 else end
            comments.append((line, index, end))
            index = end
            continue
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            end = len(text) if end < 0 else end + 2
            comments.append((line, index, end))
            line += text.count("\n", index, end)
            index = end
            continue
        index += 1
    return comments


def c_family_findings(text: str) -> list[tuple[int, str]]:
    """Spanish declared names and comments in a C-family source.

    Args:
        text: source.

    Returns:
        `(line, message)` pairs.
    """
    found: list[tuple[int, str]] = []
    lines = text.splitlines()
    for number, line in enumerate(lines, start=1):
        if line.rstrip().endswith(SKIP_MARK):
            continue
        for name in DECLARATION.findall(line):
            found.extend(
                (number, f"Spanish identifier '{name}': {hit}") for hit in spanish_terms(name)
            )
    for number, start, end in comment_spans(text):
        comment = text[start:end]
        if not lines[number - 1].rstrip().endswith(SKIP_MARK) and is_spanish_prose(comment):
            found.append((number, f"Spanish comment: {comment.splitlines()[0].strip()}"))
    return found


def expand(targets: list[Path]) -> list[Path]:
    """Checkable files under the given paths.

    Args:
        targets: files or directories.

    Returns:
        Unique source files, skipping dependencies, build output and migrations.
    """
    extensions = PYTHON_EXT | C_FAMILY_EXT
    files: list[Path] = []
    for target in targets:
        candidates = sorted(target.rglob("*")) if target.is_dir() else [target]
        files.extend(
            path
            for path in candidates
            if path.suffix in extensions and path.is_file() and not SKIPPED_PARTS & set(path.parts)
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
        text = path.read_text(encoding="utf-8")
        results = python_findings(text) if path.suffix in PYTHON_EXT else c_family_findings(text)
        for number, message in results:
            total += 1
            print(f"{path}:{number}: {message}", file=sys.stderr)
    if total:
        print(
            f"\n{total} Spanish fragment(s) in code. Identifiers, comments and docstrings "
            "are written in English; user-facing strings stay in Spanish. Use the names in "
            "scripts/glossary.py. See .claude/skills/english-code/SKILL.md",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
