# Bootstrap: the first session of this workspace

You are the first Claude session of a new workspace installed from the workflow kit
(`~/trabajo/workflow-kit`). Your job is to lay the foundations with the developer:
nothing is coded until the foundations are agreed. Answer in Spanish (Rioplatense).
Documents in English, explications in Spanish.

## 0. Read first

1. `~/trabajo/workflow-kit/PORTING.md`: what the kit is, every rule and its *why*.
2. This workspace's `CLAUDE.md`, `workflow.json`, `docs/adr/README.md`,
   `docs/adr/0001-backend-modular-monolith.md`, and the skills list in `.claude/skills/`.
3. Your memory (seeded by the kit): user profile and the project's origin.

Check the tooling works: `python3 --version` (3.13+ needed), then
`uvx --python 3.13 pytest -q tests` from the root. Report the result in one line.

## 1. Interview, one theme per turn

Ask, propose, wait. Never two decisions in one question. Write each agreed decision
down (ADR, epic or CLAUDE.md) before moving on.

1. **The product**: name, one paragraph, who uses it, platforms (Android, iOS, web),
   stage. Fill the top of `CLAUDE.md`.
2. **The old app** (path given by the developer): read only enough to list its features
   (screens, routes, models by name): a table with *keep / drop / later* for the
   developer to decide. The 2026 World Cup "prode" is dropped. **Never copy code.** Find
   the store identity values (`applicationId`, last `versionCode`, iOS bundle id) and
   write them in `CLAUDE.md` "Store identity". The developer copies the keystore and
   passwords into `secrets/` by hand; Claude never reads them.
3. **ADR 0001 backend**: review the draft with the developer, adjust the module list,
   accept it.
4. **ADR 0002 client stack** (skill `new-adr`): native Android, native iOS and web, full
   access to the platform. Present the options by kind with a recommendation:
   one TypeScript codebase that renders native components with native modules when
   needed (React Native with Expo), shared Kotlin logic with native UIs (Kotlin
   Multiplatform), or fully separate native apps. Criteria: 100 % of the platform, one
   developer, web too, the developer's languages, over-the-air updates, test tooling.
   The developer decides. Then: the `app` entry of `workflow.json` (from
   `~/trabajo/workflow-kit/extras/workflow.app-examples.json`; editing it asks), the
   skills `app-architecture`, `theming` and `reuse-components` (PORTING §4), the comment
   rule for the app language, the reviewer's stack items, CLAUDE.md lines.
5. **Repository layout** (ADR or a CLAUDE.md line): one monorepo, or one repository per
   project with the workspace root holding the documents (the iTuc layout). Tags
   `v0.N.P` follow it.
6. **ADR 0003 accounts and login**: SMS first behind a port (provider, a test number
   and key for local), sessions for mobile (tokens in secure storage), social login
   later through the same module.
7. **Epics** from the kept features (`epics/`, one file each, index and
   dependency diagram), in delivery order.
8. **First requirements** (skill `new-requirement`, status pending): typically the
   skeleton (backend health, app shell with every screen "Próximamente", a store build
   with the kept identity) and the SMS login. Do not implement them in this session
   unless the developer says so.
9. Fill `docs/agent/codebase-map.md` sections as the skeleton appears, and
   `docs/production-readiness.md` with what applies.

## 2. Talking to the iTuc session

The developer may keep the iTuc session open (renamed `ituc-workflow`; before renaming it
was `chatbot-ituc-a6`) to answer questions about *why* the workflow is the way it is. Use
it for questions the kit does not answer:

- find it with `ListAgents` (the row of the `chatbot-ituc` folder), write with
  `SendMessage` to the name it shows;
- make every message self-contained (that session does not see this workspace);
- ask about the iTuc experience ("why does the review run only once?", "how did you
  reproduce bugs in the browser without leaking tokens?"), never ask it to edit files
  here;
- if no answer arrives, go on with the kit's documents and tell the developer.

## 3. When the foundations are done

- Tell the developer, in Spanish, what was decided (ADRs, epics, requirements) and what
  the next step is (implement requirement 0001).
- Ask whether to delete this `BOOTSTRAP.md` (it is a one-time script).
- Save to memory only what the repository does not already record.
