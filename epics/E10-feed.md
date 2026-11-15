---
id: E10
title: Feed
status: idea
origin: Previous app ("chimentos"), bootstrap session 2026-11-03
adrs: ["0006"]
requirements: []
depends_on: [E07, E09]
---

# E10 - Feed

## What is wanted

The "chimentos" wall: posts with image or video link, replies and reactions, and posts
generated from events ("Juan rates himself" with the radar, "Pedro thinks Juan is...",
"Juan created a group", "Juan made Pedro an admin", "players missing" from E09).

## Why

The fun and the banter keep people coming back between matches.

## What is already decided

- Generated posts are an outbox consumer (ADR 0006).

## Open questions

- To be defined when the epic starts.

## Impact on the architecture

Module `feed`.
