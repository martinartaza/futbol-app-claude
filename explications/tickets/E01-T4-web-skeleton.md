# E01-T4 - Esqueleto web: notas

Ticket: [`requirements/0004-web-skeleton.md`](../../requirements/0004-web-skeleton.md), tag
`v0.1.4`.

## Alternativas y elección

- **Andamiaje antes del TDD.** Sin un proyecto Next.js con Vitest y Playwright instalados
  los tests en rojo no se pueden ni ejecutar. Se acordó con el usuario hacer primero el
  andamiaje como cambio directo (`tdd.py start web-scaffold --direct`, un solo permiso),
  sin pantallas ni lógica, y después el 0004 con TDD.
- **Versión de Node.** El Mac tiene Node 22; se usó esa y se fijó en `.nvmrc`,
  `engines` del `package.json` y la imagen `node:22-slim`.
- **Dos corredores de tests, un comando.** El workflow tiene un solo `test_command`
  por proyecto; `tools/run-tests.mjs` manda cada archivo a su corredor (`*.test.ts(x)`
  a Vitest, `*.spec.ts` a Playwright) y sale con 5 cuando no hay tests, como pytest.

## Instalación y configuración

- Proyecto creado con `pnpm dlx create-next-app@latest` (Next.js 16.4, React 19.3,
  TypeScript estricto, App Router, `src/`, ESLint, sin Tailwind) en el scratchpad y
  copiado a `web/` sin la página de ejemplo, los SVG ni el favicon.
- Dependencias: `@apollo/client` 4 y `graphql` 17; de desarrollo graphql-codegen
  (`client-preset`, más `@graphql-typed-document-node/core`, que el código generado
  importa), Vitest 5 con jsdom y Testing Library, Playwright, `eslint-plugin-boundaries`
  y Prettier (formato al editar, como ruff en el backend).
- Scripts: `lint`, `typecheck` (`next typegen` antes de `tsc`, porque `LayoutProps` sale
  de los tipos de rutas que genera Next), `codegen`, `format`, `test`, `test:unit`,
  `test:e2e`.
- Local: `docker compose up -d` en `web/` (proyecto `fulbito-web`). Variables en `.env`:
  `WEB_HOST`, `BACKEND_HOST`, `BACKEND_URL`, `BUILD_NUMBER`, `MKCERT_CA_DIR`
  (`mkcert -CAROOT`). El contenedor resuelve el host del backend a la Mac con
  `extra_hosts: host-gateway` y confía en el certificado local con
  `NODE_EXTRA_CA_CERTS`.
- `workflow.json`: entrada `web` con fuente, tests, comandos, checks (ESLint, TypeScript,
  Prettier), formato al editar y archivos generados con `"edit": "deny"` (tokens y
  schema, tipos de codegen, `pnpm-lock.yaml`).

## Esqueleto (TDD)

- Tests: `tests/web-skeleton.test.tsx` (Vitest, 14) y `e2e/web-skeleton.spec.ts`
  (Playwright, 7 por tema, 14 en total).
- Estructura: grupo de rutas `src/app/(shell)/` con la navegación y el chequeo de
  conexión; `/sign-in` y `/update` fuera del grupo. Componentes genéricos en `src/ui`;
  features `health` y `app_config`; cliente Apollo y link de actualización en
  `src/core/apollo`.
- Fuente Inter incluida en `public/fonts/` (variable, latin y latin-ext, con licencia),
  tomada de `@fontsource-variable/inter`, sin descargarla en tiempo de ejecución.
- Capturas de referencia por plataforma: `*-darwin.png` (Mac) y `*-linux.png`, generadas
  con la imagen `mcr.microsoft.com/playwright:v1.65.1-noble`, la misma en la que corre
  `tests.yml`.

## Problemas y soluciones

- **`tsc` no encontraba `LayoutProps`**: es un tipo global que Next genera en `.next/`;
  se resolvió con `next typegen` antes de `tsc` en el script `typecheck`.
- **Los tipos generados no compilaban**: faltaba `@graphql-typed-document-node/core`.
- **Vitest sin tests sale con 1**, igual que una falla; por eso el wrapper sale con 5
  cuando no encuentra archivos.
- **Testing Library no limpiaba entre tests**: el limpiado automático necesita
  `globals: true` en Vitest.
- **Dos "Próximamente" al navegar**: con Cache Components, Next deja la ruta anterior
  montada y oculta. El usuario aprobó cambiar en el test de navegación `getByText` por
  `getByRole("paragraph")`, que ignora lo oculto (lo recomienda la guía de Next).
- **La página no hidrataba detrás de Traefik**: el servidor de desarrollo bloquea los
  recursos `/_next/*` pedidos desde otro host; `allowedDevOrigins` lee `WEB_HOST`.
- **Aviso de navegación instantánea** en cada sección: el contenido espera el chequeo de
  conexión en el cliente; las páginas del shell exportan `instant = false`.
- **El comentario de doc de una función anidada** (dentro de un `describe`) chocaba con
  la regla de comentarios; la regla acepta un bloque `/** */` justo encima de una
  función.
- **La corrida en Docker dejó un store de pnpm en `web/`**: se borró y se ignora
  (`.pnpm-store`).

## Otras notas

- `AGENTS.md` lo escribe Next (`next dev` lo vuelve a crear si se borra); se deja en el
  repo.
- Verificado a mano: `https://<WEB_HOST>/` responde 200 con `lang="es"`, y desde el
  contenedor la query `health` al backend responde `ok` por HTTPS.
- El usuario probó el web en local (secciones, temas y error de conexión) y dio el ticket por terminado el 2026-11-15. Un error en el panel de Next venía de la extensión Vue Devtools duplicada, no de la app.
