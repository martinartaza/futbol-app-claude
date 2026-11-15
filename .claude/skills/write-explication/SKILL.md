---
name: write-explication
description: Write the Spanish walkthrough explications/EXX-<slug>.md of a closed epic from explications/_template.md - how the epic's new piece was built (alternatives weighed, installation, configuration, problems), its flows, and every file of its scope briefly - from the ticket notes in explications/tickets/ and the scope taken from git tags; then update the "Cómo está hoy" section of older explications it made out of date. Use when the user asks for an explication ("creá el explications de la E04", "explicame la épica"). Refuses while the epic's closing ticket is not committed and tagged.
argument-hint: "<epic id, e.g. E04>"
---

# Write an epic explication

Epic: `$ARGUMENTS` (if empty, the epic just closed in the conversation).

The user reads epic and requirements → explication → code. Each epic brings one new,
large piece (social login, the radar, live chat, maps): the explication tells **how it
was built**, and lists every committed file briefly. Its scope comes from git, never
from memory, and a blocking checker verifies it (ADR 0004 section 6).

## 1. Scope first

The epic must be `done`: its closing ticket (`kind: epic-close`) is tagged. Its tag is
the epic's last, `v0.E.T`. From the workspace root:

```bash
python3 scripts/explication_scope.py v0.3.5
```

- Exit code 1: **stop** and tell the user, in Spanish, the message as printed (a tag
  missing, uncommitted changes). Do not commit or tag on your own.
- Exit code 0: one line per changed file since the previous epic's last tag,
  `<project> <A|M|D|R> <path>`. That list is the scope: every file of it goes into the
  explication.

## 2. Read the sources

- The ticket notes `explications/tickets/EXX-T*.md` of this epic, all of them: they are
  the source of "Cómo se implementó" (alternatives weighed and why, installation,
  external configuration, commands, problems and solutions).
- The epic file, its requirements and bugs (their `tag` starts with `v0.E.`), the
  closing ticket's *Findings*, and the ADRs they name.
- The code of the scope (`git diff <previous> <tag> -- <path>` in each project).
- Never another explication as a model: the template is the **only** format reference.

## 3. Write from the template

- Copy `explications/_template.md` to `explications/EXX-<slug>.md`.
- **Cómo se implementó** is the core: one `###` per new piece. Only the alternatives
  really weighed with the developer (two or three, never a catalogue), which one was
  chosen and why; the library or service, how it was installed and configured
  (including outside the code); the commands to reproduce it; the problems and how they
  were solved.
- **Files**: every scope file in backticks in its project's section (`section` in
  `workflow.json`) or in "Tests" (with the project prefix), one per backtick span,
  deleted and renamed ones too. A short description: three words for what every module
  has (`router.py`: ruteo), one line for the files that are this epic's own.
- Keep the `##` headings of the template, in order; delete the "(si aplica)" sections
  that do not apply and every template comment; replace `EXX` and `NNNN`.
- Spanish, Mermaid only for diagrams.
- Add the explication to `explications/README.md`: a row in the table and a node in the
  diagram.

## 4. The checker

The PostToolUse hook runs `scripts/check_explication.py` on every Write/Edit of the file
and blocks with what is missing: scope files, template sections or their order, the
Mermaid diagram, leftover placeholders, the scope count line. Fix it until it passes.

## 5. Older explications made out of date

Read only the files tables and the "Cómo está hoy" section of each older explication,
never the rest.

1. **Candidates**: scope files that appear in the files tables of an older explication.
2. **Relevant or not**: relevant when someone who reads the old explication and then
   opens the code would be confused (a behaviour, name, signature, location or rule it
   states has changed). Formatting, imports or unrelated additions are not.
3. **Offer, then write only if the user accepts**: update or add the piece's row in
   "Cómo está hoy" ("Hoy" and "Cambió en"). The body is a snapshot: never edit it.

## 6. Report

In Spanish: the file written, how many scope files it covers ("X de <project>, Y de
<project> y Z de tests"), that the checker passed, and the older explications updated
or offered. Nothing is committed.
