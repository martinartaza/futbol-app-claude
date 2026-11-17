# Prior art

The established patterns, standards and practices this project follows, so each one can
be recognised by its name and looked up. Each entry says what it is, where we use it and
its main reference. References are given from memory and may be approximate (titles,
years); they point to where to start reading, not to an exact page.

A new entry is added when an ADR, a requirement or a design answer adopts something
beyond the basics.

## Architecture

**Architecture Decision Records (ADR).** Short documents that record one decision, its
context and its consequences, numbered and never rewritten (a new one supersedes).
Used: `docs/adr/`. Reference: Michael Nygard, "Documenting Architecture Decisions"
(blog post, 2011).

**Modular monolith.** One deployable application split into modules with enforced
boundaries, instead of microservices. Used: ADR 0001. Reference: Shopify Engineering,
"Deconstructing the Monolith" (around 2019); Simon Brown's talks on modular monoliths.

**Bounded context.** Each business concept has one owner and its own model; other parts
talk to it through its interface. Used: one backend module per concept, ADR 0001.
Reference: Eric Evans, *Domain-Driven Design* (2003).

**Ports and adapters (hexagonal architecture).** The core defines interfaces (ports);
each external provider is an adapter that implements one. Used: login providers, push,
events, live channel, storage (ADR 0001, 0005, 0006). Reference: Alistair Cockburn,
"Hexagonal Architecture" (around 2005).

**Dependency injection.** Objects receive their collaborators instead of creating them,
so a fake can replace a real adapter in tests. Used: FastAPI `Depends` in
`dependencies.py`, Hilt on Android. Reference: Martin Fowler, "Inversion of Control
Containers and the Dependency Injection pattern" (2004).

**Backend for frontend (BFF).** A server layer owned by one client that talks to the
backend on its behalf. Used: Next.js holds the web session and the backoffice session
(ADR 0005, 0007). Reference: Sam Newman, "Backends For Frontends" (blog post, around
2015); the IETF draft "OAuth 2.0 for Browser-Based Applications".

## Data and domain

**Normalisation.** Each fact is stored once, in the table that owns it; no duplicated
identities. Used: one `users` table (ADR 0002). Reference: E. F. Codd, the relational
model and normal forms (1970s).

**Party and Party Role.** One entity for a person; the roles they play are separate
relations, not types of person. Used: roles on relations (ADR 0002 sections 1 and 2).
Reference: Martin Fowler, *Analysis Patterns* (1996); Len Silverston, *The Data Model
Resource Book*.

**Polymorphic associations (antipattern).** A "type + id" pair that may point to any
table, so the database cannot enforce the foreign key. Avoided in ADR 0002 section 3.
Reference: Bill Karwin, *SQL Antipatterns* (2010).

**State machine on a relation.** A relation has a status with allowed transitions
(invited, active, left...) instead of separate entities for each stage. Used: members
and invitations (ADR 0002 section 4). Reference: general practice; GitHub's API models
memberships with a `pending` / `active` state.

**Audit log.** Every change appends a row saying who changed what, when, from which value
to which. Used: `<context>_member_changes` (ADR 0002 section 6). Reference: Martin
Fowler's temporal patterns (Audit Log, Temporal Property), early 2000s.

**Multi-criteria and context-aware ratings.** A rating has several dimensions (skills)
and depends on a context (the group). Used: the radar (ADR 0002 section 9). Reference:
G. Adomavicius and A. Tuzhilin, work on context-aware recommender systems (around 2011).

**Bayesian average.** An average pulled towards a base value while there are few votes,
so one vote does not jump to the extreme. Used: radar averages (ADR 0002 section 9).
Reference: IMDb's weighted rating formula; any text on Bayesian estimation.

**Placeholder profile claimed later.** Someone is added by name before having an
account and inherits that record when signing up. Used: group guests (ADR 0002 section
9). Reference: no formal name; a product practice of shared-expense and team apps.

## Authorisation and login

**Role-based access control (RBAC) with scopes.** Permissions come from roles, and a
role is assigned within a scope (a group). Used: ADR 0002 section 2. Reference: the
NIST RBAC model (Sandhu, Ferraiolo and others, around 2000).

**Relationship-based access control (ReBAC).** Permissions derive from relations
("user U is admin of group G"). Used: permission questions in each module's service
(ADR 0002 section 8). Reference: Google, "Zanzibar: Google's Consistent, Global
Authorization System" (2019).

