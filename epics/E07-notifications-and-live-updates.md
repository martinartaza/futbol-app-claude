---
id: E07
title: Notifications and live updates
status: idea
origin: Previous app (invitations with notifications), bootstrap session 2026-11-03
adrs: ["0006"]
requirements: []
depends_on: [E05]
---

# E07 - Notifications and live updates

## What is wanted

A notification inbox per user, push notifications when the app is closed, and screens
that update by themselves when something changes.

## Why

Invitations, sign-ups and votes are social: people answer each other in real time.

## What is already decided

- Everything in ADR 0006: outbox consumers, inbox as source of truth, GraphQL
  subscriptions over WebSocket, push through FCM.

## Open questions

- To be defined when the epic starts (which events notify, preferences per type).

## Impact on the architecture

Module `notifications`; the worker's consumers; the `PushSender` and `LiveChannel`
adapters; Firebase projects.
