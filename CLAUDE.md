# MatchFulbito

MatchFulbito makes amateur football easier to organise. A group of friends that plays
once a week signs up for each match through the app, and when players are missing the
organiser can announce it on other social networks. It is used by amateur players,
tournament organisers and pitches (football venues). Platforms: Android, iOS and web,
built with native technologies. Users sign in with social login.

The heart of the product is the **player radar** (the hexagon in the logo), like the
player charts of football video games: each player rates themselves on a set of skills
(speed, stamina, passing, dribbling, shooting, defence), other players vote on them, and
the radar appears everywhere: a player's self-rating and the votes received, a vote
being cast, and the two teams (red and blue) compared by their averages when teams are
picked. The number of skills is not fixed.

The display name (MatchFulbito) may change; it lives only in the store listing and the
app's display-name setting, never in identifiers, module names or routes. What never
changes is the Android package (see "Store identity").

The same holds for **domains and host names**: in local, staging and production they
are not defined for good and may change with the name. They live only in each
project's environment (`.env`, Vercel and build settings), never in code, tests or
documents as fixed values. Local today: `local-fulbito` (web) and `api.local-fulbito`
(backend), behind the local Traefik.

- **Stage**: development (since 2026-11-02). Everything built
  is definitive and works for real; a screen that is not ready says so ("Próximamente")
  instead of pretending.
- Feature specs: `requirements/` (see its README). **Nothing is built without an approved
  requirement**, except when the user explicitly asks for a direct change, or a bug of
  `bugs/` (behaviour that differs from an approved requirement, fixed with a red test
  first).
- Architecture decisions: `docs/adr/` (see its README). Requirements say *what*; ADRs
  say *how*. A cross-cutting decision is an ADR, never a requirement.
- Epics: `epics/`: large product themes, still open. **Before proposing a
  requirement or an ADR, read the related epics.**
- `docs/production-readiness.md`: what is still missing before real production.

## Talking with the user

- **Always reply in Spanish (Rioplatense).** The user writes in Spanish.
- **Code is in English**: identifiers, comments, docstrings, commits, requirement, bug and
  ADR files. Skill `english-code`.
- The user likes to discuss and agree before coding ("conversemos"); propose, then wait.
- **Name the prior art.** When a proposal goes beyond the basics, name the established
  pattern, standard or practice and give its main reference from memory (approximate is
  fine; no web search unless asked). When adopted, add it to `docs/prior-art.md` and to
  the ADR's References. If it has no formal name, say so.

## Layout

| Path | What |
|---|---|
| `backend/` | FastAPI + Strawberry GraphQL + SQLAlchemy (async) + Alembic + PostgreSQL, managed with `uv`. Own git repository. ADR 0001, 0003. |
| `android/` | Android app: Kotlin + Jetpack Compose + Apollo Kotlin. Own git repository. ADR 0004. |
| `ios/` | iOS app: Swift + SwiftUI + Apollo iOS. Own git repository. ADR 0004. |
| `web/` | Web client: Next.js + TypeScript + Apollo Client, on Vercel. Own git repository. ADR 0004. |
| `design-tokens/` | The one source of colours, fonts, radii, spacing; generated into each client by `scripts/sync_contracts.py`. |
| `requirements/` | Numbered requirement files: `pending` → `approved` → `done`. |
| `bugs/` | Bug files `BNNN-slug.md`: `reported` → `reproduced` → `fixed` (or `requirement`). |
| `docs/adr/` | Architecture decision records: `proposed` → `accepted` → `superseded`. |
| `epics/` | Epics. |
| `docs/prior-art.md` | The established patterns, standards and practices we follow: what each is, where we use it, main reference. |
| `docs/agent/codebase-map.md` | Where things are, for Claude. **Read the section you need before exploring the code.** |
| `docs/agent/bug-reproduction.md` | How Claude reproduces bugs in local. |
| `explications/` | **In Spanish.** One explication per epic (how its new piece was built, every file briefly), written when the user asks after the epic closes; `tickets/` holds the notes of each ticket, written while it is built. While developing, Claude only **writes** ticket notes here and reads **nothing**. |
| `scripts/` | Workflow tooling: `workflow.py` (reads `workflow.json`), `tdd.py`, rule checkers, explication scope, glossary. |
| `workflow.json` | The projects, what is source and test in each, and their format, lint and test commands. |
| `secrets/` | Store credentials (upload keystore, passwords). Git-ignored; Claude never reads it. |
| `.claude/` | Hooks, skills, agents and settings for Claude Code. |

## Architecture decisions so far

<!-- One line per accepted ADR, with the skill that applies it. -->

- **Backend: modular monolith**, one module per business concept (initial list in the
  ADR), ports and adapters only where the provider may change, one API for every client.
  ADR 0001 (accepted); skills `backend-architecture`, `new-module`, `migrations`.
