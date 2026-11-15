---
id: E03
title: Dynamic themes
status: defining
origin: Bootstrap session, 2026-11-03
adrs: ["0004", "0008", "0009"]
requirements: []
depends_on: [E01, E02]
---

# E03 - Dynamic themes

## What is wanted

Two everyday themes in code, **white** and **dark**, that the apps pick from the
device's setting; and seasonal themes (Christmas, Halloween, New Year, end of season,
Copa América, events...) created and edited entirely from the backoffice and applied
without a store release.

"Si hacemos todo el sistema y después queremos crear la parte dinámica en todos lados,
sería demasiado grande; es lo mismo que pretender hacer todo el sistema y después
iPhone."

## Why

Seasonal themes keep the app alive, and building the theme structure from the first
screen keeps every component themable by construction.

## What is already decided

- ADR 0008: a token contract organised as a tree of components (W3C Design Tokens
  format), white and dark values in `design-tokens/base.json`, generated for CSS,
  Compose and SwiftUI.
- First ticket: the basic home screen in white and dark on Android, iOS and web, with a
  background-image decoration slot that white and dark leave empty.
- From then on, **every new component is added to the contract** with its white and
  dark values (and its decoration slots, if any) in the same ticket, and is checked in
  both themes on the three platforms (6 checks) before moving on. Screenshot tests back
  the manual checks.
- Seasonal themes are overrides edited in the backoffice: a tree of components on the
  left, the chosen element's properties on the right; decoration slots (corner badges,
  thumbnails, backgrounds) that the everyday themes leave empty.
- Contrast check (WCAG AA), preview, and activation for testers first, then for
  everyone, between dates.
- Fonts come from the set bundled in the apps.
- The backoffice does not use dynamic themes.
- Decorative images are images of purpose `theme_asset` (ADR 0009).

## Open questions

- None yet.

## Impact on the architecture

ADR 0008; `design-tokens/base.json`; the theme layer of the three clients; module
`app_config` stores seasonal themes and serves the active one; the backoffice theme
editor.
