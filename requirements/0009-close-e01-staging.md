---
id: "0009"
title: Close E01 after the staging backend
status: done
kind: epic-close
projects: [workspace, backend, web, android, ios]
created: 2026-11-17
approved: 2026-11-17
done: 2026-11-17
depends_on: ["0007", "0008"]
epic: E01
tag: v0.1.9
---

# 0009 - Close E01 after the staging backend

## Goal

Close E01: full suite of every project and architecture review of what changed after
the first closing ticket (0007, `v0.1.7`), that is requirement 0008.

## Scope

**In scope**

- The full suite of every project (`python3 scripts/tdd.py suite`).
- One run of the `architecture-reviewer` on the diff `v0.1.7..v0.1.8` of the four code
  repositories and on the documents 0008 changed. The rest of E01 was reviewed in 0007.
- The checks of earlier tickets still open on the user's side: 0004 AC-9 (web CI),
  0005 AC-8 (bundle on a Play internal track), 0005 AC-10 (Android CI), 0008 AC-6 (web
  on Vercel against staging).

**Out of scope**

- New behaviour: a finding that needs it becomes a possible requirement of a later
  epic.

## Findings

The full suite of every project passes (backend 42, workspace 74, web Vitest and 14
Playwright, android, ios): no regression. Every row comes from the reviewer.

| Id | Kind | Source | What fails or what is wrong | Proposed fix |
|---|---|---|---|---|
| F-1 | refactor | `requirements/0008-backend-staging.md`, implementation notes | The staging host is written as a fixed value; `CLAUDE.md` keeps host names out of documents | "the staging host (`BACKEND_HOST` in the server's `.env`)" |
| F-2 | refactor | `docs/production-readiness.md`, "Releases" | 0008 points the backend deploy from CI to "Releases", but the row covers only store builds | Add the backend deploy from CI, "until then `tools/deploy.sh` by hand (requirement 0008)", and the backend repository to its hook |
| F-3 | refactor | `docs/adr/0004-native-clients-and-repositories.md` section 7 | "Local development" describes the whole stack in local; the environments (apps against staging, compose per environment, migrate on start, deploy script) live only in a requirement | Edit section 7 in place; Docker's "multiple Compose files" and The Twelve-Factor App in its References and in `docs/prior-art.md` |
| F-4 | refactor | `docs/agent/bug-reproduction.md`, "reach a state fast" | Says `--reload` restarts the worker; only the backend reloads | "`--reload` restarts the backend (the worker needs `docker compose restart worker`)" |
| F-5 | refactor | `backend/tools/deploy.sh:17` | `BACKEND_HOST` read with `sed` keeps quotes, spaces or `\r` that Compose strips, so the health check can ask the wrong name | Strip quotes, surrounding spaces and `\r` from the value |
| F-6 | refactor | `requirements/0005-android-skeleton.md` (behaviour, configuration, diagram), `requirements/0006-ios-skeleton.md` (configuration) | Other ngrok passages of the done requirements carry no "replaced in 0008" mark | Mark them "(replaced in 0008)" |

## Open questions

- None.

## Implementation checklist

- [x] Full suite of every project green
- [x] Architecture review run once, findings approved
- [x] Findings fixed (regressions with the smallest fix, review findings as refactors)
- [ ] Checks of earlier tickets verified by the user
- [x] Epic `done`, `epics/README.md` and `docs/agent/codebase-map.md` updated
- [x] Ticket notes `explications/tickets/E01-T9-close.md`

## Implementation notes

- Findings approved on 2026-11-17, all six fixed here:
  - F-1: the 0008 notes name the staging host by its variable.
  - F-2: the "Releases" row of `docs/production-readiness.md` adds the backend deploy
    from CI, with `tools/deploy.sh` by hand until then.
  - F-3: ADR 0004 section 7 is now "Environments: local and staging" (compose per
    environment, migrate on start, deploy script), edited in place; Docker's multiple
    Compose files and The Twelve-Factor App added to its References and to
    `docs/prior-art.md`.
  - F-4: `docs/agent/bug-reproduction.md` says only the backend reloads.
  - F-5: `backend/tools/deploy.sh` drops quotes, spaces and `\r` around `BACKEND_HOST`,
    as Compose does.
  - F-6: the remaining ngrok passages of 0005 and 0006 are marked as replaced or
    removed in 0008.
- No test changed.