- **One user, roles on relations**: one `users` identity, roles and statuses on each
  relation (contacts, members of each context), invitations as members in `invited`,
  no deletes, history and outbox events for every change, ratings per scope and position
  (outfield, goalkeeper), claimable guests. ADR 0002 (accepted); skill
  `backend-architecture`.
- **Client API: GraphQL without versions**: one `/graphql` (Strawberry), additive
  changes and deprecations only, generated `schema.graphql` with a breaking-change check,
  persisted operations per app build, minimum version gate. ADR 0003 (accepted); skills
  `backend-architecture`, `new-module`.
- **Three native clients, one repository per project**: Android (Kotlin, Compose), iOS
  (Swift, SwiftUI), web (Next.js); Apollo in the three; thin clients; schema and design
  tokens generated into each client; the workspace root is the documents repository;
  delivery by epic with versions `v0.E.T`, ticket tests per ticket, full suite and
  architecture review in each epic's closing ticket, notes per ticket and one
  explication per epic. ADR 0004 (accepted); skills `app-architecture`, `theming`, `reuse-components`.
- **Social login and sessions**: providers behind an `IdentityProvider` port (Google in
  production and staging, Apple with iOS, GitHub and a development login in local),
  one user with many identities linked by verified email, backend tokens (15-minute
  access, rotating refresh, 90 days sliding, one independent session per device), web
  session in `HttpOnly` cookies through Next.js. ADR 0005 (accepted); skills
  `backend-architecture`, `app-architecture`.
- **Events, live updates and push**: outbox events (plain JSON) delivered through an
  `EventBus` port with one queue per consumer (PostgreSQL adapter first, replaceable by
  SNS/SQS or RabbitMQ), idempotent consumers in a worker process, notification inbox as
  source of truth, GraphQL subscriptions over WebSocket, push through a `PushSender`
  port with FCM (Android, and iOS through APNs). ADR 0006 (accepted); skill
  `backend-architecture`.
- **Backoffice**: one operator from the backend `.env` (secret path, user, password),
  not a user; separate admin GraphQL schema; actions through the same services with an
  `Actor`, so history and events happen as for users; declared settings in `app_config`
  (no secrets); fixed theme; every feature adds its backoffice section. ADR 0007
  (accepted); skills `backend-architecture`, `new-module`, `app-architecture`.
- **Dynamic themes**: one token tree by component (W3C format) in `design-tokens/`,
  white and dark bundled in the apps following the system setting, decoration slots
  empty in both, seasonal themes as overrides edited in the backoffice (contrast check,
  preview, testers first, dates) and applied at run time, unknown tokens ignored,
  bundled fonts only. ADR 0008 (accepted); skill `theming`.

- **Images**: an `images` module with an `ObjectStorage` port, the server disk first
  and an S3-compatible bucket by configuration later; tables store keys, never URLs;
  signed direct uploads; the worker strips EXIF and generates fixed WebP variants;
  served by a static file server with immutable caching; provider pictures copied.
  ADR 0009 (accepted); skill `backend-architecture`.

**Done for a UI ticket** = it works on Android, iOS and web, in white and in dark (six
checks), with screenshot tests per theme. ADR 0008 section 7.

## Store identity (never change)

The app keeps the identity of the existing Play Store listing, so no new app (and no new
14-day closed test) is needed:

- `applicationId` / package name: `com.sebastianartaza.fulbito`;
- the **upload key** (keystore in `secrets/`, git-ignored);
- every release has a `versionCode` above the last published one (last published: `7`, versionName `1.0.1`; versionCode 6 was named `1.0.2`, so the
  new app starts at versionName `1.1.0` or above);
- iOS bundle id: `com.sebastianartaza.fulbito` (the same as the Android package).

Never write passwords or key material in tracked files, logs, tests or the transcript.

## Non-negotiable rules

1. **Git**: commit or push **only after the user explicitly confirms**, every time. A hook
   asks too. Commit messages in English. Each finished ticket (requirement, bug or
   direct change) is tagged `v0.E.T` by the user in the four code repositories
   (backend, android, ios, web), even those it did not touch: E is the epic's delivery
   order (`version` in the epic file), T the ticket's order inside the epic (`tag` in
   the ticket file). ADR 0004 section 6. Only
   the code repositories are mentioned in commit suggestions; the documents repository
   (requirements, ADRs, explications) is the user's call.
2. **TDD at the user's pace** (`scripts/tdd.py`, skill `testing`). The user wants to
   understand every step, so Claude never builds ahead of what was approved:
   - `tdd.py start <task>`, then write **only tests**, in one new test file; they must
     fail (red). Source code is locked.
   - Show the user the tests and that they fail, **end the turn**, and run `tdd.py green`
     only after an explicit OK. A clarification is not an OK.
   - Implement; if tests fail, change or add implementation, **never the approved
     tests** without the user's permission for that specific test.
   - When tests pass, the task stays open while the user tests by hand; `tdd.py done`
     when the user says it is finished. Never write code just to make a test pass.
   - **Direct changes** (scaffolding, a change the user asked for explicitly, lab
     mode) open with `tdd.py start <task> --direct`: the user approves once, then
     source and tests are free until `tdd.py done`. Claude works through the whole
     change and reports it once at the end, never in pieces. Never edit source or tests
     with no task open: that asks the user for every file.
