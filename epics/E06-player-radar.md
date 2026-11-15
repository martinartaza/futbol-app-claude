---
id: E06
title: Player radar
status: idea
origin: Previous app (the hexagon of the logo), bootstrap session 2026-11-02 and 2026-11-03
adrs: ["0002"]
requirements: []
depends_on: [E04, E05]
---

# E06 - Player radar

## What is wanted

The heart of the product: each player rates themselves on a set of skills, their
contacts rate them, and the radar chart shows it everywhere. It extends the profile
screen of E04 with the self-rating and age.

## Why

It is what distinguishes the product from any other match organiser.

## What is already decided

- Positions `outfield` and `goalkeeper`, each with its own configurable skills; a
  player may play both and has one radar per position (ADR 0002 section 9).
- Self-rating is general only: set after creating the account, editable later.
- Only contacts can rate each other (public figures are the exception, E14).
- A rater has one current rating per player, scope and position; rating again replaces
  it and the count does not grow.
- Averages are Bayesian, per player, scope and position.
- The radar almost always shows two colours: the rating being cast against a
  baseline. Baseline = the player's average in the group; if the group has no ratings
  yet, the general average; if none, the self-rating.
- The radar draws as many axes as skills arrive (skill `theming`).

## Open questions

- To be defined when the epic starts.

## Impact on the architecture

Module `ratings`; the `RadarChart` component in the three clients.
