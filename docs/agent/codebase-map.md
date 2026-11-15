# Codebase map (for Claude)

Where things are, so a task starts without exploring. Read the section you need, not the
whole file. Rules and workflow live in `CLAUDE.md`; this file only says where.

**Keep it true**: when a requirement adds, moves or renames something listed here,
update the line when the work is finished (skill `implement-requirement`). Snapshot:
after 0001 (v0.1.1).

## Backend (`backend/app/`)

| Need | Path |
|---|---|
| Application factory (routers, lifespan, `app.state.settings` and `sessionmaker`) | `main.py` |
| Environment settings (`APP_ENV`, `DATABASE_URL`, `GRAPHQL_MAX_DEPTH`) | `core/config.py` |
| GraphQL error codes (`extensions.code`) | `core/errors.py` |
| Declarative base | `db/base.py` |
| Engine, session factory, one transaction per request (`get_session`, `RequestSession`) | `db/session.py` |
| Every module's models for Alembic | `models/__init__.py` |
| Client schema assembly (add a module's `Query` here) | `api/schema.py` |
| `/graphql` and REST routers mounted | `api/router.py` |
| Client headers and version gate (context builder) | `api/context.py` |
| Rejection as a GraphQL error (`on_operation`) | `api/gate.py` |
| Query depth limit | `api/depth.py` |
| Schema up to date and breaking-change check | `api/breaking_changes.py` |
| `GET /health` and the `health` query | `modules/health/` |
| Declared settings, cache, `is_version_allowed` | `modules/app_config/service.py` |
| Settings table `app_settings` | `modules/app_config/models.py` |

Outside `app/`: `alembic/` (async `env.py`, migrations in `versions/`), `schema.graphql`
(exported), `pyproject.toml` (dependencies, tool settings, import-linter contracts),
`docker-compose.yml`, `Dockerfile`, `.env.example`, `.github/workflows/`.

## App

| Need | Path |
|---|---|

## Test helpers

| Need | Path |
|---|---|

## Ops facts

| Fact | Where |
|---|---|
| Local stack: `backend`, `db`, `db-test` (compose project `fulbito`) | `backend/docker-compose.yml` |
| Backend host and its Traefik router | `BACKEND_HOST` in `backend/.env`, labels in the compose file |
| Local TLS for the project's hosts | `~/trabajo/traefik/dynamic/fulbito.yml` and `certs/fulbito*.pem` |
| Test database on the host | `127.0.0.1:TEST_DB_PORT`, `TEST_DATABASE_URL` in `backend/.env` |
| CI | `backend/.github/workflows/checks.yml` (push), `tests.yml` (manual dispatch) |
