# E01-T2 - Eventos del backend: notas

Ticket: [`requirements/0002-backend-events.md`](../../requirements/0002-backend-events.md), tag
`v0.1.2`.

## Alternativas y elección

- **Para qué sirve.** No es un log (la historia vive en las tablas `*_changes` de
  cada módulo, ADR 0002) ni la comunicación con los dispositivos (E07): es la cañería
  para que un módulo reaccione a lo que pasó en otro sin llamarlo, sin perder la
  reacción. Se evaluó posponerlo hasta el primer consumidor real (YAGNI); el usuario
  eligió hacerlo ahora, en la E01.
- **Cómo el relay encuentra eventos nuevos.** Con un cursor por posición (`position`
  asignada al insertar) un evento cuya transacción hace commit tarde queda detrás del
  cursor y se pierde: el problema no es el desorden sino la pérdida. Se eligió marcar
  cada evento (`relayed_at`) y tomar los no marcados con `FOR UPDATE SKIP LOCKED`:
  ningún proceso espera a otro (sin abrazo mortal ni "los dos gordos en la puerta") y
  los huecos de numeración no importan.
- **Orden.** Se evaluó FIFO por `aggregate_key` (un evento que falla bloquea a los
  siguientes del mismo grupo hasta quedar `dead`) contra no garantizar orden. El
  usuario eligió **sin garantía de orden**: los consumidores previstos (inbox, feed,
  señales en vivo) no dependen del orden; el que lo necesite compara la versión del
  agregado. Quedó escrito en ADR 0006 §3, §4 y §9, en el skill `backend-architecture`
  y en el agente `architecture-reviewer`.

## Instalación y configuración

- Variables nuevas (con default, no hace falta tocar `.env`): `EVENTS_MAX_ATTEMPTS=8`,
  `EVENTS_POLL_SECONDS=5`, `EVENTS_BACKOFF_MAX_SECONDS=3600`.
- Servicio `worker` en `docker-compose.yml`: misma imagen que `backend`, comando
  `python -m app.events.worker`, sin recarga automática (`docker compose restart
  worker` después de un cambio).
- Migración autogenerada: `docker compose exec backend alembic revision --autogenerate
  -m "events_outbox_and_deliveries"`, después `upgrade head` y `check` bajo
  `run_locked.py`.
- Base de tests del backend, primera vez: `tests/conftest.py` lee `TEST_DATABASE_URL`
  de `backend/.env`, aplica las migraciones una vez por sesión contra `db-test` y vacía
  las tablas antes de cada test. `pythonpath = [".", "tests"]` en `pyproject.toml` para
  importar `app` y `fakes` sin instalar el proyecto.

## Problemas y soluciones

- **`app` no se importaba en los tests**: el proyecto no se instala en el `.venv`. En
  rojo se resolvió con una línea de `sys.path` en `conftest.py`; en verde se pasó a
  `pythonpath` en `pyproject.toml`, con permiso del usuario para tocar el test aprobado.
- **Deprecaciones de SQLAlchemy 2.1**: `Result.tuples()` y `Row.tuple()` ya no hacen
  falta (la fila se desarma como tupla); corregido también en `app_config`. `dict()`
  directo sobre un `Result` sigue sin servir (tiene `keys()`): `dict(result.all())`.
- **mypy y `LISTEN`**: `driver_connection` puede ser `None` según el tipo; se valida y
  se corta con un error claro.

## Otras notas

- Cómo se despierta el worker: `publish` hace `pg_notify` en la misma transacción
  (llega solo si hay commit); el adaptador escucha en una conexión propia y además
  consulta cada `EVENTS_POLL_SECONDS` por si se perdió una notificación. Verificado a
  mano: un evento publicado desde el contenedor de la API quedó relayed en menos de un
  segundo.
- El reloj se pasa como argumento (`relay(now)`, `deliver_due(now)`): los tests de
  reintentos mueven la hora en lugar de esperar.
- La sección del backoffice para eventos y dead letters llega con la E02 (ADR 0007
  §6).
- El usuario corrió los tests del ticket (10 pasan) y revisó los logs del `worker`, y
  dio el ticket por terminado el 2026-11-15.
