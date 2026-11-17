---
name: theming
description: Design tokens and themes for the three clients (android/, ios/, web/). Load BEFORE writing any UI code, choosing a colour, font, size, radius, spacing or shadow, adding a component, or drawing the radar. Only tokens through the theme layer, never literal values; one token tree in design-tokens/base.json with white and dark values, seasonal themes applied at run time.
---

# Theming with design tokens

Decisions: `docs/adr/0008-dynamic-themes.md` (themes), which refines
`docs/adr/0004-native-clients-and-repositories.md` section 5 (generation).

## The rule

**A component never contains a literal colour, font, size, radius, spacing or shadow,
and never reads a generated constant directly.** It reads a token through the client's
theme layer, which resolves: active seasonal override → bundled white or dark value.

## The contract: one tree in `design-tokens/base.json`

- W3C Design Tokens Community Group format. Each token has a type (colour, dimension,
  font weight, font family, asset) and a value for **white** and for **dark**.
- Three tiers: primitives (palette, scales) → semantic roles (`surface`, `on-surface`,
  `team.red`, `team.on-red`, `radar.grid`) → component tokens grouped by component
  (`home.title.color`, `tab.label.color`, `avatar.radius`), which reference roles.
- `scripts/sync_contracts.py` generates in each client the typed accessors (a missing
  token does not compile) and the bundled white and dark values: Compose theme
  (android), SwiftUI theme (ios), CSS custom properties (web). Generated files are
  `"edit": "deny"`: change the JSON and regenerate. It also publishes the contract the
  backoffice editor shows.

## White and dark

The two themes in code. The app follows the device's light or dark setting. Every token
has both values; `sync_contracts.py` fails otherwise.

## Pairs

Every background token has its foreground pair. A component that sets a background sets
the matching foreground. Pairs are checked for WCAG AA contrast.

## Adding or changing a component

1. Add its group to `base.json` with every token it uses, in white and dark.
2. Decide its **decoration slots** (`avatar.corner-badge`, `home.background-image`):
   asset tokens, empty in white and dark. Draw a slot only when it has a value.
3. Regenerate (`sync_contracts.py`), use the tokens through the theme layer.
4. Screenshot tests in white and dark: Roborazzi (android), swift-snapshot-testing
   (ios), Playwright screenshots (web).
5. Done = works on Android, iOS and web, in white and dark (six checks).

The component appears in the backoffice theme editor by itself; the editor is never
changed per component.

## Seasonal themes (run time)

- Overrides stored in `app_config`, edited in the backoffice, read with the
  `activeTheme` query (id, version, overrides).
- The theme layer starts from the cached theme (or none) over the bundled white or
  dark, applies the server's theme when it arrives, re-reads it on foreground and on the
  live signal (ADR 0006).
- **Unknown tokens are ignored; a missing override keeps the bundled value.** Never
  fail on a theme.
- Assets come through ADR 0009. Fonts: only families bundled in the apps, never
  downloaded.

## The backoffice

The backoffice (ADR 0007) uses its own fixed token set in `design-tokens/` and never
reads `activeTheme`.

## The radar

The radar chart lives in each client's `ui` layer and takes only data (axis labels, one
or two series of values, which team colour each series uses). Its colours, strokes and
grid come from the `team` and `radar` roles; the number of axes comes from the data,
never from the code.

## Enforcement

A lint rule per client fails on literals outside the generated theme, written with each
skeleton: a detekt rule (android), the `ios/LintRules` rule `no-literal-design-values` (ios), ESLint and Stylelint
rules (web). `sync_contracts.py` checks the contract; backend tests reject seasonal
themes with unknown tokens, wrong types or failing contrast; the
`architecture-reviewer` checks item 22.
