---
name: comment-style
description: Comment and docstring rule for this project, every language. Load BEFORE writing or editing any source file. No comments inside a function body; functions are documented at the top (Python docstring, TSDoc/KDoc/DocC block). The only exception is a regular expression, whose comment must show an input -> output example.
---

# Comments and docstrings

## The rule

**A function is documented once, at its beginning. Nothing is commented inside its body.**

- **Python**: the docstring (PEP 257, Google style) is the first statement of the body.
  It is not a comment, so it is always allowed. `#` comments inside a function are
  forbidden, trailing ones included.
- **TypeScript / JavaScript**: a TSDoc block `/** ... */` right above the function,
  component or hook. `//` and `/* */` inside the body are forbidden, JSX `{/* */}`
  included. A nested function may carry its own `/** */` block right above it.
- **Kotlin / Swift / other languages**: the language's doc block above the function
  (KDoc `/** */`, DocC `///`), nothing inside the body.

**Single exception: a regular expression.** The comment goes right above the line that
builds or uses it and must show an example of input and output with `->`:

```python
def split_score(text: str) -> tuple[int, int] | None:
    """Read a score typed by a player.

    Args:
        text: raw text, e.g. "3 a 1".

    Returns:
        `(home, away)`, or None when the text is not a score.
    """
    # "3 a 1" -> (3, 1); "3-1" -> (3, 1)
    match = re.fullmatch(r"\s*(\d+)\s*(?:a|-)\s*(\d+)\s*", text)
    return (int(match[1]), int(match[2])) if match else None
```

```ts
/**
 * Extracts the minute from a match event label.
 *
 * @param label - event label as the referee typed it.
 * @returns The minute, or null when missing.
 */
export function parseMinute(label: string): number | null {
  // "Gol 45+2'" -> 45
  const match = /(\d{1,3})(?:\+\d+)?'/.exec(label);
  return match ? Number(match[1]) : null;
}
```

## If a block "needs" a comment

A comment that explains *what* a block does means the block wants to be a function with a
name. Extract it and document the function instead.

## Docstring format (Python, Google style)

- First line: one sentence saying what it does.
- `Args:` omitted when there are no parameters (`self`/`cls` are never listed).
- `Returns:` omitted for `None`. `Raises:` only for exceptions the caller must handle.
- Say what the type hint cannot say: units, ranges, what `None` means.
- Modules and classes also get a docstring explaining why they exist.

## TSDoc format

`@param name - description`, `@returns description`. Exported functions and components
must have it. Tests and config files are exempt.

## What is still allowed

- Module, class and function docstrings; doc blocks above functions.
- Comments at module or class level (outside function bodies), e.g. above a constant.
- Header comments in config files (`.yml`, `.toml`, `Dockerfile`, `.env.example`).
- Tool pragmas: `# noqa`, `# type: ignore`, `// eslint-disable-next-line`,
  `// @ts-expect-error`, `@Suppress(...)`, `// swiftlint:disable:next`.

## How it is enforced

- Python: `scripts/check_comments.py`, run by the PostToolUse hook after every
  Write/Edit. Generated folders are skipped.
- TypeScript (`web/`): the ESLint rule `no-function-body-comments` (copied from the
  workflow kit's `extras/eslint/`), declared in the web project's `on_edit` check.
- Kotlin (`android/`): a custom detekt rule, written with the Android skeleton
  (ADR 0004), declared in the android project's `on_edit` check.
- Swift (`ios/`): the rule `no-function-body-comments` of `ios/LintRules` (SwiftSyntax),
  written with the iOS skeleton (ADR 0004), run by the ios project's `lint-rules` check.
