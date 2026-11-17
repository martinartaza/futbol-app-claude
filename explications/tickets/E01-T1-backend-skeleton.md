# E01-T1 - Esqueleto del backend: notas

Ticket: [`requirements/0001-backend-skeleton.md`](../../requirements/0001-backend-skeleton.md), tag
`v0.1.1`.

## Alternativas y elección

- **Con o sin tests en este ticket.** El ciclo TDD necesita un proyecto, un entorno
  virtual, pytest y una base de test; antes de este ticket no existía nada de eso. Se
  barajó un "paso 0" de andamiaje sin lógica y después el ticket con tests en rojo; el
  usuario eligió hacer todo el esqueleto como andamiaje, sin tests, y arrancar el
  proceso completo desde el ticket siguiente. Cada criterio se verificó a mano.
- **Certificado local.** Regenerar el certificado compartido de Traefik (que usan otros
  proyectos) o agregar un par propio. Se eligió un par propio cargado por un archivo
  propio en `dynamic/`, así nada compartido cambia. Con labels de Docker no se puede:
  Traefik solo carga certificados desde el proveedor de archivos; las labels declaran
  el router (host, entrypoint, `tls=true`).
- **Dónde corta el version gate.** Una extensión de Strawberry en `on_execute` dejaba
  pasar la ejecución en esta versión de Strawberry; se movió a `on_operation`, que
  además corre antes de validar: una app vieja cuya query ya no valida recibe
  `UPGRADE_REQUIRED` y no un error de validación.

## Instalación y configuración

- Proyecto con `uv init --bare --python 3.13`, dependencias con `uv add` (fastapi,
  uvicorn, strawberry-graphql, sqlalchemy[asyncio], asyncpg, alembic,
  pydantic-settings) y de desarrollo con `uv add --dev` (pytest, pytest-asyncio, httpx,
  ruff, mypy, import-linter, `strawberry-graphql[cli]` para `export-schema`).
- Imagen: `python:3.13-slim` con `uv` 0.12.7 copiado de su imagen oficial; el entorno
  virtual vive en `/opt/venv` dentro del contenedor, así el código montado en `/app` no
  pisa el `.venv` de la Mac.
- `docker compose` con proyecto `fulbito`: `backend` (uvicorn con `--reload` sobre
  `app/`), `db` (PostgreSQL 17 con volumen) y `db-test` (PostgreSQL 17 en `tmpfs`,
  publicado en `127.0.0.1:TEST_DB_PORT` para pytest desde la Mac).
- `.env` creado desde `.env.example` con una contraseña aleatoria (`openssl rand`),
  nunca impresa. `DATABASE_URL` lo arma el compose con `POSTGRES_*`.
- Traefik compartido (`~/trabajo/traefik`): `mkcert -cert-file certs/fulbito.pem
  -key-file certs/fulbito-key.pem <host web> <host backend>` (los dos hosts locales de
  `/etc/hosts`) y el archivo
  `dynamic/fulbito.yml` que lo carga. Sin reinicio: el proveedor de archivos vigila la
  carpeta.
- Primera migración: `docker compose exec backend alembic revision --autogenerate -m
  "app_settings"`, después `upgrade head` y `check` bajo `run_locked.py`.

## Problemas y soluciones

- **import-linter marcaba todo como roto**: los contratos `forbidden` miran también las
  importaciones indirectas (router → dependencies → repository → sqlalchemy). Se
  activó `allow_indirect_imports`: la regla es sobre lo que cada archivo importa
  directamente, y el cableado pasa por `dependencies`. Además `dependencies.py`
  importaba `AsyncSession`; se agregó `RequestSession` en `app/db/session.py`.
- **mypy**: `AddValidationRules` como instancia está deprecado en esta versión de
  Strawberry; se pasa una fábrica. El decorador `@strawberry.field` sobre un método
  quedaba sin tipos; se usa `strawberry.field(resolver=...)`.
- **`dict(result.tuples())` fallaba** (`ChunkedIteratorResult` no es subscriptable):
  `dict()` lo trata como mapping porque tiene `keys()`. Se usa `.tuples().all()`.
- **El gate parecía no bloquear** después de un cambio: Traefik mantenía conexiones
  keep-alive con el proceso anterior al `--reload`. Pasa solo en desarrollo.

## Otras notas

- Verificación a mano: AC-1, AC-2, AC-4, AC-9 contra el stack levantado por HTTPS
  (`https://$BACKEND_HOST`); AC-3, AC-5, AC-6 con la aplicación en proceso (httpx
  `ASGITransport`) y `APP_ENV=staging`; AC-7 con `breaking_changes` sobre un schema con
  un campo de más; AC-8 con una copia del código donde `health.service` importa el
  repositorio de `app_config`.
- El usuario probó a mano `/graphql` (GraphiQL) y `/health` por HTTPS y dio el ticket
  por terminado el 2026-11-15. AC-10 se verificó con el primer push: `checks.yml` en
  verde en GitHub Actions (para `main` y para el tag `v0.1.1`). Los cuatro repos de
  código tienen su remoto en GitHub y el tag `v0.1.1`.
- A raíz de este ticket (unos 41 permisos, uno por archivo, por trabajar sin tarea
  abierta) se agregó `tdd.py start <tarea> --direct`: un solo permiso para todo un
  cambio directo, con fuente y tests libres hasta `done`.
- Strawberry imprime en el log los errores esperados (`UPGRADE_REQUIRED`, ...). Se
  puede filtrar más adelante.
