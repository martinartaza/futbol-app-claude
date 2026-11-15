---
name: new-module
description: Create a new backend module in backend/app/modules/<name>/ with the standard shape (api, router, service, repository, models, schemas, dependencies, and ports/adapters only when needed). Use when an approved requirement introduces a business concept that no existing module owns.
argument-hint: "[module name in English, snake_case, e.g. matches]"
---

# New backend module

Module: `$ARGUMENTS`

Existing modules:

!`ls -1 backend/app/modules/ 2>/dev/null | grep -v '^__' || echo "(none yet)"`

Load the `backend-architecture` skill first.

## Before creating it

1. **Is it really new?** If an existing module owns the concept, extend that one. Name
   modules after business concepts (`matches`, `teams`), never after screens
   (`home_screen`).
2. **Name**: English, plural when it holds a collection, snake_case. Check the glossary
   (skill `english-code`).
3. **Ports**: only if the module talks to something outside our code whose provider may
   change. If yes, the requirement says why.

## Steps

1. Create only the files the requirement needs, from: `__init__.py` (docstring),
   `schemas.py`, `models.py`, `repository.py`, `service.py`, `dependencies.py`,
   `api.py` (GraphQL types, queries, mutations, DataLoaders), `router.py` (only REST
   that is not a client query), `admin_api.py` (backoffice queries and mutations, ADR 0007), `ports.py`, `adapters/`, `jobs.py`.
2. Models: import the module in `app/models/__init__.py`, then generate the migration
   (skill `migrations`). Table names: plural snake_case.
3. GraphQL: register the module's types, queries and mutations in
   `app/api/schema.py`, then re-export the schema (`strawberry export-schema`, never by
   hand) and run the breaking-change check (ADR 0003).
   REST routes, when needed: `APIRouter(prefix="/<module>", tags=["<module>"])`, included by
   `app/api/router.py`.
   Backoffice: register `admin_api.py` in `app/api/admin_schema.py` and re-export the
   admin schema. Every feature ships its backoffice section in the same ticket.
4. Add the module to the import-linter contracts in `backend/pyproject.toml`.
5. Tests in `backend/tests/modules/<module>/` (one new file per ticket):
   - unit tests of the service with fakes (`tests/fakes/`), no database;
   - HTTP tests through the in-memory client;
   - contract tests per adapter, when there are ports.

## Checklist before reporting

- `api.py` and the router have no logic and import no repository, model or adapter.
- Every relation field uses a DataLoader; every growing list is a cursor connection;
  business errors are typed results.
- The service imports no `fastapi` and no adapter.
- No other module imports this module's internals.
- Docstrings on every public function; no comments inside function bodies.
