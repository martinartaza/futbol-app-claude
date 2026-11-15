---
id: E08
title: Groups
status: idea
origin: Previous app (fulbito), bootstrap session 2026-11-03
adrs: ["0002"]
requirements: []
depends_on: [E05, E06, E07]
---

# E08 - Groups

## What is wanted

The weekly football group ("fulbito"): place, day, time, capacity, members with roles
(owner, admin, member) that change over time, external guests, invite links, and
ratings inside the group.

## Why

It is how the product is used every week.

## What is already decided

- Members, roles, statuses, history and one active owner (ADR 0002 sections 2 to 7).
- Group guests are reused week after week and claimed when they create an account,
  keeping the inviter's rating (ADR 0002 section 9).
- A guest is added with a name and the inviting member's perception of their skills.

## Open questions

- To be defined when the epic starts.

## Impact on the architecture

Module `groups`; the group scope of `ratings`.
