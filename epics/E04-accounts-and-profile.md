---
id: E04
title: Accounts, social login and profile
status: defining
origin: Bootstrap session, 2026-11-03
adrs: ["0002", "0005", "0009"]
requirements: []
depends_on: [E01, E02, E03]
---

# E04 - Accounts, social login and profile

## What is wanted

Sign in with a social account and see one's own profile with the data the provider
returns (name and photo). The profile screen is the one the radar epic (E06) extends
with the self-rating and age.

## Why

Everything else in the product belongs to a user; the previous version broke on its
login, so this one is built first and right.

## What is already decided

- Providers, sessions, linking and the development login: ADR 0005. The enabled
  providers and their public client ids are configured from the backoffice (E02);
  provider secrets stay in the environment.
- Every screen in both themes of E03.
- One user, many identities: ADR 0002 section 1 and ADR 0005 section 2.
- Name and photo come from the provider at first sign-in.
- Sessions per device; sign out; account deletion required by the stores (ADR 0002
  section 11).
- Photos follow ADR 0009: the provider's picture is copied into storage at sign-up,
  uploads go through a signed URL, clients show variants by size.
- Delivered on Android, iOS (Simulator, without Sign in with Apple until the paid
  account) and web.

## Open questions

- Can the user edit their name and photo, or only see them, in this epic?
- What the account deletion screen asks and confirms.

## Impact on the architecture

Module `accounts` (users, identities, sessions, the `IdentityProvider` port and its
adapters); module `images` (ADR 0009); the profile and sign-in screens in the three clients.
