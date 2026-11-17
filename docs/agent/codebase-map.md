# Codebase map (for Claude)

Where things are, so a task starts without exploring. Read the section you need, not the
whole file. Rules and workflow live in `CLAUDE.md`; this file only says where.

**Keep it true**: when a requirement adds, moves or renames something listed here,
update the line when the work is finished (skill `implement-requirement`). Snapshot:
after 0009 (v0.1.9).

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
| Publish an event (`Event`, `publish`) in the caller's transaction | `events/__init__.py`, `events/schemas.py` |
| Declare a consumer (`Consumer`) | `events/consumers.py`; the module's own `consumers.py` |
| Consumers the worker runs (add a module's consumers here) | `consumers.py` |
| `EventBus` port | `events/ports.py` |
| Relay, deliveries, backoff, dead letters | `events/adapters/postgres.py`, queries in `events/repository.py` |
| Outbox and delivery tables | `events/models.py` |
| Worker process (`python -m app.events.worker`) | `events/worker.py` |
| Declared settings, cache, `is_version_allowed` | `modules/app_config/service.py` |
| Settings table `app_settings` | `modules/app_config/models.py` |

Outside `app/`: `alembic/` (async `env.py`, migrations in `versions/`), `schema.graphql`
(exported), `pyproject.toml` (dependencies, tool settings, import-linter contracts),
`docker-compose.yml` (every environment), `compose.override.yml` (local, loaded by
itself), `compose.staging.yml` (the server), `tools/deploy.sh` (staging deploy),
`Dockerfile`, `.env.example`, `.github/workflows/`.

## Shared contracts (workspace root)

| Need | Path |
|---|---|
| Design tokens: palette, roles, component tokens, white and dark | `design-tokens/base.json` |
| Validate tokens, copy the schema and generate client files (`--check`: the workspace check `contracts`) | `scripts/sync_contracts.py` |
| Generated web tokens and schema (never edited) | `web/src/generated/tokens.css`, `tokens.ts`, `schema.graphql` |
| Generated Android tokens and schema (never edited) | `android/app/src/main/java/com/sebastianartaza/fulbito/ui/theme/generated/Tokens.kt`, `android/app/src/main/graphql/schema.graphql` |
| Generated iOS tokens and schema (never edited) | `ios/Packages/UI/Theme/Generated/Tokens.swift`, `ios/graphql/schema.graphql` |

## App

| Need | Path |
|---|---|
| Web routes (App Router), root layout with the generated tokens, bundled Inter font | `web/src/app/`, `web/public/fonts/` |
| Web shell: sections, navigation and connection check (add a section here) | `web/src/app/(shell)/sections.tsx`, `layout.tsx` |
| Backend for frontend: `/api/graphql` adds the client headers | `web/src/app/api/graphql/route.ts` |
| Apollo client and the `UPGRADE_REQUIRED` link | `web/src/core/apollo/` |
| Generic web components (`Button`, `Message`, `ComingSoon`, `Navigation`, `BellIcon`) | `web/src/ui/` |
| Connection check (`ConnectionGate`, `Health` query); update screen | `web/src/features/health/`, `web/src/features/app_config/` |
| ESLint local rules (comments in function bodies, literal design values) and boundaries; Stylelint (no literal values or primitive tokens in CSS) | `web/tools/eslint-plugin-local.mjs`, `web/eslint.config.mjs`, `web/stylelint.config.mjs` |
| Web features, generic UI, core (Apollo, auth, preferences) | `web/src/features/`, `web/src/ui/`, `web/src/core/` |
| Web GraphQL types (`pnpm codegen`, never edited) | `web/src/generated/graphql/`, config `web/codegen.ts` |
| Android entry: `MainActivity` (version gate, then the shell), `AppShell` (bell on top, five sections at the bottom, connection error; add a section here) | `android/app/src/main/java/com/sebastianartaza/fulbito/MainActivity.kt`, `AppShell.kt` |
| Android Apollo client (headers, `UPGRADE_REQUIRED` interceptor), `VersionGate`, Hilt module | `android/app/src/main/java/com/sebastianartaza/fulbito/core/network/` |
| Android theme: `AppTheme` and `AppTheme.tokens`, Inter as a variable font | `android/app/src/main/java/com/sebastianartaza/fulbito/ui/theme/AppTheme.kt`, `android/app/src/main/res/font/inter.ttf` |
| Generic Android components (`Button`, `Message`, `ComingSoon`, `Navigation`) | `android/app/src/main/java/com/sebastianartaza/fulbito/ui/` |
| Android connection check (`ConnectionViewModel`, `HealthRepository` and its Apollo implementation), update screen, sign-in; each feature's public entry is its `<Feature>Navigation.kt` (`HealthNavigation.kt`, `AppConfigNavigation.kt`) | `android/app/src/main/java/com/sebastianartaza/fulbito/features/health/`, `features/appconfig/`, `features/accounts/` |
| Android GraphQL operations (one folder per feature; Apollo generates the types into `build/`) | `android/app/src/main/graphql/features/` |
| Android detekt rules `local` (`NoFunctionBodyComments`, `NoLiteralDesignValues`) and their config | `android/detekt-rules/`, `android/config/detekt/detekt.yml` |
| Android tests: Robolectric, Roborazzi references, Konsist rules and fixtures (tests run on JDK 21, downloaded by Gradle) | `android/app/src/test/java/`, `src/test/screenshots/`, `src/test/resources/architecture/` |
| iOS entry: `MainApp` (configuration, Apollo client, `BACKEND_STUB` for UI tests), `RootView` (version gate, then the shell), `AppShell` (bell in a top `Navigation` bar, five sections at the bottom; add a section here) | `ios/App/` |
| iOS Apollo client (headers, `UPGRADE_REQUIRED` interceptor), `VersionGate`, `AppConfiguration` (`Info.plist` values) | `ios/Packages/Core/` |
| iOS theme: `AppTheme`, `@Environment(\.tokens)`, Inter | `ios/Packages/UI/Theme/AppTheme.swift`, `ios/Packages/UI/Resources/Inter.ttf` |
| Generic iOS components (`Button`, `Message`, `ComingSoon`, `Navigation`) | `ios/Packages/UI/` |
| iOS connection check (`ConnectionViewModel`, `HealthRepository`, Apollo implementation), update screen, sign-in | `ios/Packages/FeaturesHealth/`, `FeaturesAppConfig/`, `FeaturesAccounts/` |
| iOS GraphQL operations (one `Operations/` folder per feature) and Apollo's generated types (`./apollo-ios-cli generate` from `ios/Packages/`, never edited) | `ios/Packages/Features*/Operations/`, `ios/Packages/API/Generated/`, config `ios/Packages/apollo-codegen-config.json` |
| iOS lint rules (`no-function-body-comments`, `no-literal-design-values`) and the `lint-rules` command | `ios/LintRules/` |
| iOS tests: Swift Testing and snapshot references, LintRules tests (with the package boundaries), XCUITests | `ios/Packages/Tests/SkeletonTests/`, `ios/LintRules/Tests/`, `ios/UITests/` |
| Web tests: Vitest in `tests/`, Playwright screenshots (white and dark) in `e2e/`; `pnpm test [files]` runs each file with its runner | `web/tests/`, `web/e2e/`, `web/tools/run-tests.mjs` |

## Test helpers

| Need | Path |
|---|---|
| Test database (migrated once, emptied per test): `sessionmaker` fixture | `backend/tests/conftest.py` |
| `EventBus` fake for consumer tests | `backend/tests/fakes/event_bus.py` |

## Ops facts

| Fact | Where |
|---|---|
| Local stack: `migrate` (one-shot `alembic upgrade head`, before `backend` and `worker`), `backend`, `worker`, `db`, `db-test` (compose project `fulbito`); the worker has no reload: `docker compose restart worker` after a change | `backend/docker-compose.yml`, `backend/compose.override.yml` |
| Backend host and its Traefik router | `BACKEND_HOST` in `backend/.env`, labels in the compose file |
| Local TLS for the project's hosts | `~/trabajo/traefik/dynamic/fulbito.yml` and `certs/fulbito*.pem` |
| Test database on the host | `127.0.0.1:TEST_DB_PORT`, `TEST_DATABASE_URL` in `backend/.env` |
| CI | `backend/.github/workflows/checks.yml` (push), `tests.yml` (manual dispatch) |
| Local web: `docker compose up -d` in `web/` (project `fulbito-web`), Next.js dev server behind Traefik on `WEB_HOST`; the container reaches the backend host through `extra_hosts` and trusts the mkcert CA (`MKCERT_CA_DIR`) | `web/docker-compose.yml`, `web/.env` |
| Staging: the developer's Hetzner server, shared Traefik (network `traefik`, resolver `letsencrypt`), `APP_ENV=staging` and `COMPOSE_FILE=docker-compose.yml:compose.staging.yml` in the server's `backend/.env`; deployed with `./tools/deploy.sh <ref>` on the server. The mobile apps and the web on Vercel use it | `backend/compose.staging.yml`, `backend/tools/deploy.sh` |
| Android build: identity, `backend.url` from `local.properties`, release signing from `secrets/key.properties` (fails naming what is missing), compileSdk 37.2 | `android/app/build.gradle.kts`, `android/local.properties` |
| Android tests: `./tools/run-tests.sh [files]` maps each file to its Gradle task | `android/tools/run-tests.sh` |
| Android CI | `android/.github/workflows/checks.yml` (push: detekt, Lint, debug build), `tests.yml` (manual dispatch) |
| iOS project: `ios/project.yml` (XcodeGen; `xcodegen generate` writes the git-ignored `App.xcodeproj`), bundle id, version and build number; `BACKEND_URL` and `APP_STORE_URL` from `Config/Local.xcconfig` (git-ignored) | `ios/project.yml`, `ios/Config/` |
| iOS tests: `./tools/run-tests.sh [files]` picks xcodebuild or swift test per folder, on the iPhone 17 Simulator with iOS 27.2 | `ios/tools/run-tests.sh` |
| iOS CI (both by manual dispatch while the repository is private) | `ios/.github/workflows/checks.yml` (SwiftLint, lint rules, build), `tests.yml` |
| Web CI | `web/.github/workflows/checks.yml` (push: codegen fresh, ESLint, TypeScript), `tests.yml` (manual dispatch) |