**Refresh token rotation with reuse detection.** Each refresh returns a new token and
invalidates the old one; reusing an old one revokes the session. Used: ADR 0005
section 4. Reference: OAuth 2.0 Security Best Current Practice (IETF, published as
RFC 9700).

## Events

**Transactional outbox.** The event is written in the same transaction as the change and
published afterwards, so it exists if and only if the change was committed. Used: ADR
0002 section 10, ADR 0006. Reference: Chris Richardson, microservices.io, "Pattern:
Transactional outbox".

**Idempotent consumer.** A consumer records the messages it processed, so a repeated
delivery has no effect. Used: ADR 0006 section 4. Reference: Chris Richardson,
microservices.io; Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns*
(2003).

**Publish-subscribe with fan-out to one queue per consumer.** One topic, a durable queue
for each consumer, retries and dead letters. Used: ADR 0006 section 3. Reference:
*Enterprise Integration Patterns* (publish-subscribe channel, dead letter channel);
AWS's SNS-to-SQS fan-out pattern.

**Valet Key.** The server hands out a short-lived, limited permission (a signed URL) so
the client talks to storage directly. Used: image uploads (ADR 0009 section 3).
Reference: Microsoft, *Cloud Design Patterns*, "Valet Key" (around 2014); AWS S3
presigned URLs.

**Store keys, build URLs.** Rows keep the storage key; the URL comes from configuration,
so storage can move without touching data. Used: ADR 0009 section 2. Reference: no
formal name; how Rails Active Storage and Django `FileField` work.

**Immutable assets with long caching.** A file that never changes gets a unique name and
is cached for a year. Used: image variants (ADR 0009 section 6). Reference: RFC 8246,
HTTP immutable responses; cache busting by content-addressed names.

## Client API

**Versionless schema evolution.** The API only grows; fields are deprecated, never
removed while in use. Used: ADR 0003 section 2. Reference: graphql.org best practices
("Versioning").

**Persisted queries.** Clients send the id of an operation registered at build time
instead of the query text. Used: ADR 0003 section 4. Reference: Apollo's documentation
on persisted queries; Marc-André Giroux, *Production Ready GraphQL* (2020).

**DataLoader.** Batches and caches the loads of one request to avoid N+1 queries. Used:
ADR 0003 section 7. Reference: Facebook's `dataloader` library (2015).

**Cursor connections.** Pagination with opaque cursors and page info. Used: ADR 0003
section 6. Reference: Relay Cursor Connections Specification.

**Errors as data.** Expected business failures are part of the mutation's typed result,
not exceptions. Used: ADR 0003 section 8. Reference: Marc-André Giroux, *Production
Ready GraphQL*.

## Clients and design

**Design tokens.** Named design values (colours, sizes, fonts) defined once and
generated for every platform. Used: ADR 0004 section 5, ADR 0008. Reference: Salesforce
Lightning Design System (origin of the term, around 2014); the W3C Design Tokens
Community Group format; Style Dictionary (Amazon).

**Component tokens organised in tiers.** Primitive values, semantic roles (surface,
on-surface) and per-component tokens (tab label colour), grouped in a tree. Used: ADR
0008. Reference: Material Design 3 tokens; the W3C Design Tokens Community Group
format (groups).

**Screenshot (snapshot) testing.** A test renders a component and compares it with an
approved image. Used: ADR 0008 section 7. Reference: Facebook's iOS snapshot testing
(around 2013), Point-Free's swift-snapshot-testing, Roborazzi, Playwright visual
comparisons.

**Theme as overrides over a base (cascade).** A theme stores only the values it changes;
everything else falls back to the base, so a token added later never breaks an existing
theme. Used: seasonal themes over white and dark (ADR 0008 sections 4 and 5).
Reference: the CSS cascade and custom properties (W3C); Material Design 3 theme
overrides.

**Tolerant reader.** A client ignores data it does not understand and keeps its own
default for data that is missing. Used: unknown theme tokens ignored by old app
versions (ADR 0008 section 5). Reference: Martin Fowler, "TolerantReader" (bliki,
2011); Postel's robustness principle (RFC 761, 1980).

