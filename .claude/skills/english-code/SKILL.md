---
name: english-code
description: Code is written in English even though the conversation is in Spanish. Load BEFORE writing or editing any code, schema, route or file name. Defines what goes in English, what stays in Spanish, and points to the domain glossary (scripts/glossary.py).
---

# Code in English

## The rule

**We talk in Spanish; the code is English.** The user writes in Spanish and gets answers
in Spanish; everything an interpreter or compiler reads is English.

Always English:

- Classes, functions, methods, variables, constants, types, components, hooks, screens.
- Tables, columns, indexes, constraints and enums in the database.
- HTTP routes, query parameters, JSON keys, form field names, deep-link paths.
- File and module names, style names, test ids.
- **Comments, docstrings and doc blocks.**
- Commit messages, requirement, bug and ADR files.
- Migration messages (`-m "add_match_table"`).

Always Spanish (Rioplatense):

- Text the user reads: UI copy, error messages shown on screen, push notifications,
  push notification and email bodies.
- Business data: team names, field names, city names.
- Explications (`explications/`) and the conversation.

The border: if a person reads it in the product, Spanish. If a program reads it, English.

## Glossary

`scripts/glossary.py` is the single source of truth for domain names. Need a term that
is not there? **Add it to the glossary first**, then use it. One concept, one
translation. Domain terms are added as requirements introduce them, for example:

| Spanish | English |
|---|---|
| Partido | `match` |
| Equipo | `team` |
| Cancha | `pitch` |
| Torneo | `tournament` |
| Jugador | `player` |

## Enforcement

`scripts/check_language.py` runs in the PostToolUse hook. It flags identifiers built
from glossary words and comments or docstrings written in Spanish. String literals are
never checked, and quoted fragments inside comments are ignored, so a regex example such
as `# "3 a 1" -> (3, 1)` is fine. A line ending in `spanish-ok` is skipped; use it only
for a genuine exception and say why.

## Known traps

- `user` is reserved in PostgreSQL: name the table `user_account` if ever needed.
- Renaming an identifier does not rename the strings that mention it (table names,
  JSON keys consumed by the app, test ids). Search for them too.