3. **Generated files are generated**: migrations with `alembic revision --autogenerate`
   inside the backend container (skill `migrations`); `schema.graphql` with `strawberry
   export-schema` (and the admin schema); `uv.lock` with `uv add`/`uv remove`; any other entry of `generated`
   in `workflow.json`. Hooks deny hand-writing them; the schema and the lock file cannot
   be edited at all.
4. **Comments**: none inside function bodies. Docstrings and doc blocks above functions.
   Only exception: a regex, with an `"input" -> output` example comment. Skill
   `comment-style`.
5. **Diagrams**: Mermaid only in Markdown, never ASCII art. Never put `;` inside a
   Mermaid label.
6. **Edit source files with Write/Edit, not with shell commands**, so the PostToolUse hook
   formats and checks them.
7. `docker compose down -v`, dropping databases or deleting volumes: ask first (the test
   database is the exception).
8. **Ticket tests per ticket, full suite and architecture review per epic**: a ticket
   runs only its new tests (and the checks). When they pass, say "listo para probar" and
   do not suggest a commit; when the user says the ticket is finished, close it and give
   the commit summary. The full suite of every project and the `architecture-reviewer`
   run **once per epic**, in its closing ticket (skill `close-epic`): failing older
   tests are fixed as regressions, findings as refactors. A doubtful design decision is
   raised right away, not left for the review. An architecture-contract failure is fixed
   by moving code, never by adding an ignore without asking.
9. **Bugs get the smallest fix** (`bugs/README.md`): only what makes the report work
   again; extras are written as possible requirements.
10. **Documents say what is used.** ADRs, requirements and epics name the chosen design;
    discarded options appear only by kind, never "no X for now".

## Working modes

- **Lab mode** ("modo laboratorio"): the process is suspended to try something by hand
  (a provider, a library, a native API). A direct change (`tdd.py start lab-<topic>
  --direct`), no requirement, tests or review;
  failing checks are reported in one line, not fixed. When it works, the user reverts the
  lab code and the requirement is written from what was learned. No backups of lab code.

## Reporting

- File counts always read "X de backend, Y de android, Z de ios, W de web y N de tests"
  (tests counted apart; projects without changes are left out),
  in summaries and in the scope line of explications.

## Commands

<!-- Filled when the stacks are set up. -->

```bash
python3 scripts/tdd.py status
python3 scripts/run_locked.py -- <test_command of "workspace" in workflow.json>
```

Tests and database commands (pytest, alembic except `alembic revision`, each project's
`test_command`) always run through `scripts/run_locked.py -- <command>`, from the folder
the command needs (it runs in the current folder; from `backend/`:
`python3 ../scripts/run_locked.py -- .venv/bin/pytest -q`). One global lock, so two
sessions or subagents never use the test database at once; a second caller waits (up to
`WORKFLOW_LOCK_TIMEOUT`, 100 s by default, 300 s in the Stop hook) and is told who holds
it.

## Hooks (`.claude/settings.json`)

| Event | Script | Effect |
|---|---|---|
| PreToolUse Write/Edit | `guard_edit.py` | Deny hand-written generated files, ask before editing one; reuse guard (`reuse_guard` in `workflow.json`); TDD phases (red: source denied; green: tests ask; direct: both free; no task: both ask); `workflow.json` and `.claude/settings*.json` always ask |
| PreToolUse Bash | `guard_bash.py` | Ask before `git commit`/`git push` and `tdd.py green`/`abort`/`start --direct`; deny shell writes to generated folders and to the TDD state; TDD phases for shell commands that write files; deny tests and database commands not run through `run_locked.py` |
| PostToolUse Write/Edit | `post_edit.py` | The project's `on_edit` format and lint commands; comment, language and Mermaid checks; explications must cover their tag's git scope |
| Stop | `stop_checks.py` | `checks` of the touched projects and, under the test lock, the current ticket's own tests (every suite in an epic's closing ticket, the touched suites outside a task); test-failure policy of the TDD phase |

## Skills and agents

Skills: `new-requirement`, `implement-requirement`, `fix-bug`, `close-epic`, `new-adr`,
`testing`,
`comment-style`, `english-code`, `write-explication`, `backend-architecture`,
`new-module`, `migrations`, `app-architecture`, `theming`, `reuse-components`.

Agents: `architecture-reviewer` (read-only review of an epic's whole diff, in its
closing ticket).
