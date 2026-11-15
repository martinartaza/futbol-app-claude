---
name: new-adr
description: Write the next architecture decision record in docs/adr/ (NNNN-slug.md, English, status proposed) after discussing a cross-cutting decision with the user. Use when the user asks for an ADR, or when a requirement needs a decision about how the system is built that applies beyond one feature (a library, a layer, a protocol, where something lives). Does NOT implement anything.
argument-hint: "[short topic, e.g. mobile stack]"
---

# New ADR

Decision: `$ARGUMENTS` (if empty, what was just discussed).

Current ADRs:

!`ls -1 docs/adr/ 2>/dev/null | grep -E '^[0-9]{4}-' || echo "(none yet)"`

## Requirement or ADR?

| Question | Goes to |
|---|---|
| "A player can follow a team" | `requirements/` (what the system does) |
| "Every external provider sits behind a port" | `docs/adr/` (how it is built, across features) |

A cross-cutting decision is never written inside a requirement.

## Steps

1. **Read the related epics** (`epics/`) and the accepted ADRs it touches.
   An ADR that changes an accepted one **supersedes** it (new file, `supersedes: NNNN`);
   the old one only gets `superseded_by` and keeps its text.
2. **Agree before writing.** The decision, the options considered and what each one
   costs. If the user has not chosen, present the options with a recommendation and ask;
   do not write a decision the user did not make.
3. **Number and name.** Next `NNNN`, English kebab-case slug. Copy
   `docs/adr/_template.md`, `status: proposed`, today's date.
4. **Write it in English**: *Context* (facts, constraints), *Decision* (numbered
   sections, each one checkable), *Consequences* (good and bad), *Alternatives
   considered* (by kind, with the reason they lost). Mermaid for diagrams.
5. **Say how it is enforced**: an import contract, a lint rule, a hook, a test, or the
   architecture review checklist. A rule nobody checks erodes.
6. Add the row to the index of `docs/adr/README.md`.
7. **Reply in Spanish** with a summary and ask for approval. On approval: `status:
   accepted`, the date, and update `CLAUDE.md` "Architecture decisions so far" with one
   line, and the skills that apply it.

## Style

- Title and decisions say only the chosen design. Discarded options appear in
  *Alternatives considered*, described by kind, not as "no X for now".
- Every decision says the *why* in one sentence; the reader is a future Claude session
  that must apply it without this conversation.
