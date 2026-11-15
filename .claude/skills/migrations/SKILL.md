---
name: migrations
description: How database migrations are created. Load ALWAYS when creating or changing a model or touching anything in backend/alembic/. Migrations are generated with `alembic revision --autogenerate`, never written by hand.
---

# Migrations: Alembic writes them, not Claude

## The rule

**A migration file is never written by hand.** Writing into `backend/alembic/versions/`
is denied by the hooks (`generated` in `workflow.json`), from Write/Edit and from the
shell. Editing a generated file asks the user first.

## The chain

Alembic reads the database URL from the settings, so it runs inside the backend
container (the source is bind-mounted, so the generated file lands in the repo). From
`backend/`:

```bash
docker compose up -d
docker compose exec backend alembic revision --autogenerate -m "add_match_table"
python3 ../scripts/run_locked.py -- docker compose exec backend alembic upgrade head
python3 ../scripts/run_locked.py -- docker compose exec backend alembic check
```

Every alembic command except `revision` runs under the workspace test lock
(`scripts/run_locked.py`, skill `testing`); the shell guard denies it otherwise.

Read the generated file entirely between generating and upgrading.

## Reviewing the generated file

| Change | What autogenerate does | What to do |
|---|---|---|
| Rename a column or table | drop + add (data loss) | Stop. Tell the user; propose `op.alter_column(new_column_name=...)` and ask before editing |
| New `CheckConstraint` | nothing | Tell the user and ask before editing |
| Data backfill or seed | nothing | Tell the user and ask before editing |
| `NOT NULL` column on a table with rows | fails on upgrade | Prefer `server_default` in the model and regenerate |

If the file is wrong because the model is wrong: fix the model, delete the file (the
hook asks the user), and generate again. Never "fix" a migration to hide a model mistake.

## Starting over (development only)

`docker compose down -v` deletes the database volume: ask the user before running it.
A test database created from the models (`create_all`) must be dropped after adding
columns; that is allowed, it is test data only.
