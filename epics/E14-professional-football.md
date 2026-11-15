---
id: E14
title: Professional football
status: idea
origin: Previous app (public comparisons between players), bootstrap session 2026-11-03
adrs: ["0002"]
requirements: []
depends_on: [E06]
---

# E14 - Professional football

## What is wanted

A section about famous and professional players, to be reinvented: for example a
Ballon d'Or style vote with the shortlisted players, and data of professional players.
Users rate public figures with the same radar, outside the contacts rule.

Origin, kept so it is not lost: the previous app had public comparisons ("who is
better, X or Y?") between two players, with their radars and votes. The developer wants
to rethink it rather than copy it.

## Why

Engagement around the football people follow on TV.

## What is already decided

- Public figures are not users: their ratings live in their own module and reuse the
  `ratings` calculation (ADR 0002 section 9).

## Open questions

- Everything: to be redefined when the epic starts.

## Impact on the architecture

Module `comparisons` (name to be revisited with the new definition).
