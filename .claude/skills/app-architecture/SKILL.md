---
name: app-architecture
description: Where client code goes in the three native clients (android/ Kotlin + Compose, ios/ Swift + SwiftUI, web/ Next.js + TypeScript), how they talk to the backend (Apollo, generated types, persisted operations) and who owns which state. Load ALWAYS before creating or moving files in android/, ios/ or web/, adding a screen, a GraphQL operation, a stored value or a dependency.
---

# Client architecture

Decision and reasons: `docs/adr/0004-native-clients-and-repositories.md` (stacks,
repositories) and `docs/adr/0003-client-api-graphql.md` (API). This skill is the
day-to-day rulebook for the three clients; the rules are the same, the folders differ.

## Principles (every platform)

1. **Features mirror backend modules**: `accounts`, `network`, `groups`, `matches`,
   `ratings`, `awards`, `feed`, `comparisons`, `notifications`, `app_config`. A feature
   is never named after a screen.
2. **One public entry per feature** (its navigation entry and the few types other
   features need). Another feature imports only that entry.
3. **Screens and routes are thin**: they compose feature components and call the
   feature's view model or hook. No business logic in a screen.
4. **Generic UI apart from feature UI**: the `ui` layer (buttons, cards, the radar
   chart, the "Próximamente" state) knows no feature and no GraphQL type.
5. **Thin clients**: no business rules (averages, permissions, invitation states,
   limits). The backend decides; the client renders what the API returns.
6. **The backend only through Apollo with generated types**: operations live in the
   feature that uses them, with colocated fragments per component; types and the
   persisted-operations manifest are generated from the synced `schema.graphql`.
   Hand-written copies of backend types are not allowed.
7. **State ownership**: business data is fetched (Apollo cache); local state only for
   the UI; device storage only through the `core` preferences module; tokens only
   through `core` secure storage (Android Keystore, iOS Keychain, web per the login
   ADR).
8. **Session (ADR 0005)**: sign in once; the `core` auth module refreshes the access
   token when it expires (one refresh at a time, rotating the refresh token) and only
   shows the sign-in screen when the backend rejects the refresh. On web, tokens live
   in `HttpOnly` cookies handled by the Next.js server, never in browser storage.
9. **Every request sends platform and `versionCode`**; `UPGRADE_REQUIRED` opens the
   update screen (ADR 0003 section 5).
10. **Unfinished screens say "Próximamente"** instead of pretending.
11. **Boundaries are checked by tools**, never by memory (see each platform).

## Android (`android/`)

```text
android/app/src/main/java/com/sebastianartaza/fulbito/
  MainActivity.kt         entry: theme, navigation host
  core/                   network (Apollo client, headers), auth (Keystore token store),
                          preferences (DataStore), navigation
  ui/                     generic components, theme (generated tokens)
  features/<feature>/     screens, view models, feature components, operations (.graphql)
                          <Feature>Navigation.kt: the public entry
android/app/src/main/graphql/   schema.graphql (generated, synced)
```

- UI layer and data layer of Google's app architecture guide: a screen observes a
  `ViewModel` exposing `StateFlow` UI state; the view model calls the feature's
  repository, which wraps Apollo.
- Dependency injection with Hilt.
- Boundaries: Konsist architecture tests (a feature imports another only through its
  navigation entry; `ui` imports no feature; only `core` touches storage).

## iOS (`ios/`)

```text
ios/App/                  the app target: entry, root navigation
ios/Packages/             one local Swift package with one target per layer:
  Core/                   network (Apollo client, headers), auth (Keychain token store),
                          preferences (UserDefaults wrapper)
  UI/                     generic components, theme (generated tokens)
  Features<Feature>/      views, view models (@Observable), operations (.graphql);
                          its public types are the entry, the rest is internal
  API/                    Apollo generated types (generated)
```

- Views observe `@Observable` view models; view models call the feature's repository,
  which wraps Apollo.
- Boundaries are compiler-checked: each feature target depends only on `Core`, `UI`,
  `API` and the targets it declares; internals are `internal`.

## Web (`web/`)

```text
web/src/app/              Next.js App Router routes: thin, server components by default
web/src/features/<feature>/   components, hooks, operations; index.ts is the public entry
web/src/ui/               generic components, theme (generated CSS tokens)
web/src/core/             Apollo client, auth, preferences
web/src/generated/        graphql-codegen types and tokens (generated)
web/src/app/backoffice/   backoffice routes, reached only through the secret path rewrite
web/src/backoffice/       backoffice screens per module and its own ui/ (fixed theme)
```

- Backoffice (ADR 0007): middleware rewrites `/<BACKOFFICE_PATH>/...` to
  `src/app/backoffice/`, the internal path answers 404; its types come from
  `admin_schema.graphql`; its session cookie is held by the Next.js server.
- Public pages (invite links) are server-rendered with Open Graph metadata and hand over
  to the app through App Links and universal links.
- Boundaries: ESLint import-boundary rules (features through `index.ts` only; `ui`
  imports no feature; `app/` imports features, not their internals).

## Not without an ADR

A state-management library beyond the platform's own, an offline database, a
cross-platform UI layer, code shared between clients other than generated contracts.
