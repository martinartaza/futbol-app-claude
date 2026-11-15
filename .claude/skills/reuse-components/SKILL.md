---
name: reuse-components
description: Reuse before creating a UI component in android/, ios/ or web/. Load BEFORE creating a new component, view or composable. Search the ui catalog first, extend an existing component with a parameter instead of copying it, keep the same component names across the three clients.
---

# Reuse components

## Before creating a component

1. Look in the client's `ui` layer and in the feature's own components (the catalog is
   listed in `docs/agent/codebase-map.md`).
2. If one does almost what is needed, **extend it with a parameter**; never copy it
   under a new name.
3. Create a new one only when no existing component fits; generic ones go to `ui`,
   feature-specific ones to the feature.

The edit guard enforces step 1: the first creation of a file under the `reuse_guard`
globs of `workflow.json` is denied with the list of similar files; the second attempt
passes. Read the list, then decide.

## Rules

- Generic components take data, not GraphQL types or feature models.
- **Same name in the three clients** for the same component (`RadarChart`,
  `PlayerCard`, `ComingSoon`), so a requirement names one component and each client
  implements it.
- Only tokens inside (skill `theming`).
- Every new generic component is added to the catalog in `docs/agent/codebase-map.md`.

## Guarded folders (added to `workflow.json` with each skeleton)

| Client | `reuse_guard` globs |
|---|---|
| android | `app/src/main/java/**/ui/**/*.kt`, `app/src/main/java/**/features/**/components/**/*.kt` |
| ios | `Packages/UI/**/*.swift`, `Packages/Features*/**/Components/**/*.swift` |
| web | `src/ui/**/*.tsx`, `src/features/**/components/**/*.tsx`, `src/backoffice/ui/**/*.tsx` |
