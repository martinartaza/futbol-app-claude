---
id: E05
title: Contacts network
status: idea
origin: Previous app (network tab), bootstrap session 2026-11-03
adrs: ["0002"]
requirements: []
depends_on: [E04]
---

# E05 - Contacts network

## What is wanted

Invite another user to one's network; the other accepts or declines; contacts can be
listed and blocked. Invitations can also go out as a link shared on other networks.

## Why

Rating a player requires being their contact (E06), and groups are formed from people
one knows.

## What is already decided

- Contacts are symmetric: one row per pair with status (ADR 0002 section 3).

## Open questions

- To be defined when the epic starts.

## Impact on the architecture

Module `network`; invite links; the first events of the outbox.