**Decoration slots.** A component declares named places where optional content may be
drawn, empty by default. Used: `avatar.corner-badge`, `home.background-image` (ADR 0008
section 3). Reference: no formal name for themes; akin to slots in UI component models
(Web Components `<slot>`, Vue slots).

**Release toggles and staged rollout.** A change is switched on by configuration, first
for a small audience, then for everyone, within dates. Used: seasonal themes for testers
first (ADR 0008 section 4). Reference: Pete Hodgson, "Feature Toggles (aka Feature
Flags)" (martinfowler.com, 2017).

**Contrast requirements.** Minimum contrast between text and its background. Used: the
theme editor's check (ADR 0008). Reference: W3C Web Content Accessibility Guidelines
(WCAG 2.x), level AA.

**Guide to app architecture (UI layer, data layer).** Screens observe a view model's
state; view models call repositories. Used: skill `app-architecture` (Android, and the
same shape on iOS). Reference: Google, "Guide to app architecture" for Android.

**Project file generated from a specification.** The Xcode project is described in a
short YAML file and generated, so it is never edited by hand nor merged in git. Used:
`ios/project.yml` (requirement 0006). Reference: XcodeGen (Yonas Kolb,
github.com/yonaskolb/XcodeGen); Tuist.

**Lint rules on the syntax tree.** A rule walks the parsed source instead of matching
text, so it knows whether a comment sits inside a function body. Used: `ios/LintRules`
(requirement 0006), detekt rules on Android. Reference: SwiftSyntax (Apple,
github.com/swiftlang/swift-syntax); ESLint's rule model on ESTree.

**Launch-time test configuration.** UI tests start the app with an environment variable
that selects a fixed answer instead of the network. Used: `BACKEND_STUB` in the iOS UI
tests (requirement 0006). Reference: Apple, XCTest `XCUIApplication.launchEnvironment`.

## Process

**Test-driven development.** A failing test first, then the code that makes it pass.
Used: `scripts/tdd.py`, skill `testing`. Reference: Kent Beck, *Test-Driven
Development: By Example* (2002).

**Advisory file lock (flock).** Cooperating processes take an exclusive lock on a file
before a shared action; the OS releases it when the holder exits or dies, so no stale
flag remains. Used: `scripts/run_locked.py`, the test lock taken by the Stop hook,
`tdd.py` and every test or database command. Reference: BSD `flock(2)` and POSIX
`fcntl(2)` man pages; util-linux `flock(1)`.

**Exit code 75 (EX_TEMPFAIL).** A temporary failure that may succeed if retried. Used:
`scripts/run_locked.py` when the lock stays busy past its timeout. Reference: BSD
`sysexits.h` (1980s).

**Semantic Versioning, initial development.** `MAJOR.MINOR.PATCH`; with major `0`
anything may change. Used: tags `v0.E.T`, epic in delivery order and ticket inside it
(ADR 0004 section 6). Reference: Tom Preston-Werner, Semantic Versioning 2.0.0
(semver.org).

**Staged test pipeline.** A fast stage on every change and a full stage less often.
Used: per ticket only its new tests; the full suite at each epic's closing ticket (ADR
0004 section 6). Reference: Jez Humble and David Farley, *Continuous Delivery* (2010).

**Hardening (stabilisation) iteration.** A last iteration that fixes what the full
checks find before a release. Used: the closing ticket of each epic, with regressions
fixed as bugs and review findings as refactors. Reference: Scaled Agile Framework,
Innovation and Planning iteration.

**Compose file per environment (base plus overrides).** One base Compose file with
what every environment runs, and one small file per environment with only its
differences. Used: `backend/docker-compose.yml`, `compose.override.yml` (local),
`compose.staging.yml` (server), ADR 0004 section 7. Reference: Docker documentation,
"Use multiple Compose files".

**The Twelve-Factor App (config in the environment, dev/prod parity).** Configuration
that changes between deploys lives in the environment, and the environments stay as
alike as possible. Used: host names only in each `.env`, the same images and migrations
locally and on staging (ADR 0004 section 7). Reference: Adam Wiggins, The Twelve-Factor
App (12factor.net, 2011).

**Design patterns as named, discovered solutions.** Patterns name solutions that
practitioners kept finding independently. Reference: Gamma, Helm, Johnson and
Vlissides, *Design Patterns* (1994); Christopher Alexander, *A Pattern Language*
(1977).
