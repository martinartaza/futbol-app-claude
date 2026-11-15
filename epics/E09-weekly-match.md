---
id: E09
title: Weekly match
status: idea
origin: Previous app (next match, teams, result), bootstrap session 2026-11-03
adrs: ["0002"]
requirements: []
depends_on: [E08]
---

# E09 - Weekly match

## What is wanted

Each week's match of a group: sign-up opening at a set day and time, order of arrival
and capacity, the position played that day, guests, red and blue teams compared by
their radars, the result, and sharing "players missing" on other networks.

## Why

Signing up and picking teams is the weekly ritual the product supports.

## What is already decided

- Teams are compared outfield against outfield and goalkeeper against goalkeeper (ADR
  0002 section 9).
- Sharing "players missing" to the feed waits for E10; the rest of this epic does not.

## Open questions

- To be defined when the epic starts.

## Impact on the architecture

Module `matches`; public share pages on web (ADR 0004 section 3).
