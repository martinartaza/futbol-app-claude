---
name: implement-requirement
description: Implement an approved requirement from requirements/NNNN-*.md end to end - plan, tests first, code, migrations, checks - up to "ready to test", then the commit summary with its v0.E.T tag when the user says it is finished (the architecture review and the full suite run once per epic, skill close-epic). Use when the user approves a requirement ("aprobado", "dale con el 0003") or asks to implement one. Refuses to start while the status is pending.
argument-hint: "<requirement number, e.g. 0003>"
---

# Implement a requirement

Requirement: `$ARGUMENTS`

!`f=$(ls requirements/$ARGUMENTS-*.md 2>/dev/null | head -1); if [ -n "$f" ]; then echo "File: $f"; grep -m1 '^status:' "$f"; else echo "No requirement file matches '$ARGUMENTS'"; fi`

## Before starting

- If the status is `pending` and the user has **just approved it in this conversation**,
  set `status: approved` and fill `approved` with today's date. If they have not
  approved it, ask; do not start.
- **Tag** (ADR 0004 section 6): fill `tag` with `v0.E.T`. E is the `version` of its
  epic; if the epic has none, it is the first ticket: the epic moves to `in progress`
  with the next `version` (one more than the highest `version` of any epic) — tell the
  user. T is the next free ticket number of the epic: one more than the highest `tag`
  of its requirements, bugs and direct changes.
- If the status is `done`, ask what they want changed: that is a new requirement.
- Read the whole requirement, its epic, the ADRs it names, and re-read `CLAUDE.md` rules.

## Implementation loop

TDD at the user's pace (skill `testing`): tests first, the user approves, then code.

1. **Plan** in Spanish, briefly: files to create or change per project, migrations,
   tests. Find the files in `docs/agent/codebase-map.md` before searching the code.
   Proceed unless the plan reveals a decision the requirement did not settle; then ask.
   A doubtful design decision is raised **now**, not left for the review.
2. **Start the task**: `python3 scripts/tdd.py start NNNN-slug`. Phase red.
3. **Tests first**, in **one new test file** per project: at least one per acceptance
   criterion (`AC-n` in the test name or docstring). Run them; they must fail for the
   right reason. Only these tests run during the ticket; the full suite runs in the
   epic's closing ticket.
4. **Stop and ask**: show the user, in Spanish, the tests criterion by criterion and
   that they fail. End the turn. Run `python3 scripts/tdd.py green` only after an
   explicit OK; its permission prompt is the user's approval.
5. **Code** following the skills `english-code`, `comment-style` and the architecture
   skills. Use Write/Edit (not shell edits) so the hooks format and check every file.
6. **Models changed?** Skill `migrations`: autogenerate, review, upgrade.
7. **Make the tests pass** by changing the implementation. Changing an approved test
   needs the user's permission for that test.
8. **Tick the checklist** in the requirement as items are completed.
9. **Ticket notes**, in Spanish, in `explications/tickets/<epic id>-T<T>-<slug>.md`
   (`E04-T02-social-login.md`, from `explications/tickets/_template.md`): add to them
   **when it happens**, not at the end. They
   hold what the epic explication will need and the code does not show: what was
   installed and how, external configuration (a provider console, keys in `.env`),
   commands, problems and how they were solved, and the alternatives that were really
   weighed with the user (two or three, never a catalogue) and why one was chosen.

## Closing

Closing has two moments: ready to test, then ready to commit.

**Ready to test** (the tests pass):

- Verify every acceptance criterion against a passing test or a manual check you
  actually ran (say which).
- **UI tickets** (ADR 0008 section 7): new or changed components have their tokens in
  white and dark in `design-tokens/base.json`, screenshot tests in both themes on every
  client, and the summary lists the six checks (Android, iOS, web × white, dark) with
  which ones you ran and which the user still has to try.
- Keep `status: approved` (it becomes `done` when the user, after testing, says it is
  finished). Add an *Implementation notes* section: files touched, migrations
  generated, deviations agreed with the user.
- Summarise in Spanish. Every file count reads "X de <project>, Y de <project> y Z de
  tests" (tests counted apart, with the labels of `workflow.json`).
- End with: **"Listo para probar."** Keep the TDD task open. Do not suggest a commit:
  the user tests by hand and usually asks for changes (requirement updated, a new TDD
  round).

**Ready to commit** (the user says the work is finished):

- `python3 scripts/tdd.py done` (the requirement's tests). The architecture review and
  the full suite are not run here: they run once per epic, in its closing ticket.
- `status: done` with today's date in `done`.
- Complete the ticket notes: anything from this conversation still missing.
- **Update `docs/agent/codebase-map.md`**: only the lines for what this requirement
  added, moved, renamed or removed, and the snapshot line (`after NNNN (v0.E.T)`).
- Summarise in Spanish and end with two paragraphs:
  1. **Commit, push and tag.** Commit in the code repositories that changed (never the
     workspace root documents repository, which the user commits when they decide);
     the tag goes on all four code repositories. Suggest the message in English
     (`feat(0015): match list`) and the requirement's `tag`:
     ```text
     git tag -a v0.3.2 -m "0015: match list" && git push origin v0.3.2
     ```
  2. **Epic.** If this was the last open ticket of the epic, offer its closing ticket
     (skill `close-epic`).
- Claude commits, pushes or tags only when the user explicitly asks (the hook asks too).
