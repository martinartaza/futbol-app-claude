# E01-T9 - Segundo cierre de la E01: notas

Ticket: [`requirements/0009-close-e01-staging.md`](../../requirements/0009-close-e01-staging.md),
tag `v0.1.9`.

## Alternativas y elección

- **Por qué un segundo cierre.** La E01 se había cerrado con el 0007 (`v0.1.7`). Con
  ngrok caído, el usuario pidió sumar a la épica el backend en staging (0008). En lugar
  de deshacer el 0007, se etiquetó tal cual y se agregó este cierre corto: suite
  completa y `architecture-reviewer` solo sobre `v0.1.7..v0.1.8`.

## Qué se corrió

- **Suite completa** de backend (42), workspace (74), web (Vitest y 14 de Playwright),
  android e ios: todo en verde, sin regresiones.
- **`architecture-reviewer`** sobre el 0008: seis hallazgos, todos de documentos salvo
  uno del script de deploy. El usuario aprobó corregirlos todos.

## Qué se corrigió

- El dominio de staging no se escribe en los documentos: se nombra por su variable
  (`BACKEND_HOST`), como pide CLAUDE.md.
- La fila "Releases" de `docs/production-readiness.md` incluye el deploy del backend
  desde CI; mientras tanto, `tools/deploy.sh` a mano.
- La sección 7 del ADR 0004 pasó a describir los entornos local y staging (compose por
  entorno, migrate al levantar, script de deploy), con sus referencias en el ADR y en
  `docs/prior-art.md`.
- `bug-reproduction.md` dice que solo el backend recarga solo.
- `deploy.sh` limpia comillas, espacios y `\r` de `BACKEND_HOST`, igual que Compose, para
  que el chequeo de health no pregunte por un nombre equivocado.
- Los párrafos de ngrok que quedaban en el 0005 y el 0006 dicen que el 0008 los
  reemplazó.
