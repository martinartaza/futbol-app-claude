# Bug reproduction (for Claude)

How Claude reproduces a bug in local (skill `fix-bug`, step 2). Written once the app and
the backend run; until then this page only lists what it must answer.

## What this page must answer

| Question | Answer |
|---|---|
| How to start the stack in local | From `backend/`: `docker compose up -d` (`backend`, `db`, `db-test`), then `python3 ../scripts/run_locked.py -- docker compose exec backend alembic upgrade head`. The backend answers at `https://$BACKEND_HOST` (value in `backend/.env`) through the shared local Traefik; GraphiQL at `/graphql` in `local`. Logs: `docker compose logs backend` |
| How to get a test account without a real social login | The development login of ADR 0005 section 6 (local only, seeded test users) |
| Where the credentials for that live (git-ignored file, read at run time) | ... |
| How to reach a state fast (seed data, API calls, database updates) | `curl` to `https://$BACKEND_HOST/graphql` with `X-Client-Platform` and `X-Client-Version`; settings through `AppConfigService.set` in `docker compose exec -T backend python -`; database through `docker compose exec db psql` under `run_locked.py`. After a code change, `--reload` restarts the worker, but Traefik may keep a keep-alive connection to the previous one for a few requests |
| Web: browser automation and where screenshots go (git-ignored) | ... |
| Android / iOS: emulator or simulator, how to install the dev build, how to drive it | ... |
| What never goes into tracked files, logs or the transcript | tokens, refresh tokens, emails, personal data |
