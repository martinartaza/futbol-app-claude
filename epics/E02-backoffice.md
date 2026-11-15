---
id: E02
title: Backoffice and app configuration
status: defining
origin: Bootstrap session, 2026-11-03 (the Django admin of the previous app was how the developer tested the whole system)
adrs: ["0002", "0006"]
requirements: []
depends_on: [E01]
---

# E02 - Backoffice and app configuration

## What is wanted

A backoffice in the web client to see and operate the whole system: watch connections,
invitations and votes, act on them, configure the app, and follow how events move.
"En Django cada interacción que hacía en la red la podía ver en el admin, manejarla,
simular comportamiento… fue la manera de probar todo el sistema."

## Why

It is the developer's main tool to test and operate a social system with many crossed
states.

## What is already decided

- Access as in iTuc: a secret path, a user and a password read from the backend's
  `.env`; a full-access operator separate from user accounts, available before social
  login exists.
- Hardening: rate limit and temporary lockout on the backoffice sign-in, `HttpOnly`
  short-lived session cookie over HTTPS, the internal web route answers 404 when asked
  directly.
- Every backoffice action goes through the owning module's service: history, outbox
  events, notifications and live updates happen exactly as for a user action. History
  rows record the actor `backoffice` (no `changed_by_id`).
- A settings store for values the backoffice can change (non-secret ones; secrets stay
  in the environment).
- Minimum app version per platform (ADR 0003 section 5).
- A view of outbox events, consumer positions and dead letters (ADR 0006).
- Its own design rules: a fixed theme (never the dynamic themes of E03) and its own
  component catalog under the reuse guard.
- **Every later epic adds its backoffice section**, so the backoffice always covers the
  newest feature.

## Open questions

- The backoffice ADR (0007): API surface for admin operations, the web routing of the
  secret path, the settings store shape.

## Impact on the architecture

ADR 0007; module `app_config` (settings, minimum version); admin operations in each
module; the `/admin` section of `web/`.
