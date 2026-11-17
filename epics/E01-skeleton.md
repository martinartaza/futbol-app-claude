---
id: E01
title: Skeleton of the four projects
status: done
version: v0.1
origin: Bootstrap session, 2026-11-03
adrs: ["0001", "0003", "0004", "0006"]
requirements: ["0001", "0002", "0003", "0004", "0005", "0006", "0007", "0008", "0009"]
depends_on: []
---

# E01 - Skeleton of the four projects

## What is wanted

The four projects running end to end before any feature: the backend answers, the three
clients open, show every screen of the product as "Próximamente", and the Android build
can replace the published app.

## Why

Every later epic adds a feature to a structure that already builds, tests and deploys;
the architecture contracts are checked by tools from the first line of code.

## What is already decided

- Backend: FastAPI with Strawberry at `/graphql`, an empty schema plus a health query,
  PostgreSQL, Alembic, the outbox tables and the worker process (ADR 0001, 0003, 0006),
  import-linter contracts including `api.py`, the schema export and the breaking-change
  check.
- Clients: Android (Compose), iOS (SwiftUI, on the Simulator) and web (Next.js), each
  in its own repository with its CI, the folder layout of the skill `app-architecture`,
  the comment and token lint rules, and every screen in the "Próximamente" state.
- Shell navigation: Home (next match, E09), Groups (E08), Network (E05), Feed (E10),
  Profile (E04, E06), notifications icon (E07), plus the sign-in and update screens.
- `scripts/sync_contracts.py`: copies the exported GraphQL schema and generates the
  design tokens into each client.
- Every request sends platform and `versionCode`; the minimum version gate and the
  update screen work (ADR 0003 section 5); the minimum is set from the backoffice in
  E02.
- The Android build uses `com.sebastianartaza.fulbito`, the upload key from `secrets/`
  and a `versionCode` above 7 (`CLAUDE.md`, "Store identity").
- `workflow.json` gets the entries of the three clients; `docs/agent/codebase-map.md`
  and `docs/agent/bug-reproduction.md` are filled as the skeleton appears.
- Local stack behind the local Traefik; the backend runs as staging on the developer's
  Hetzner server behind its shared Traefik, deployed by hand with a script, and the
  mobile apps and the web on Vercel use it (requirement 0008). After 0008 a short
  closing ticket runs the full suite and the review on the changes since `v0.1.7`.
- Store bundles are built locally by the developer and uploaded to a test track;
  building and publishing from CI is a row of `docs/production-readiness.md`
  ("Releases").

## Open questions

- None.

## Impact on the architecture

Creates every project; no business module yet beyond what the version gate needs
(`app_config`).
